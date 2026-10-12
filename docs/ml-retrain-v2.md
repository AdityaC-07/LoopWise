# LoopWise — model retrain v2 (Colab)

**Why this exists.** A real user photo of a crushed clear PET bottle returned
`metal` at high confidence. That is not a wiring bug — it is the failure mode
already measured in `ml/runs/baseline-20261010T124443Z/evaluation_report.md`:

| Measured fact | Source |
|---|---|
| Errors are **confident**: incorrect predictions have median conf 0.76, p75 **0.98**, max **1.00** | §5 |
| Confidence cannot separate errors; no threshold both keeps coverage and removes them | §6.1 |
| `plastic` test acc **0.930**, confusion list contains **metal**; `glass` is the error sink | §7 |
| 0.9461 top-1 is **in-distribution only** (single Kaggle source); §7 warns it is not field accuracy | §2, §7 |
| The true class is still in the **top-3 for 98.8%** of images | §7 |

**Already shipped (no retrain):** the result page now always shows the
runners-up, so a confidently-wrong `metal` still surfaces `plastic`. That is the
cheap safety net. This document is the other half — actually making the model
better.

---

## 1. What will and will not fix it

**Will not fix it:**
- More epochs. The v1 run early-stopped at 28 with the best checkpoint at
  epoch **13** and val top-1 plateaued at **0.9419**. The nano model saturated
  on this dataset. More epochs of the same recipe re-learns the same thing.
- Lowering `LOW_CONFIDENCE_THRESHOLD`. Errors are confident; thresholding does
  not catch them (§6.1).

**Might fix it (this notebook):**
1. **Bigger base** — `yolo26s-cls` instead of `yolo26n-cls`.
2. **Higher resolution** — `imgsz` 384 instead of 224. Transparent/crumpled
   objects need texture detail that 224 throws away.
3. **Cosine LR + longer schedule** — `cos_lr=True`, 100 epochs, `patience=25`.
4. **Label cleaning** — `prepare_dataset.py` flagged **5 perceptual-hash groups
   spanning multiple classes** and kept them all ("possible mislabel"). Those
   are ~5 guaranteed contradictions for the model to memorise.

**Will fix it, but needs you (out of scope for automation):**
- The dataset is **single-source** (Kaggle `mostafaabla`, ODbL). 7,233 images,
  540–800 per class. Field photos of mixed bins look nothing like these studio
  shots. **No hyperparameter change closes that gap** — only more, more
  representative data does. If v2 still misreads real photos, collecting ~1–2k
  LoopWise-style photos is the real answer, and the app's per-item correction
  flow is already capturing exactly those labels.

---

## 2. Acceptance bar (do not skip)

v1 reference numbers, reproduced from the ONNX:

| Metric | v1 |
|---|---|
| test top-1 | 0.9461 |
| val top-1 | 0.9419 |
| `plastic` class acc | 0.930 |
| `metal` class acc | 0.896 |

**Adopt v2 only if** all hold:
- test top-1 **≥ 0.96**, **and**
- `plastic` top-1 **≥ 0.95**, **and**
- no per-class accuracy regresses by more than 1 pp.

If v2 misses the bar, **keep v1 deployed**. A bigger model that is still
confidently wrong on plastic is not an upgrade. Report the numbers either way.

---

## 3. Colab notebook

Runtime → **Change runtime type → GPU (T4)**. Each `# %%` block is a cell.

### Cell 0 — install

```python
# %%
%pip install -q ultralytics onnx onnxruntime
import torch
assert torch.cuda.is_available(), "Select a GPU runtime (T4) before running."
print(torch.cuda.get_device_name(0))
```

### Cell 1 — get the dataset

Option A (recommended): upload a zip of your prepared dataset to Google Drive.

```python
# %%
from google.colab import drive
drive.mount('/content/drive')

import shutil, pathlib, zipfile
zip_path = '/content/drive/MyDrive/loopwise/waste-classify.zip'
assert pathlib.Path(zip_path).is_file(), f"Upload the zip to {zip_path}"
with zipfile.ZipFile(zip_path) as z:
    z.extractall('/content/raw')
print(sorted(p.name for p in pathlib.Path('/content/raw').iterdir()))
```

Option B: re-download from Kaggle and re-prepare with the repo's own script.

```python
# %%
# !pip install -q kaggle
# import os; os.environ['KAGGLE_USERNAME']='...'; os.environ['KAGGLE_KEY']='...'
# !kaggle datasets download -d mostafaabla/garbage-classification -p /content/raw --unzip
# !git clone -q https://github.com/AdityaC-07/LoopWise.git /content/LoopWise
# !python /content/LoopWise/ml/prepare_dataset.py \
#     --source /content/raw/Garbage_classification \
#     --mapping /content/LoopWise/ml/source_mapping.json \
#     --out /content/waste-classify
```

Normalise the layout so `/content/waste-classify` holds `train/ val/ test/`
plus `manifest.csv`.

```python
# %%
import pathlib, shutil
raw = pathlib.Path('/content/raw')
if (raw / 'train').is_dir():
    DATA = raw
else:  # nested one level, e.g. raw/waste-classify/train
    cand = next(p for p in raw.iterdir() if (p / 'train').is_dir())
    DATA = cand
DATA = DATA.resolve()
assert (DATA / 'train').is_dir() and (DATA / 'val').is_dir()
print("dataset root:", DATA)
```

### Cell 2 — quarantine the flagged cross-class collisions

`prepare_dataset.py` kept 5 perceptual-hash groups that span more than one
class. Drop the minority member of each group so the model is not asked to
learn a contradiction.

```python
# %%
import csv, collections, pathlib, os

DATA = pathlib.Path(DATA)
manifest = DATA / 'manifest.csv'
if not manifest.is_file():
    print("no manifest — skipping quarantine (cannot audit collisions)")
else:
    rows = list(csv.DictReader(manifest.open(encoding='utf-8')))
    groups = collections.defaultdict(list)
    for r in rows:
        groups[r['dhash']].append(r)

    dropped, kept_groups = [], 0
    for dhash, members in groups.items():
        by_class = collections.Counter(m['final_class'] for m in members)
        if len(by_class) < 2:
            continue
        kept_groups += 1
        majority = by_class.most_common(1)[0][0]
        for m in members:
            if m['final_class'] != majority:
                p = DATA / m['output_relpath']
                if p.is_file():
                    os.remove(p)
                    dropped.append(m['output_relpath'])

    print(f"{kept_groups} cross-class group(s); quarantined {len(dropped)} file(s):")
    for d in dropped:
        print("  -", d)
```

This is intentionally conservative: it removes only the minority label in a
contradicting near-duplicate group. Every removal is printed for audit.

### Cell 3 — verify the 8-class invariant

Ultralytics derives class indices by **sorting folder names alphabetically**.
If this check fails the exported class map will mislabel every prediction.

```python
# %%
import json, pathlib
CANONICAL = ["battery_hazardous", "glass", "metal", "organic",
             "other_residue", "paper_cardboard", "plastic", "textile"]
for split in ("train", "val", "test"):
    found = sorted(p.name for p in (pathlib.Path(DATA) / split).iterdir() if p.is_dir())
    assert found == CANONICAL, f"{split} folders {found} != {CANONICAL}"
assert CANONICAL == sorted(CANONICAL)
print("class order OK:", CANONICAL)
```

### Cell 4 — train

```python
# %%
from ultralytics import YOLO

BASE = "yolo26s-cls.pt"   # was yolo26n-cls.pt
IMGSZ = 384               # was 224

model = YOLO(BASE)
results = model.train(
    data=str(DATA),
    epochs=100,           # v1 stopped early at 28 (best @13) — cosine LR uses the full budget
    imgsz=IMGSZ,
    batch=32,             # 384px + small model; drop to 16 if T4 OOMs
    patience=25,
    seed=42,
    deterministic=True,
    cos_lr=True,          # smoother decay than the default step schedule on a small dataset
    device=0,
    project="/content/runs",
    name="v2-384s",
    exist_ok=True,
    verbose=True,
)
print("val top1", results.top1, "top5", results.top5)
```

### Cell 5 — evaluate on the held-out test split

```python
# %%
test_metrics = model.val(data=str(DATA), split="test", imgsz=IMGSZ)
print("TEST top1", test_metrics.top1, "top5", test_metrics.top5)
```

Per-class numbers are printed in the run's `results.png` and in the validation
summary — check `plastic` and `metal` specifically against the bar in §2.

### Cell 6 — export ONNX + class map

```python
# %%
import json, numpy as np, onnx, onnxruntime as ort, pathlib

run_dir = pathlib.Path("/content/runs/v2-384s")
exported = model.export(format="onnx")
onnx_path = pathlib.Path(exported)
onnx.checker.check_model(onnx.load(str(onnx_path)))
print("onnx.checker OK")

sess = ort.InferenceSession(str(onnx_path))
inp = sess.get_inputs()[0]
shape = [d if isinstance(d, int) and d > 0 else (1 if i == 0 else 3 if i == 1 else IMGSZ)
         for i, d in enumerate(inp.shape or [1, 3, IMGSZ, IMGSZ])]
out = sess.run(None, {inp.name: np.random.rand(*shape).astype("float32")})
assert out[0].shape[-1] == len(CANONICAL), f"output classes {out[0].shape[-1]} != 8"
print("smoke inference OK:", shape, "->", list(out[0].shape))

class_map = {str(i): c for i, c in enumerate(CANONICAL)}
map_path = onnx_path.with_name(onnx_path.stem + ".class-index-map.json")
map_path.write_text(json.dumps(class_map, indent=2), encoding="utf-8")
print("class map:", map_path)
```

> The exported graph's output is **already softmaxed** (same as v1). The backend
> reads `MODEL_OUTPUT=probabilities` by default and must **never** re-softmax it
> — that bug capped every confidence at 0.2797 and returned `unknown` for 100%
> of images (evaluation report §6).

### Cell 7 — download the artifacts

```python
# %%
from google.colab import files
import shutil, pathlib
out_dir = pathlib.Path('/content/loopwise-v2')
out_dir.mkdir(exist_ok=True)
shutil.copy(run_dir / 'weights/best.pt', out_dir / 'best.pt')
shutil.copy(onnx_path, out_dir / onnx_path.name)
shutil.copy(map_path, out_dir / map_path.name)
shutil.copy(run_dir / 'results.csv', out_dir / 'results.csv')
for f in out_dir.iterdir():
    files.download(str(f))
```

---

## 4. Landing the result locally

1. Put the downloaded files in `ml/models/`:
   - `loopwise-yolo26n-cls.onnx` → rename to your chosen artifact name
   - `loopwise-yolo26n-cls.class-index-map.json` (same stem)
   - keep `best.pt` in `ml/runs/<run>/weights/`
2. **Keep `low_confidence_threshold = 0.35`.** It is a safety net, not a tuning
   knob; the v1 sweep showed no threshold removes most errors (§6.1).
3. Start the backend against the new weights:

```powershell
cd backend
$env:DEMO_MODE = "false"
$env:MODEL_PATH = "C:\Users\Agniv Dutta\LoopWise\ml\models\loopwise-yolo26n-cls.onnx"
$env:CLASS_INDEX_MAP = "C:\Users\Agniv Dutta\LoopWise\ml\models\loopwise-yolo26n-cls.class-index-map.json"
$env:MODEL_VERSION = "yolo26s-cls-v2"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Re-run the evaluation against the **deployed ONNX** (not the `.pt`), so the
   backend preprocessing path is what gets measured:

```powershell
ml\.venv\Scripts\python.exe ml\evaluate.py `
  --onnx ml\models\loopwise-yolo26n-cls.onnx `
  --class-map ml\models\loopwise-yolo26n-cls.class-index-map.json `
  --data ml\data\waste-classify --splits test val --preprocess backend `
  --out ml\runs\v2-eval
```

5. Regression tests (the real-artifact integration test skips if the file is
   missing, so run it explicitly after swapping):

```powershell
.venv\Scripts\python.exe -m pytest backend\tests -q
.venv\Scripts\python.exe -m pytest ml\tests -q
```

6. Re-test the original photo end to end. Expect either a correct `plastic`
   prediction **or** `plastic` appearing in the new "Other possible matches"
   list. Both are acceptable; a confident `metal` with no `plastic` anywhere in
   the top-3 is not.

---

## 5. Licence reminder

`yolo26s-cls.pt` and weights derived from it are **AGPL-3.0-or-later**
(Ultralytics); LoopWise itself is MIT. The Kaggle dataset is **ODbL-style with
attribution required**. This is flagged unresolved in the evaluation report §8
and retraining does not change it — resolve before distributing weights.
