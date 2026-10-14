"""Lazy-loading model registry with an LRU cap so 7+ models never sit in VRAM at once."""
import os, random, threading
from collections import OrderedDict


class MockDetector:
    """Same interface as the real detector. Used when the .pth is missing or USE_MOCK=1."""
    def __init__(self, mcfg, defect_rate=0.2):
        self.m, self.rate = mcfg, defect_rate

    def _box(self):
        x, y = random.randint(100, 900), random.randint(80, 700)
        return [x, y, x + random.randint(80, 240), y + random.randint(60, 180)]

    def predict(self, frame=None):
        out = []
        for ck in self.m["checks"]:
            flip, r = random.random() < self.rate, ck["rule"]
            def add(c): out.append({"box": self._box(), "score": round(random.uniform(.9, .99), 2), "class_name": c})
            if r == "required":
                if not flip:
                    for _ in range(ck.get("min_count", 1)): add(ck["class"])
            elif r == "forbidden":
                if flip: add(ck["class"])
            elif r == "pair":
                add(ck["bad"][0] if flip else ck["good"][0])
            elif r == "count":
                for _ in range(ck["count"] - (1 if flip else 0)): add(ck["class"])
        return out


class RFDETRDetector:
    def __init__(self, mcfg, path, variant, resolution, threshold):
        from rfdetr import RFDETRSmall, RFDETRLarge
        self.m = mcfg
        kw = {"pretrain_weights": path}
        if resolution:
            kw["resolution"] = resolution
        self.model = (RFDETRLarge if variant == "large" else RFDETRSmall)(**kw)
        self.threshold = threshold
        self.lock = threading.Lock()

    def _names(self):
        cn = getattr(self.model, "class_names", None)
        if isinstance(cn, dict):
            names = {int(k): v for k, v in cn.items()}
        elif cn:
            names = dict(enumerate(cn))
        else:
            names = {}
        # Support models where background is 0 and class is at index 1
        if 1 not in names and 0 in names:
            names[1] = names[0]
        return names

    def predict(self, frame_bgr):
        import cv2
        from PIL import Image
        with self.lock:   # RF-DETR is not thread-safe
            det = self.model.predict(Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)), threshold=self.threshold)
        names, out = self._names(), []
        for i in range(len(det.xyxy)):
            cid = int(det.class_id[i])
            cname = names.get(cid, str(cid))
            # Fallback if unmapped empty string or index mismatch
            if not cname or cname == str(cid):
                for ck in self.m.get("checks", []):
                    if ck.get("class"):
                        cname = ck["class"]
                        break
            out.append({"box": [int(v) for v in det.xyxy[i]], "score": float(det.confidence[i]), "class_name": cname})
        return out


class ModelRegistry:
    def __init__(self, cfg, base_dir=".", max_loaded=2):
        self.cfg, self.base, self.max = cfg, base_dir, max_loaded
        self.cache, self.lock = OrderedDict(), threading.Lock()
        self.force_mock = os.getenv("USE_MOCK", "0") == "1"

    def _load(self, key):
        m = self.cfg[key]
        path = os.path.join(self.base, m["path"])
        if self.force_mock or not os.path.exists(path):
            print(f"[registry] {key}: using MOCK detector ({path} not used)")
            return MockDetector(m)
        print(f"[registry] loading {key}")
        return RFDETRDetector(m, path, m.get("variant", "small"), m.get("resolution"), m["threshold"])

    def get(self, key):
        if key not in self.cfg:
            raise KeyError(key)
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            while len(self.cache) >= self.max:
                old, det = self.cache.popitem(last=False)
                print(f"[registry] evicting {old}")
                del det
                try:
                    import torch, gc
                    gc.collect(); torch.cuda.empty_cache()
                except Exception:
                    pass
            self.cache[key] = self._load(key)
            return self.cache[key]

    def detect(self, key, frame=None):
        return self.get(key).predict(frame)
