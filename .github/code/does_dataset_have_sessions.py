from pathlib import Path
import sys
import argparse


def does_dataset_have_sessions(dataset_id: str, bids_path: Path):
    """
    Exit with code 0 if any sessions exist, 1 if no sessions are found, 
    and 3 if some subjects have sessions and others do not.
    """
    subjects_with_sessions = []
    subjects_without_sessions = []
    for sub_dir in bids_path.glob('sub-*'):
        if sub_dir.is_dir():
            sub_has_any_ses = any(ses_dir.is_dir() for ses_dir in sub_dir.glob('ses-*'))
            if sub_has_any_ses:
                subjects_with_sessions.append(sub_dir.name)
            else:
                subjects_without_sessions.append(sub_dir.name)

    if subjects_with_sessions and subjects_without_sessions:
        print(
            f"{dataset_id}: WARNING Dataset has a session layer but "
            f"{len(subjects_without_sessions)} subject(s) lack session subdirectories: "
            f"{subjects_without_sessions}"
        )
        # Exit code 2 might be thrown by command line parsing errors,
        # so we use a distinct code that's unlikely to collide with other codes
        sys.exit(3)

    if subjects_with_sessions:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if any sessions exist in a BIDS dataset.")
    parser.add_argument("dataset_id", type=str, help="Dataset ID")
    parser.add_argument("bids_path", type=Path, help="Path to the BIDS dataset")
    args = parser.parse_args()
    does_dataset_have_sessions(args.dataset_id, args.bids_path)
