from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.common import read_json, save_json, save_text
from engine.runtime import build_pipeline, configure_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay a saved raw snapshot.")
    parser.add_argument("--raw", required=True, help="Path to raw snapshot JSON.")
    return parser.parse_args()


def main(raw_path: str) -> dict:
    configure_logging(PROJECT_ROOT)
    raw_data = read_json(raw_path)
    pipeline = build_pipeline(PROJECT_ROOT, use_demo_data=True)
    features = pipeline["feature_extractor"].extract(raw_data)
    evidences = pipeline["evidence_builder"].build(features)
    decision = pipeline["decision_engine"].decide(evidences, meta={"raw_data": raw_data, "features": features})
    decision = pipeline["risk_engine"].apply(decision, raw_data, features, evidences)
    markdown = pipeline["report_renderer"].render_markdown(
        state={"symbol": raw_data["symbol"]},
        raw_data=raw_data,
        features=features,
        evidences=evidences,
        decision=decision,
    )
    replay = {"raw_data": raw_data, "features": features, "evidences": evidences, "decision": decision}
    save_json(replay, PROJECT_ROOT / "data" / "outputs" / "replay_output.json")
    save_text(markdown, PROJECT_ROOT / "data" / "outputs" / "replay_output.md")
    return replay


if __name__ == "__main__":
    args = parse_args()
    main(args.raw)
