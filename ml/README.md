# LoopWise ML — YOLO26 training workflow

> Status: scaffolding complete. **No dataset, no weights, no trained model.**
> Nothing here has been downloaded and no training has run. Demo (mock) mode
> remains the only active inference path in the backend.

## 1. ML readiness status (verified 2026-10-10, this machine)

| Asset | State |
|---|---|
| Dataset (waste photos + labels) | **MISSING** — no dataset directory exists anywhere under `C:\Projects\LoopWise`. Training is blocked until it is provided (requirements in §4). |
| Class labels | **DEFINED (provisional)** — 8 MVP classes in `ml/classes.json` / `ml/data.yaml`, matching the 8 mock-pool `material_id`s that have full guidance entries. Full taxonomy (25 materials) in `backend/app/seeds/materials.py`. Labels stay provisional until cross-checked against a real model's outputs (arch U2). |
| Pretrained weights (`yolo26n-cls.pt`) | **NOT DOWNLOADED** — will be fetched automatically by Ultralytics on first approved `train.py` run. |
| Trained/fine-tuned weights | **DO NOT EXIST** — no `.pt`/`.onnx` anywhere in the repo (verified by filesystem search). |
| Training packages (torch, ultralytics, onnx) | **NOT INSTALLED** — backend `.venv` contains only `fastapi/pillow/pytest` (+ deps). `ml/requirements-ml.txt` is install-isolated to `ml/.venv`. |
| onnxruntime / numpy in backend env | **NOT INSTALLED** — `ONNXClassifier` degrades honestly (`INFERENCE_FAILED`) until the backend env gains them; factory stays on mock. |
| Compute (this machine) | Windows 10, i5-1135G7 (4C/8T), 7.7 GB RAM, Intel Iris Xe (no CUDA), ~235 GB free disk. CPU-only training is feasible for `yolo26n-cls` but slow (expect several hours for 50 epochs); a Colab T4 GPU is recommended. |
| Backend integration | **READY** — `ONNXClassifier` reads input size from ONNX metadata, maps indices via `CLASS_INDEX_MAP`, applies the 0.35 unknown threshold, and never labels mock output as genuine. Only `MODEL_PATH`/`CLASS_INDEX_MAP`/`MODEL_VERSION` env values are missing (by design — no model yet). |

## 2. Task decision: classification, not detection

The product contract (`POST /api/v1/classify` → one `predicted_class` + `top3`) and UX (single-item BinCard) describe **whole-image classification**: one photo, one item, one bin. No bounding-box annotation exists anywhere in the repo, and the 25 `material_id` labels are object-level material classes, not boxes. Therefore: fine-tune **YOLO26 as a classifier** (`yolo26n-cls`, `yolo classify`), which outputs class confidences that map 1:1 onto the `top3` contract. (The backend `_parse_logits` also accepts YOLO detection tensors, so a future detector stays compatible without code changes.)

## 3. Reproducible workflow

```
ml/
  requirements-ml.txt   training deps (isolated venv; backend untouched)
  data.yaml             dataset config template (fixed class order 0-7)
  classes.json          canonical index -> material_id
  validate_dataset.py   stdlib-only gate: structure, counts, disjoint splits (exit 2 if unready)
  train.py              seeds + deterministic + early stopping + val/test metrics + settings_used.json
  export_onnx.py        .pt -> verified .onnx + onnxruntime smoke test + class-index-map.json
  runs/  models/  data/  (git-ignored; created on use)
```

Reproducibility: `--seed 42`, `deterministic=True`, timestamped run dirs, `settings_used.json` + `metrics.json` per run, early stopping (`--patience 15`), final `test/` split eval (top-1/top-5).

## 4. Dataset requirements (exact — training blocked until all hold)

```
<root>/train/<material_id>/*.jpg   <root>/val/<material_id>/*.jpg   <root>/test/<material_id>/*.jpg
```
- 8 class folders exactly as named in `ml/classes.json` (e.g. `plastic_pet_bottle/`).
- Formats: JPEG, PNG, WebP. Minimum **20 non-empty images per class per split** (hard gate); recommended **≥100 train / ≥20 val / ≥20 test**.
- Splits disjoint: no filename in two splits (checked). Single dominant item per photo, roughly matching phone-camera conditions.
- Licensed for ML training; no faces/legible plates/private data; strip EXIF GPS before use.
- `python ml/validate_dataset.py --data <root>` must exit 0. If only `train/` exists, `--auto-split 0.15` creates `val/` deterministically (seed 42).

## 5. Approval gate — do NOT run until explicitly approved

Expected downloads (first run only, sizes approx — confirmed at runtime):
- PyPI ML stack (torch CPU + torchvision + ultralytics + onnx/onnxruntime + numpy): order of ~250–350 MB into `ml/.venv` only.
- `yolo26n-cls.pt` pretrained checkpoint via Ultralytics (~5 MB scale, nano variant).

Compute: CPU-only on this machine, 50 epochs, batch 32 (reduce to 16/8 on OOM), est. multiple hours; GPU (e.g. free Colab T4) cuts this to tens of minutes.

Commands (each needs explicit approval first):
```powershell
python -m venv ml/.venv; ml/.venv/Scripts/python -m pip install -r ml/requirements-ml.txt
ml/.venv/Scripts/python ml/validate_dataset.py --data ml/data/waste-classify
ml/.venv/Scripts/python ml/train.py --data ml/data/waste-classify --epochs 50 --device cpu
ml/.venv/Scripts/python ml/export_onnx.py --weights ml/runs/<run>/weights/best.pt --out ml/models/loopwise-yolo26n-cls.onnx
```

After export: copy `.onnx` + `.class-index-map.json` to the server, set `MODEL_PATH` / `CLASS_INDEX_MAP` / `MODEL_VERSION=yolo26n-cls-v1`, install `onnxruntime+numpy` in the backend env, set `DEMO_MODE=false`. No retraining from user corrections ever (arch rule: `reviewed=true` human gate before any export use).

## 6. What changed in this step (no app rebuild)

- New `ml/` directory only (scripts + configs + this README).
- `backend/app/core/config.py`: additive `MODEL_VERSION` setting (default `"yolo26-v1"`).
- `onnx_classifier.py`: `model_version` now reflects `MODEL_VERSION` instead of a hardcoded string.
- `backend/tests/test_inference.py`: one assertion for the `MODEL_VERSION` default.
- No frontend/backend rebuild, no AWS, no downloads, no training run, privacy protections untouched.
