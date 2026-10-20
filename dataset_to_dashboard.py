import json

from datetime import datetime, timezone

from pathlib import Path

from uuid import uuid4

from ultralytics import YOLO

MODEL = Path(
    "/workspaces/vision-system/data/runs/weld_public/baseline_v1-2/weights/best.pt"
)

IMAGES = Path("/workspaces/vision-system/datasets/dataset-feee0b80/images/val")

OUTPUT = Path("/workspaces/vision-system/data/dashboard-demo")

OUTPUT.mkdir(parents=True, exist_ok=True)

model = YOLO(str(MODEL))

run_id = uuid4().hex[:12]

images = sorted(
    p
    for p in IMAGES.iterdir()
    if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
)

if not images:
    raise RuntimeError(f"No images found in {IMAGES}")

# Start with one image. Change to images[:20] after it works.

for index, image in enumerate(images[:1]):
    result = model.predict(source=str(image), device="cpu", conf=0.25, verbose=False)[0]

    detections = [
        (result.names[int(box.cls.item())], float(box.conf.item()))
        for box in result.boxes
    ]

    # Demo rules: any bad weld/defect takes priority.

    bad = [d for d in detections if d[0] in {"Bad Weld", "Defect"}]

    good = [d for d in detections if d[0] == "Good Weld"]

    if bad:
        state, selected = "FAIL", max(bad, key=lambda d: d[1])

    elif good:
        state, selected = "PASS", max(good, key=lambda d: d[1])

    else:
        state, selected = "REVIEW", (None, None)

    inspection_id = f"dataset-{run_id}-{index:04d}"

    payload = {
        "schemaVersion": 1,
        "eventId": inspection_id,
        "inspectionId": inspection_id,
        "state": state,
        "result": state,
        "passFail": {"PASS": True, "FAIL": False}.get(state),
        "className": selected[0],
        "confidence": selected[1],
        "message": f"Dataset demo: {image.name}; detections={detections}",
        "profile": "weld_public",
        "healthStatus": "HEALTHY",
        "runtimeMode": "DATASET_DEMO",
        "observedAt": datetime.now(timezone.utc).isoformat(),
    }

    payload_file = OUTPUT / f"{inspection_id}.json"

    payload_file.write_text(json.dumps(payload, indent=2))

    result.save(filename=str(OUTPUT / f"{inspection_id}.jpg"))

    print(f"{image.name}: {state}")

    print(f"Message: {payload_file}")
