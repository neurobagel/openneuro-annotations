import json
from pathlib import Path
import argparse


EXAMPLE_CONFIG={
    "NAME": "fmriprep",
    "VERSION": "",
    "STEPS": [
        {
            "TRACKER_CONFIG_FILE": "tracker.json"
        }
    ],
    "PIPELINE_TYPE": "processing",
    "SCHEMA_VERSION": 1
}

EXAMPLE_TRACKER={
    "PATHS": [
        "[[NIPOPPY_BIDS_PARTICIPANT_ID]]/[[NIPOPPY_BIDS_SESSION_ID]]/anat/[[NIPOPPY_BIDS_PARTICIPANT_ID]]_[[NIPOPPY_BIDS_SESSION_ID]]*_T1w.json",
        "[[NIPOPPY_BIDS_PARTICIPANT_ID]]_[[NIPOPPY_BIDS_SESSION_ID]]*_T1w.html"
    ]
}


def load_json(path: Path) -> dict:
    with open(path, 'r') as f:
        return json.load(f)


def remove_session_placeholders(tracker: dict) -> dict:
    new_paths = []
    for path in tracker["PATHS"]:
        new_path = path.replace("[[NIPOPPY_BIDS_SESSION_ID]]/", "")
        new_path = new_path.replace("_[[NIPOPPY_BIDS_SESSION_ID]]", "")
        new_paths.append(new_path)
    tracker["PATHS"] = new_paths
    return tracker


def main(config: dict, tracker: dict, version: str, dataset_has_sessions: bool):
    parser = argparse.ArgumentParser(description="Customize pipeline configurations")
    parser.add_argument("config", type=str, help="Path to the config file")
    parser.add_argument("tracker", type=str, help="Path to the tracker file")
    parser.add_argument("version", type=str, help="Pipeline version")
    parser.add_argument(
        "dataset_has_sessions", action="store_true", help="Whether the dataset has sessions. One of true, false"
    )
    args = parser.parse_args()

    config["VERSION"] = args.version

    if not args.dataset_has_sessions:
        tracker = remove_session_placeholders(tracker)
