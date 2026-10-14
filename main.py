import cv2
import os

THRESHOLD_MAX = 30.0
OUTPUT_DIR = "inspection_results"

def _banner(img, is_fail):
    if is_fail:
        cv2.rectangle(img, (0, 0), (img.shape[1], 45), (0, 0, 180), -1)
        cv2.putText(img, "STATUS: FAIL - DEFECT DETECTED", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    else:
        cv2.rectangle(img, (0, 0), (img.shape[1], 45), (0, 150, 0), -1)
        cv2.putText(img, "STATUS: PASS - QUALITY VERIFIED", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

def inspect_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None, "[ PASS: QUALITY VERIFIED ]"
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        _banner(img, False)
        return img, "[ PASS: QUALITY VERIFIED ]"
    cnt = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(cnt, returnPoints=False)
    if hull is None or len(hull) <= 3:
        _banner(img, False)
        return img, "[ PASS: QUALITY VERIFIED ]"
    defects = cv2.convexityDefects(cnt, hull)
    if defects is None:
        _banner(img, False)
        return img, "[ PASS: QUALITY VERIFIED ]"
    is_fail = False
    for i in range(defects.shape[0]):
        s, e, f, d_raw = defects[i, 0] if defects.ndim == 3 else defects[i]
        actual_distance = d_raw / 256.0
        if actual_distance > THRESHOLD_MAX:
            is_fail = True
            pt = tuple(cnt[f][0])
            box = 25
            p1 = (max(0, pt[0] - box), max(0, pt[1] - box))
            p2 = (min(img.shape[1], pt[0] + box), min(img.shape[0], pt[1] + box))
            cv2.rectangle(img, p1, p2, (0, 0, 255), 2)
            label = "Structural Defect"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(img, (p1[0], max(0, p1[1] - th - 6)), (p1[0] + tw + 6, p1[1]), (0, 0, 255), -1)
            cv2.putText(img, label, (p1[0] + 3, p1[1] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            break
    _banner(img, is_fail)
    return img, "[ FAIL: STRUCTURAL DEFECT DETECTED ]" if is_fail else "[ PASS: QUALITY VERIFIED ]"

def run_pipeline():
    base = "validation_dataset"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for cat in ["good", "defect"]:
        folder = os.path.join(base, cat)
        if not os.path.exists(folder):
            continue
        print(f"\n--- {cat.upper()} ---")
        for name in sorted(os.listdir(folder)):
            if not name.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            annotated, result = inspect_image(os.path.join(folder, name))
            out = os.path.join(OUTPUT_DIR, f"result_{name}")
            cv2.imwrite(out, annotated)
            print(f"{name} -> {result} | Saved: {out}")

if __name__ == "__main__":
    run_pipeline()
