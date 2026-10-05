# Weld Model Workflow

This is the canonical workflow for collecting weld images, training a model on
a desktop/GPU machine, and deploying the approved model to a Raspberry Pi.

Training does not run on the Pi in the supported production workflow. The Pi
captures representative images, runs the optimized model, and reports inspection
results. Training, labeling, and model export happen on a desktop or GPU machine.

## 1. Decide the inspection classes

Do not train with good weld images alone. At minimum, collect independently
reviewed examples of:

- good welds;
- bad welds, including each defect type that matters;
- a part with a missing weld;
- no part present;
- unclear cases, glare, shadows, position changes, and normal production variation.

The intended first model uses these classes:

```yaml
names:
  0: good_weld
  1: bad_weld
```

A qualified weld inspector must provide the ground-truth good/bad decisions.
Do not use model output as an authoritative production acceptance decision until
it has passed a representative holdout test and a controlled production pilot.

### Current tooling limitation

The bundled `training/label_images.py`, default dataset validation, and
model-profile packaging were originally built around one class and reject empty
negative labels. They must be updated before using the recommended two-class
weld workflow end to end. Until then, use an external YOLO-compatible annotation
tool for labeling and review the generated class mapping carefully. Treat this
as a production rollout blocker, not as permission to interpret every missing
`good_weld` detection as a bad weld.

## 2. Capture images on the production Pi

The Pi camera provides the most representative images because lighting, focus,
mounting position, and reflections match the production installation.

Stop the runtime while the capture script owns the camera:

```bash
sudo systemctl stop vision.service
cd /home/ansible/vision-system
source .venv/bin/activate
```

Capture separate, clearly named sessions:

```bash
python scripts/capture_dataset_images.py \
  --profile weld \
  --camera-profile pi_camera3 \
  --label positive \
  --session good-welds-001 \
  --count 100 \
  --interval-seconds 2

python scripts/capture_dataset_images.py \
  --profile weld \
  --camera-profile pi_camera3 \
  --label negative \
  --session bad-welds-001 \
  --count 100 \
  --interval-seconds 2
```

The `positive` and `negative` values organize capture folders; they are not
the final YOLO `good_weld` and `bad_weld` annotations. A human must still
inspect and label every training image.

Restart the runtime after capture:

```bash
sudo systemctl start vision.service
```

Raw images and their quality metadata are written under:

```text
data/collections/weld/pi_camera3/<session>/
```

This directory is deliberately ignored by Git.

### Desktop camera alternative

For bench work, a USB camera can write directly to the training dataset:

```bash
python training/collect_images.py --camera 0
```

Use Pi images for final validation even if early training images came from a
desktop camera.

## 3. Transfer Pi captures to the training machine

From the `vision-system` repository on the desktop:

```bash
rsync -av \
  ansible@<pi-host>:/home/ansible/vision-system/data/collections/weld/ \
  data/collections/weld/
```

Keep a separate holdout set from different parts or production runs. Never
train on the holdout images used for final evaluation.

## 4. Label and prepare the YOLO dataset

Use a YOLO-compatible annotation tool to draw a box around each weld and assign
`good_weld` or `bad_weld`. Images without a weld use an empty label file.

Prepare this layout:

```text
data/datasets/weld/
├── data.yaml
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

Each image must have a matching `.txt` label with the same filename stem. Use
an absolute path valid on the training machine in `data.yaml`; do not copy the
existing machine-specific Windows path from the sample dataset.

```yaml
path: /absolute/path/to/vision-system/data/datasets/weld
train: images/train
val: images/val
names:
  0: good_weld
  1: bad_weld
```

## 5. Train on the desktop/GPU machine

Install the desktop dependencies outside the lean development container, then
run:

```bash
python training/train_pipeline.py
```

Enter `weld` when prompted. Training reads images from `data/datasets/weld/`
and writes the complete, disposable Ultralytics run under:

```text
data/runs/weld/
```

The pipeline copies its best checkpoint into the deployable profile:

```text
models/weld/
├── best.pt
├── latest/best.pt
├── versions/vN/best.pt
├── classes.txt
├── config.json
└── training_report.json
```

`data/runs/` is ignored by Git. Deployable files under `models/` are tracked.

## 6. Validate before promotion

Test the candidate against holdout images that were not used for training:

```bash
python scripts/validate_model.py \
  --profile weld \
  --model models/weld/best.pt \
  --model-format pt \
  --image <holdout-image>
```

Review results by defect type and production condition, not only one combined
accuracy number. False passes are the critical failure mode.

Configure the runtime decision mapping in `profiles/weld/config.yaml`:

```yaml
profile_name: weld
inspection:
  acceptable_classes:
    - good_weld
  reject_classes:
    - bad_weld
  minimum_confidence: 0.35
  required_consecutive_detections: 3
  allowed_no_detection_frames: 3
  allow_simulation: false
```

Tune the confidence and stability values from measured holdout and pilot data.

## 7. Export the Pi model

The Pi runtime prefers NCNN over the desktop `.pt` file. Always regenerate the
NCNN export after approving a new model:

```bash
python scripts/export_profile_to_ncnn.py --profile weld --imgsz 320
```

This writes:

```text
models/weld/best_ncnn_model/
├── model.ncnn.bin
├── model.ncnn.param
├── model_ncnn.py
└── metadata.yaml
```

## 8. Commit and deploy

Commit the approved profile and both model formats:

```bash
git add models/weld profiles/weld/config.yaml
git commit -m "Update weld inspection model"
git push
```

In `dmca-iot-iac/ansible/production`, add the target Pi serial under `[vision]`.
Then deploy from the `dmca-iot-iac` development container:

```bash
cd ansible
uv run ansible-playbook \
  -Kki production \
  --tag setup \
  --limit <pi-serial> \
  playbook.yaml
```

The role updates the repository, runs the native Pi installer, restarts
`vision.service`, and starts the `iot-vision` MQTT adapter.

## 9. Verify the Pi

```bash
systemctl status vision.service
journalctl -u vision.service -n 100 --no-pager
curl http://127.0.0.1:8000/status
docker compose -f /docker/docker-compose.yaml ps vision
docker compose -f /docker/docker-compose.yaml logs --tail 100 vision
```

Confirm the status names the expected profile and model path before starting a
controlled production pilot.

## 10. Repeat safely

Use review images and new production captures to improve the dataset. A new
model follows the same label, train, holdout, NCNN export, Git, and Ansible
sequence. Keep the previous Git revision available for rollback.

## Remaining implementation blockers

Before a two-class weld model is production-ready:

1. Update the bundled labeling, negative-sample validation, and profile-packaging
   tools for multiple classes.
2. Make the Ansible-selected runtime profile configurable; the current installer
   starts `yellow_daifuku` by default.
3. Replace or constrain the shared wildcard AWS IoT certificate policy.
