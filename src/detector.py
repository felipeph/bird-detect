import cv2
import os

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
        img = cv2.imread(img_path)
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
            filename = os.path.basename(img_path)
            cv2.imwrite(os.path.join(out_raw_dir, filename), img)
            cv2.imwrite(os.path.join(out_ann_dir, filename), img_ann)
            return True

        return False
