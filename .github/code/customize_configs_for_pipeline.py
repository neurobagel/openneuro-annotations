import json
from pathlib import Path
import argparse


def load_json(path: Path) -> dict:
    with open(path, 'r') as f:
        return json.load(f)


def save_json(data: dict, path: Path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def remove_session_placeholders_from_tracker(tracker: dict) -> dict:
    tracker["PATHS"] = [
        path.replace("[[NIPOPPY_BIDS_SESSION_ID]]/", "").replace("_[[NIPOPPY_BIDS_SESSION_ID]]", "") 
        for path in tracker["PATHS"]
    ]
    if tracker.get("PARTICIPANT_SESSION_DIR"):
        tracker["PARTICIPANT_SESSION_DIR"] = tracker["PARTICIPANT_SESSION_DIR"].replace(
            "/[[NIPOPPY_BIDS_SESSION_ID]]/", ""
        ).replace("[[NIPOPPY_BIDS_SESSION_ID]]/", "")  # Some Freesurfer trackers have session ID first

    return tracker


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
        tracker = remove_session_placeholders_from_tracker(tracker)

    save_json(config, args.output_dir / "config.json")
    save_json(tracker, args.output_dir / "tracker.json")


if __name__ == "__main__":
    main()
