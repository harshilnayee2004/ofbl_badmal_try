import torch
import cv2
from PIL import Image
import numpy as np
from threading import Lock


class RFDETRProcessor:
    def __init__(self, model_path: str = None, resolution: int = 1024, threshold: float = 0.60,label: str = "None"):
        """
        Initialize and load RF-DETR model
        """
        from rfdetr import RFDETRSmall

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.threshold = threshold
        self.lock = Lock()
        self.label = label

        print(f"[INFO] Loading RF-DETR model from: {model_path}")
        print(f"[INFO] Using device: {self.device}")

        if model_path is None:
            self.model = RFDETRSmall(
                resolution=resolution
            )
        else:
            self.model = RFDETRSmall(
                pretrain_weights=model_path,
                resolution=resolution
            )

        print("[INFO] Model loaded successfully.")

    def process_image(self, image: np.ndarray):
        """
        Accepts OpenCV BGR image (numpy array)
        Returns list of detections:
        [
            {
                "bbox": [x1, y1, x2, y2],
                "confidence": float,
                "label": str
            }
        ]
        """
        if image is None:
            print("Image is Not available.")
            return []

        try:
            with self.lock:  # Thread safety for FastAPI
                image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                detections = self.model.predict(image_pil, threshold=self.threshold)

            results = []

            if detections is None or len(detections.xyxy) == 0:
                return results

            for i in range(len(detections.xyxy)):
                x1, y1, x2, y2 = detections.xyxy[i].astype(int)
                score = float(detections.confidence[i])

                results.append({
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": score,
                    "label": self.label
                })
            return results

        except Exception as e:
            print(f"[ERROR] Inference failed: {e}")
            return []

    def close(self):
        """
        Explicit cleanup method (recommended for FastAPI shutdown event)
        """
        print("[INFO] Releasing RF-DETR model...")

        if hasattr(self, "model"):
            del self.model

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print("[INFO] Model released successfully.")

    def __del__(self):
        """
        Destructor (fallback cleanup)
        """
        self.close()