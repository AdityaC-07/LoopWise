"""Export a trained YOLO26 checkpoint to ONNX + verify + write class mapping.

  ml/.venv/Scripts/python ml/export_onnx.py \\
      --weights ml/runs/<run>/weights/best.pt \\
      --out ml/models/loopwise-yolo26n-cls.onnx

Steps:
  1. model.export(format='onnx')  (opset chosen by Ultralytics; printed)
  2. onnx.checker validation of the exported graph
  3. onnxruntime smoke inference: random input of the model's own input shape,
     assert one output tensor with <num_classes> scores
  4. Write CLASS_INDEX_MAP JSON (index -> material_id from ml/data.yaml names)
     next to the .onnx file, and print the exact backend settings to use.

Requires the ML virtualenv. Reads no dataset; downloads nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_names(repo_root: Path) -> dict[int, str]:
    import yaml  # ML env only

    with open(repo_root / "ml" / "data.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    names = cfg.get("names", {})
    return {int(k): str(v) for k, v in names.items()}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Export YOLO26 .pt to verified .onnx + class map.")
    ap.add_argument("--weights", required=True, help="Trained checkpoint (best.pt)")
    ap.add_argument("--out", required=True, help="Output .onnx path, e.g. ml/models/loopwise-yolo26n-cls.onnx")
    ap.add_argument("--opset", type=int, default=0, help="ONNX opset (0 = Ultralytics default)")
    ap.add_argument("--model-version", default="yolo26n-cls-v1",
                    help="MODEL_VERSION value to configure in the backend for these weights")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent

    from ultralytics import YOLO  # ML env only; lazy so --help works anywhere

    weights = Path(args.weights)
    if not weights.is_file():
        print(f"ERROR: checkpoint not found: {weights}", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(weights))
    exported = model.export(format="onnx", opset=args.opset or None)
    exported_path = Path(exported)
    if exported_path.resolve() != out.resolve():
        exported_path.replace(out)
    print(f"Exported ONNX: {out} ({out.stat().st_size / 1e6:.1f} MB)")

    import onnx
    graph = onnx.load(str(out))
    onnx.checker.check_model(graph)
    print("onnx.checker: graph valid")

    import numpy as np
    import onnxruntime as ort

    sess = ort.InferenceSession(str(out))
    inp = sess.get_inputs()[0]
    shape = [d if isinstance(d, int) and d > 0 else (1 if i == 0 else 3 if i == 1 else 224)
             for i, d in enumerate(inp.shape or [1, 3, 224, 224])]
    dummy = np.random.rand(*shape).astype("float32")
    outputs = sess.run(None, {inp.name: dummy})
    print(f"Smoke inference OK: input {shape} -> output {[list(o.shape) for o in outputs]}")

    names = load_names(repo_root)
    n_out = outputs[0].shape[-1] if len(outputs[0].shape) >= 1 else 0
    if n_out != len(names):
        print(f"ERROR: model outputs {n_out} classes but data.yaml defines {len(names)}. "
              "Refusing to write a mismatched class map.", file=sys.stderr)
        return 2
    class_map = {str(k): v for k, v in sorted(names.items())}
    map_path = out.with_name(out.stem + ".class-index-map.json")
    map_path.write_text(json.dumps(class_map, indent=2), encoding="utf-8")
    print(f"Wrote class map: {map_path}")

    print("\nBackend wiring (set in backend/.env, then DEMO_MODE=false):")
    print(f"  MODEL_PATH={out.resolve()}")
    print(f"  CLASS_INDEX_MAP={map_path.resolve()}")
    print(f"  MODEL_VERSION={args.model_version}")
    print("The backend reads input size from the ONNX metadata at startup "
          "(no preprocessing code change needed) and reports it via /api/v1/health.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
