"""
download_dataset.py

Download the T1-Bench data files from the Hugging Face Hub into the local
`datasets/` folder, where all tool implementations under `src/t1_plus_plus/`
expect to find them (e.g. `datasets/data_attractions.csv`, `datasets/data_hotel.csv`).

Usage:
    python scripts/download_dataset.py

    # Override the default repo or target folder
    python scripts/download_dataset.py --repo-id capitalone/t1-bench --out-dir datasets

    # Re-download even if datasets/ already exists
    python scripts/download_dataset.py --force
"""

import argparse
import os
import sys

_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DEFAULT_REPO_ID = "capitalone/t1-bench"
DEFAULT_OUT_DIR = os.path.join(_repo_root, "datasets")


def main():
    parser = argparse.ArgumentParser(
        description="Download the T1-Bench dataset files from the Hugging Face Hub.",
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        default=DEFAULT_REPO_ID,
        help=f"Hugging Face dataset repo ID (default: {DEFAULT_REPO_ID}).",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default=None,
        help="Specific revision (branch, tag, or commit hash) to download (default: latest).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=DEFAULT_OUT_DIR,
        help=f"Directory to download files into (default: {DEFAULT_OUT_DIR}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if --out-dir already exists and is non-empty.",
    )
    args = parser.parse_args()

    if (
        os.path.isdir(args.out_dir)
        and os.listdir(args.out_dir)
        and not args.force
    ):
        print(f"{args.out_dir} already exists and is non-empty. Use --force to re-download.")
        sys.exit(0)

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print(
            "huggingface_hub is required to download the dataset.\n"
            "Install it with: uv pip install huggingface_hub",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Downloading {args.repo_id} to {args.out_dir} ...")
    snapshot_download(
        repo_id=args.repo_id,
        repo_type="dataset",
        revision=args.revision,
        local_dir=args.out_dir,
    )
    print("Done.")


if __name__ == "__main__":
    main()
