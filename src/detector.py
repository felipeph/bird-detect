import cv2
import os
import numpy as np

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
        algo = config.get("algo", "MOG2")
        
        if algo == "MOG2":
            self.back_sub = cv2.createBackgroundSubtractorMOG2(
                history=config.get("history", 500),
                varThreshold=config.get("threshold", 16.0),
                detectShadows=config.get("detectShadows", True)
            )
        else:
            self.back_sub = cv2.createBackgroundSubtractorKNN(
                history=config.get("history", 500),
                dist2Threshold=config.get("threshold", 400.0),
                detectShadows=config.get("detectShadows", True)
            )

    def process_image(self, img_path, out_raw_dir, out_ann_dir):
        img = safe_imread(img_path)
        if img is None:
            return False

        fg_mask = self.back_sub.apply(img)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected = False
        min_area = self.config.get("min_contour_area", 50)
        
        img_ann = img.copy()

        for c in contours:
            if cv2.contourArea(c) > min_area:
                detected = True
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(img_ann, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if detected:
            os.makedirs(out_raw_dir, exist_ok=True)
            os.makedirs(out_ann_dir, exist_ok=True)
            filename = os.path.basename(img_path)
            safe_imwrite(os.path.join(out_raw_dir, filename), img)
            safe_imwrite(os.path.join(out_ann_dir, filename), img_ann)
            return True

        return False

