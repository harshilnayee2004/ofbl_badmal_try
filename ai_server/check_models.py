"""Run all 7 models on ONE photo and write check_models_report.txt (class names + raw detections, no rules applied).
Usage (from the ai_server folder):   python check_models.py "C:\\path\\to\\photo.jpg"
Optional: python check_models.py photo.jpg primer_assembly     (only one model)"""
import os, sys, time, traceback, warnings
warnings.filterwarnings("ignore")
import yaml, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
    sys.exit('Usage: python check_models.py "path\\to\\photo.jpg" [model_key]')
img_path, only = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
cfg = yaml.safe_load(open(os.path.join(HERE, "inspection", "models_config.yaml"), encoding="utf-8"))["models"]
frame = cv2.imread(img_path)
if frame is None:
    sys.exit("Could not read that image.")
pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
out = [f"Photo: {img_path}  size={frame.shape[1]}x{frame.shape[0]}\n"]

from rfdetr import RFDETRSmall, RFDETRLarge
for key, m in cfg.items():
    if only and key != only:
        continue
    path = os.path.join(HERE, m["path"])
    out.append(f"=== {key}  ({m['path']})")
    out.append(f"    config: threshold={m['threshold']} variant={m.get('variant')} resolution={m.get('resolution')}")
    out.append(f"    config expects classes: {sorted({c for ck in m['checks'] for c in ([ck['class']] if 'class' in ck else ck['good'] + ck['bad'])})}")
    if not os.path.exists(path):
        out.append("    !! model file not found\n"); continue
    try:
        kw = {"pretrain_weights": path}
        if m.get("resolution"):
            kw["resolution"] = m["resolution"]
        t0 = time.time()
        model = (RFDETRLarge if m.get("variant") == "large" else RFDETRSmall)(**kw)
        names = getattr(model, "class_names", None)
        out.append(f"    model class_names: {names}")
        det = model.predict(pil, threshold=0.25)             # low threshold on purpose: show what the model sees
        nm = {int(k): v for k, v in names.items()} if isinstance(names, dict) else dict(enumerate(names or []))
        out.append(f"    {len(det.xyxy)} detections at conf>=0.25  ({time.time()-t0:.1f}s incl. load)")
        for i in range(len(det.xyxy)):
            cid = int(det.class_id[i])
            out.append(f"      id={cid:<3} {nm.get(cid, '?'):<28} conf={float(det.confidence[i]):.2f}  box={[int(v) for v in det.xyxy[i]]}")
    except Exception:
        out.append("    !! FAILED:\n" + "".join("      " + l for l in traceback.format_exc().splitlines(True)[-6:]))
    out.append("")
text = "\n".join(out)
print(text)
open(os.path.join(HERE, "check_models_report.txt"), "w", encoding="utf-8").write(text)
print("Saved: check_models_report.txt")
