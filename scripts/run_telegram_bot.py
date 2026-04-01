from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.push.telegram_bot_v3 import build_telegram_runtime


def main() -> None:
    runner = build_telegram_runtime(PROJECT_ROOT)
    runner.run_forever()


if __name__ == "__main__":
    main()
