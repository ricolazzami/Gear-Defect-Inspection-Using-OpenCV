import cv2
import os

THRESHOLD_MAX = 30.0

def inspect_frame(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        cv2.rectangle(img, (0, 0), (img.shape[1], 45), (0, 150, 0), -1)
        cv2.putText(img, "STATUS: PASS - QUALITY VERIFIED", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return img, False

    cnt = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(cnt, returnPoints=False)
    if hull is None or len(hull) <= 3:
        cv2.rectangle(img, (0, 0), (img.shape[1], 45), (0, 150, 0), -1)
        cv2.putText(img, "STATUS: PASS - QUALITY VERIFIED", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return img, False

    defects = cv2.convexityDefects(cnt, hull)
    if defects is None:
        cv2.rectangle(img, (0, 0), (img.shape[1], 45), (0, 150, 0), -1)
        cv2.putText(img, "STATUS: PASS - QUALITY VERIFIED", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return img, False

    has_defect = False
    for i in range(defects.shape[0]):
        s, e, f, d_raw = defects[i, 0] if defects.ndim == 3 else defects[i]
        actual_distance = d_raw / 256.0
        
        if actual_distance > THRESHOLD_MAX:
            has_defect = True
            pt = tuple(cnt[f][0])
            box = 30
            p1 = (max(0, pt[0] - box), max(0, pt[1] - box))
            p2 = (min(img.shape[1], pt[0] + box), min(img.shape[0], pt[1] + box))
            
            cv2.rectangle(img, p1, p2, (0, 0, 255), 2)
            label = "Structural Defect"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(img, (p1[0], max(0, p1[1] - th - 6)), (p1[0] + tw + 6, p1[1]), (0, 0, 255), -1)
            cv2.putText(img, label, (p1[0] + 3, p1[1] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            break

    if has_defect:
        cv2.rectangle(img, (0, 0), (img.shape[1], 45), (0, 0, 180), -1)
        cv2.putText(img, "STATUS: FAIL - DEFECT DETECTED", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    else:
        cv2.rectangle(img, (0, 0), (img.shape[1], 45), (0, 150, 0), -1)
        cv2.putText(img, "STATUS: PASS - QUALITY VERIFIED", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    return img, has_defect

def run_conveyor_simulation():
    window_name = "Conveyor Belt CV Inspector (Press 'q' to stop)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 700, 700)

    good_files = [os.path.join("validation_dataset/good", f) for f in sorted(os.listdir("validation_dataset/good"))]
    defect_files = [os.path.join("validation_dataset/defect", f) for f in sorted(os.listdir("validation_dataset/defect"))]
    
    stream = []
    for g, d in zip(good_files, defect_files):
        stream.extend([g, d])

    print("=== Conveyor Belt Live Simulation Starting ===")
    for idx, path in enumerate(stream, 1):
        frame = cv2.imread(path)
        if frame is None:
            continue

        result_frame, defect = inspect_frame(frame)
        cv2.imshow(window_name, result_frame)
        
        status_text = "TRIGGER: ACTUATOR PUSH (REJECT)" if defect else "TRIGGER: CONVEYOR PASS"
        print(f"Item #{idx:02d} | Source: {os.path.basename(path)} -> {status_text}")
        
        key = cv2.waitKey(1200) & 0xFF
        if key == ord('q'):
            print("Simulation aborted by user.")
            break

    cv2.destroyAllWindows()
    print("=== Simulation Completed ===")

if __name__ == "__main__":
    run_conveyor_simulation()
