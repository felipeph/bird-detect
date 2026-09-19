import cv2
import os
import numpy as np
from ultralytics import YOLO

def safe_imread(path: str):
    """Lê imagem de forma segura no Windows mesmo com acentos/espaços no caminho."""
    try:
        img = cv2.imread(path)
        if img is not None:
            return img
        with open(path, "rb") as f:
            data = np.frombuffer(f.read(), dtype=np.uint8)
            return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None

def safe_imwrite(path: str, img):
    """Grava imagem de forma segura no Windows mesmo com acentos/espaços no caminho."""
    try:
        ext = os.path.splitext(path)[1]
        if not ext:
            ext = ".jpg"
        success, buf = cv2.imencode(ext, img)
        if success:
            with open(path, "wb") as f:
                f.write(buf)
            return True
    except Exception:
        pass
    return cv2.imwrite(path, img)

class BirdDetector:
    def __init__(self, config):
        self.config = config
        self.confidence = config.get("yolo_confidence", 0.25)
        # Load YOLOv8 Medium model (downloads automatically if missing)
        self.model = YOLO("yolov8m.pt")

    def process_image(self, img_path, out_raw_dir, out_ann_dir):
        img = safe_imread(img_path)
        if img is None:
            return False

        # Fazer predição
        results = self.model.predict(img, conf=self.confidence, verbose=False)
        
        detected = False
        img_ann = img.copy()

        for result in results:
            for box in result.boxes:
                # Classe 14 no COCO dataset é 'bird'
                if int(box.cls[0]) == 14:
                    detected = True
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cv2.rectangle(img_ann, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(img_ann, f"Bird {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        if detected:
            os.makedirs(out_raw_dir, exist_ok=True)
            os.makedirs(out_ann_dir, exist_ok=True)
            filename = os.path.basename(img_path)
            safe_imwrite(os.path.join(out_raw_dir, filename), img)
            safe_imwrite(os.path.join(out_ann_dir, filename), img_ann)
            return True

        return False

