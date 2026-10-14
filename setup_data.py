import os
import shutil
import json
import glob
import cv2
import kagglehub

DATASET = "yimingfang1994/plastic-gear-surface-defect-dataset"
VERSION_PATH = kagglehub.dataset_download(DATASET)
print(f"Downloaded to: {VERSION_PATH}")

for root, dirs, files in os.walk(VERSION_PATH):
    if "images" in dirs:
        VERSION_PATH = root
        break
if os.path.exists(os.path.join(VERSION_PATH, "versions")):
    subs = sorted(glob.glob(os.path.join(VERSION_PATH, "versions", "*")))
    if subs:
        VERSION_PATH = subs[-1]

img_dir = os.path.join(VERSION_PATH, "images")
json_dir = os.path.join(VERSION_PATH, "json")
print(f"Using: {VERSION_PATH}")

STRUCTURAL = {"broken", "missing", "shortshot", "damage"}

def max_dist(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return 9999
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0
    c = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(c, returnPoints=False)
    if hull is None or len(hull) <= 3:
        return 0
    defects = cv2.convexityDefects(c, hull)
    if defects is None:
        return 0
    if defects.ndim == 3:
        return max(d[0][3] / 256.0 for d in defects)
    return max(d[3] / 256.0 for d in defects)

good_pool = []
defect_pool = []
for jf in glob.glob(os.path.join(json_dir, "*.json")):
    name = os.path.basename(jf).replace(".json", ".png")
    if not name.startswith("endface"):
        continue
    ipath = os.path.join(img_dir, name)
    if not os.path.exists(ipath):
        continue
    labels = set(s["label"] for s in json.load(open(jf))["shapes"])
    d = max_dist(ipath)
    if labels & STRUCTURAL:
        defect_pool.append((name, d, labels))
    else:
        good_pool.append((name, d, labels))

good_pool = sorted(good_pool, key=lambda x: x[1])
defect_pool = sorted(defect_pool, key=lambda x: x[1], reverse=True)

print(f"Good pool: {len(good_pool)}, Defect pool: {len(defect_pool)}")
print("Good lowest dist:", good_pool[:3])
print("Defect highest dist:", defect_pool[:3])

selected_good = good_pool[:10]
selected_defect = defect_pool[:10]

for d in [f"validation_dataset/good", f"validation_dataset/defect"]:
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)

for i, (name, d, _) in enumerate(selected_good, 1):
    shutil.copy(os.path.join(img_dir, name), f"validation_dataset/good/good_{i}.png")
    print(f"GOOD {i}: {name} dist={d:.1f}")

for i, (name, d, _) in enumerate(selected_defect, 1):
    shutil.copy(os.path.join(img_dir, name), f"validation_dataset/defect/defect_{i}.png")
    print(f"DEFECT {i}: {name} dist={d:.1f}")

print("Dataset prepared: 10 good, 10 defect -> validation_dataset/")
