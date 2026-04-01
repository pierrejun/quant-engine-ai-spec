from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.common import build_job_id, init_state, save_json, save_text, touch_state
from engine.runtime import build_pipeline_for_market, configure_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run single-symbol quant analysis.")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--market", default="US")
    parser.add_argument("--as-of", dest="as_of", default=date.today().isoformat())
    parser.add_argument("--demo", action="store_true", help="Use deterministic demo providers.")
    return parser.parse_args()


def main(symbol: str, market: str, as_of: str, use_demo_data: bool = False) -> dict:
    configure_logging(PROJECT_ROOT)
    pipeline = build_pipeline_for_market(PROJECT_ROOT, market=market, use_demo_data=use_demo_data)
    runtime_config = pipeline["runtime_config"]["defaults"]
    job_id = build_job_id(symbol, market, as_of, run_tag="demo" if use_demo_data else "live")
    state = init_state(job_id, symbol, market, as_of)

    snapshot_dir = PROJECT_ROOT / runtime_config["snapshot_dir"]
    output_dir = PROJECT_ROOT / runtime_config["output_dir"]
    log_dir = PROJECT_ROOT / runtime_config["log_dir"]

    state.artifacts.raw_snapshot_path = str(snapshot_dir / f"{job_id}_raw.json")
    state.artifacts.features_path = str(snapshot_dir / f"{job_id}_features.json")
    state.artifacts.evidence_path = str(snapshot_dir / f"{job_id}_evidence.json")
    state.artifacts.decision_path = str(snapshot_dir / f"{job_id}_decision.json")
    state.artifacts.report_path = str(output_dir / f"{job_id}.md")
    state.artifacts.detail_report_path = str(output_dir / f"{job_id}_detail.md")
    state.artifacts.final_json_path = str(output_dir / f"{job_id}.json")

    raw_data = pipeline["collector"].collect(symbol=symbol, market=market, as_of=as_of)
    state.data_quality = raw_data["collection_status"]
    save_json(raw_data, state.artifacts.raw_snapshot_path)

    touch_state(state, stage="feature_extraction")
    features = pipeline["feature_extractor"].extract(raw_data)
    save_json(features, state.artifacts.features_path)

    touch_state(state, stage="building_evidence")
    evidences = pipeline["evidence_builder"].build(features)
    save_json(evidences, state.artifacts.evidence_path)

    touch_state(state, stage="decisioning")
    decision = pipeline["decision_engine"].decide(evidences, meta={"raw_data": raw_data, "features": features})

    touch_state(state, stage="risk_adjustment")
    decision = pipeline["risk_engine"].apply(decision, raw_data, features, evidences)
    save_json(decision, state.artifacts.decision_path)

    touch_state(state, stage="rendering_report")
    markdown = pipeline["report_renderer"].render_markdown(
        state=state.model_dump(),
        raw_data=raw_data,
        features=features,
        evidences=evidences,
        decision=decision,
    )
    detail_markdown = pipeline["report_renderer"].render_detail_markdown(
        state=state.model_dump(),
        raw_data=raw_data,
        features=features,
        evidences=evidences,
        decision=decision,
    )

    final_output = {
        "job_id": job_id,
        "state": state.model_dump(),
        "raw_data": raw_data,
        "features": features,
        "evidences": evidences,
        "decision": decision,
    }
    save_json(final_output, state.artifacts.final_json_path)
    save_text(markdown, state.artifacts.report_path)
    save_text(detail_markdown, state.artifacts.detail_report_path)

    touch_state(state, stage="done", status="completed")
    final_output["state"] = state.model_dump()
    save_json(final_output, state.artifacts.final_json_path)
    save_text(
        "\n".join(
            [
                f"job_id={job_id}",
                f"symbol={symbol}",
                f"market={market}",
                f"as_of={as_of}",
                f"status={state.status}",
                f"stage={state.stage}",
                f"data_quality={state.data_quality}",
                f"action={decision['action']}",
                f"confidence={decision['confidence']}",
                f"risk_flags={decision['risk_flags']}",
            ]
        ),
        log_dir / f"{job_id}.log",
    )
    return final_output


if __name__ == "__main__":
    args = parse_args()
    main(args.symbol.upper(), args.market.upper(), args.as_of, use_demo_data=args.demo)
