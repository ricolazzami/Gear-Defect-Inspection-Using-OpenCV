# System Architecture: Quality Inspection Pipeline
## IPO (Input-Process-Output) Model

```
+-------------------------------------------------------------+
|                            INPUT                            |
|  - Load images from validation_dataset/ (good & defect)     |
|  - Color conversion: BGR -> Grayscale (cv2.cvtColor)        |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                           PROCESS                           |
|  1. Smooth: GaussianBlur (5x5 kernel, sigma=0)              |
|  2. Binarize: cv2.threshold (127, 255, THRESH_BINARY)       |
|  3. Trace Topology: cv2.findContours (RETR_EXTERNAL)        |
|  4. Enclose: cv2.convexHull (returnPoints=False)            |
|  5. Measure Gaps: cv2.convexityDefects                      |
|  6. Scaling Correction: actual_distance = d_raw / 256.0     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                           OUTPUT                            |
|  - Tolerance Gate: actual_distance > THRESHOLD_MAX          |
|  - Visual Marker: Red bounding box around farthest_point   |
|    and visual status banner (PASS/FAIL)                     |
|  - PLC Fieldbus Signals:                                    |
|      * FAIL: [ FAIL: STRUCTURAL DEFECT DETECTED ]           |
|      * PASS: [ PASS: QUALITY VERIFIED ]                     |
+-------------------------------------------------------------+
```

## Visual Output Samples
- **Pass State**: Green header banner `STATUS: PASS - QUALITY VERIFIED`.
- **Fail State**: Red header banner `STATUS: FAIL - DEFECT DETECTED` with red bounding box annotation around structural anomalies.

## Module Responsibilities
- `setup_data.py`: Data ingestion module. Downloads dataset via `kagglehub`, filters structural defects against cosmetic defects, and populates `validation_dataset/`.
- `main.py`: Real-time batch inspection engine implementing the full IPO pipeline with OpenCV convex analysis.
- `simulate.py`: Live conveyor belt simulation runner with real-time window display and PLC signal logging.
