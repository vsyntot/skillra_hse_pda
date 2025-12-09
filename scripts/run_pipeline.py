from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.skillra_pda import cleaning, config, features, io  # noqa: E402


def run() -> None:
    config.ensure_directories()
    raw_path = Path(config.RAW_DATA_FILE)
    clean_path = Path(config.CLEAN_DATA_FILE)
    feature_path = Path(config.FEATURE_DATA_FILE)

    df = io.load_raw(raw_path)
    df = cleaning.parse_dates(df)
    df = cleaning.deduplicate(df)
    df = cleaning.handle_missingness(df)
    df = cleaning.salary_prepare(df)

    io.save_processed(df, clean_path)

    df_features = features.assemble_features(df.copy())
    io.save_processed(df_features, feature_path)

    print(f"Saved clean dataset to {clean_path}")
    print(f"Saved feature dataset to {feature_path}")


if __name__ == "__main__":
    run()
