import json
from pathlib import Path
import argparse


def load_json(path: Path) -> dict:
    with open(path, 'r') as f:
        return json.load(f)


def save_json(data: dict, path: Path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def remove_session_placeholders_from_paths(paths: list) -> list:
    new_paths = []
    for path in paths:
        new_path = path.replace("[[NIPOPPY_BIDS_SESSION_ID]]/", "")
        new_path = new_path.replace("_[[NIPOPPY_BIDS_SESSION_ID]]", "")
        new_paths.append(new_path)
    return new_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Customize configuration files for a pipeline version.")
    parser.add_argument("config", type=Path, help="Path to the config.json")
    parser.add_argument("tracker", type=Path, help="Path to the tracker.json")
    parser.add_argument("version", type=str, help="Pipeline version")
    parser.add_argument("output_dir", type=Path, help="Output directory for the pipeline configuration files")
    parser.add_argument(
        "--no-sessions", action="store_true", help="Indicate that the dataset does not have sessions"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    config = load_json(args.config)
    tracker = load_json(args.tracker)

    config["VERSION"] = args.version
    if args.no_sessions:
        tracker["PATHS"] = remove_session_placeholders_from_paths(tracker["PATHS"])

    save_json(config, args.output_dir / "config.json")
    save_json(tracker, args.output_dir / "tracker.json")


if __name__ == "__main__":
    main()
