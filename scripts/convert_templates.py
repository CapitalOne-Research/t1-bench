#!/usr/bin/env python
"""Convert downloaded user-policy template `.jsonl` files into the
`populated_*_user_policy_templates.json` layout that `scripts/run_simulation.py` expects.

The user-policy templates are published on the Hugging Face Hub as one `.jsonl`
file per domain / domain-combination (e.g. `liveshow.jsonl`,
`multi_2domain_liveshow_food&dining.jsonl`). Each line is a record:

    {"domain_id": "...", "domain": "...", "user_template": "...",
     "benchmark_success_criteria": "<JSON string>"}

`run_simulation.py` instead loads a JSON *array* from
`data/user_policies/data/<key>/populated_<key>_user_policy_templates.json`, whose
entries are objects that carry:
  - `user_template`               (used to drive the simulated user)
  - a 1-based integer `id`        (used by `--conversation_id -1` to enumerate runs)
  - `benchmark_success_criteria`  as an **object**, not a JSON string
    (`eval_tool_conversations.get_expected_tool_calls` indexes it as a dict:
     `entry["benchmark_success_criteria"]["exact_match"]["tool_calls"]`)

This script bridges the two, one input `.jsonl` -> one output `populated_*.json`:
  - `json.loads()` each `benchmark_success_criteria` string into an object, and
  - add a 1-based `id` to every entry (preserving record order).

Usage:
    # from the repo root, with the downloaded .jsonl files in ./output_jsonl
    python scripts/convert_templates.py --src output_jsonl

    # point at wherever you saved the download, and overwrite existing files
    python scripts/convert_templates.py --src ~/Downloads/t1-bench-final/output_jsonl --force

    # preview the mapping without writing anything
    python scripts/convert_templates.py --src output_jsonl --dry-run
"""

import argparse
import json
import os
import sys

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Input `.jsonl` filename -> destination key. The key is BOTH the folder name and
# the `populated_<key>_user_policy_templates.json` stem, so the generated path is
# `data/user_policies/data/<key>/populated_<key>_user_policy_templates.json`.
# Every value below is verified to match a `templates` path declared in
# DOMAIN_REGISTRY (scripts/run_simulation.py). Note the renames: liveshow ->
# live_show, food&dining -> food_and_dining, vehicle -> vehicle_rental,
# kayak -> kayak_rental, and the multi_* combos -> their registry combo keys.
JSONL_TO_KEY = {
    "attraction.jsonl": "attraction",
    "bar.jsonl": "bar",
    "cafe.jsonl": "cafe",
    "cruise.jsonl": "cruise",
    "dessert.jsonl": "dessert",
    "flight.jsonl": "flight",
    "food&dining.jsonl": "food_and_dining",
    "hotel.jsonl": "hotel",
    "kayak.jsonl": "kayak_rental",
    "liveshow.jsonl": "live_show",
    "vehicle.jsonl": "vehicle_rental",
    "multi_8domain.jsonl": "multi_8domain",
    "multi_11domain.jsonl": "multi_11domain",
    "multi_2domain_attraction_cafe.jsonl": "attraction_cafe",
    "multi_2domain_attraction_dessert.jsonl": "attraction_dessert",
    "multi_2domain_food&dining_hotel.jsonl": "food_and_dining_hotel",
    "multi_2domain_hotel_vehicle.jsonl": "hotel_rental",
    "multi_2domain_liveshow_food&dining.jsonl": "live_show_food_dining",
    "multi_2domain_vehicle_attraction.jsonl": "vehicle_rental_attraction",
    "multi_3domain_attraction_food&dining_cafe.jsonl": "attraction_food_dining_cafe",
    "multi_3domain_flight_hotel_bar.jsonl": "flight_hotel_bar",
    "multi_3domain_hotel_attraction_vehicle.jsonl": "hotel_attraction_rental",
    "multi_3domain_vehicle_food&dining_hotel.jsonl": "vehicle_rental_food_and_dining_hotel",
    "multi_4domain_flight_hotel_attraction_vehicle.jsonl": "flight_hotel_attraction_rental",
    "multi_4domain_hotel_vehicle_food&dining_bar.jsonl": "hotel_rental_food_bar",
}


def _dest_path(key: str) -> str:
    return os.path.join(
        _repo_root, "data", "user_policies", "data", key,
        f"populated_{key}_user_policy_templates.json",
    )


def _load_entries(src_path: str) -> list[dict]:
    """Read one `.jsonl` file into the runner's entry-list shape.

    Parses each `benchmark_success_criteria` JSON string into an object and adds a
    1-based `id` (records are kept in file order). Raises ValueError with the
    offending line number on malformed JSON so a bad download fails loudly.
    """
    entries: list[dict] = []
    with open(src_path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{os.path.basename(src_path)} line {lineno}: invalid JSON line: {e}") from e

            bss = rec.get("benchmark_success_criteria")
            if isinstance(bss, str):
                try:
                    rec["benchmark_success_criteria"] = json.loads(bss)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"{os.path.basename(src_path)} line {lineno}: "
                        f"benchmark_success_criteria is not valid JSON: {e}"
                    ) from e

            # `id` first for readability; existing keys (domain_id, domain,
            # user_template, benchmark_success_criteria) follow unchanged.
            entries.append({"id": len(entries) + 1, **rec})
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert downloaded user-policy template .jsonl files into the "
            "populated_*_user_policy_templates.json layout run_simulation.py expects."
        ),
    )
    parser.add_argument(
        "--src",
        default="output_jsonl",
        help=(
            "Directory containing the downloaded .jsonl template files "
            "(default: ./output_jsonl, relative to the repo root)."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite destination populated_*.json files that already exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report the planned conversions without writing any files.",
    )
    args = parser.parse_args()

    src_dir = args.src if os.path.isabs(args.src) else os.path.join(_repo_root, args.src)
    if not os.path.isdir(src_dir):
        print(f"ERROR: --src directory not found: {src_dir}", file=sys.stderr)
        return 1

    present = {f for f in os.listdir(src_dir) if f.endswith(".jsonl")}
    unmapped = sorted(present - set(JSONL_TO_KEY))
    missing = sorted(set(JSONL_TO_KEY) - present)

    written = skipped = 0
    for fname in sorted(JSONL_TO_KEY):
        if fname not in present:
            continue
        key = JSONL_TO_KEY[fname]
        dest = _dest_path(key)
        rel_dest = os.path.relpath(dest, _repo_root)
        try:
            entries = _load_entries(os.path.join(src_dir, fname))
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1

        if args.dry_run:
            print(f"  [dry-run] {fname:48s} -> {rel_dest}  ({len(entries)} entries)")
            continue
        if os.path.exists(dest) and not args.force:
            print(f"  [skip]    {fname:48s} -> {rel_dest}  (exists; use --force)")
            skipped += 1
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        print(f"  [write]   {fname:48s} -> {rel_dest}  ({len(entries)} entries)")
        written += 1

    for fname in missing:
        print(f"  [missing] {fname} not found in {args.src} (destination left untouched)")
    for fname in unmapped:
        print(f"  [ignore]  {fname} is not a known template file (skipped)")

    converted = (len(present & set(JSONL_TO_KEY))) if args.dry_run else written
    print(
        f"\nDone. {'would convert' if args.dry_run else 'wrote'} {converted} file(s)"
        + (f", skipped {skipped} existing" if skipped else "")
        + f". {len(missing)} mapped file(s) missing from source."
    )
    if converted == 0 and not args.dry_run and skipped == 0:
        print("Nothing converted — check that --src points at the downloaded .jsonl files.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
