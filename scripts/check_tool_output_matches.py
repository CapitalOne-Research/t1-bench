"""
check_tool_output_matches.py

For each scenario in a populated template, execute all gold tool calls and check
if any pair of outputs match each other (ignoring query_summary).

Usage:
    python scripts/check_tool_output_matches.py \
        --templates data/user_policies/data/live_show/populated_live_show_user_policy_templates.json

    python scripts/check_tool_output_matches.py \
        --templates data/user_policies/data/food_and_dining/populated_food_and_dining_user_policy_templates.json \
        --domain food_and_dining

    # Single scenario:
    python scripts/check_tool_output_matches.py \
        --templates data/user_policies/data/live_show/populated_live_show_user_policy_templates.json \
        --index 3
"""

import argparse
import contextlib
import io
import json
import os
import sys

_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
sys.path.insert(0, os.path.join(_repo_root, "src"))

from scripts.run_simulation import DOMAIN_REGISTRY, build_tool_registry, build_combined_domain_cfg
from scripts.eval_tool_conversations import get_expected_tool_calls
from t1_plus_plus.tools.general.cache import save_to_cache, reset_cache
from pydantic import BaseModel


def _strip_query_summary(output: str) -> str:
    """Remove query_summary from JSON output for comparison."""
    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict) and "query_summary" in parsed:
            parsed.pop("query_summary")
            return json.dumps(parsed, sort_keys=True)
        return json.dumps(parsed, sort_keys=True)
    except (json.JSONDecodeError, TypeError):
        return output


def _execute_tool(tool_name, params, tool_registry):
    """Execute a tool and return (raw_result_obj, stripped_output_str, error)."""
    if tool_name not in tool_registry:
        return None, None, f"tool '{tool_name}' not in registry"

    try:
        sanitized_args = {k: v for k, v in params.items() if v is not None}
        result_obj = tool_registry[tool_name](**sanitized_args)
        if isinstance(result_obj, BaseModel):
            raw = result_obj.model_dump_json()
        else:
            raw = json.dumps(result_obj)
        return result_obj, _strip_query_summary(raw), None
    except Exception as e:
        return None, None, str(e)


def validate_scenario(scenario_idx, entry, tool_registry):
    """Run all gold tool calls for a scenario and find pairwise output matches."""
    reset_cache()

    expected_tool_calls = get_expected_tool_calls(entry)
    if not expected_tool_calls:
        return None

    journey_id = entry.get("journey_id", f"scenario_{scenario_idx}")

    # Execute each tool call sequentially, auto-caching search/filter results
    # Suppress print output from tool internals
    outputs = []
    search_filter_count = {}

    for tc in expected_tool_calls:
        tool_name = tc["name"]
        params = tc.get("parameters", {})

        with contextlib.redirect_stdout(io.StringIO()):
            result_obj, stripped_output, error = _execute_tool(tool_name, params, tool_registry)

            # Auto-save to cache for search/filter tools so subsequent filters can use them
            if result_obj is not None and (tool_name.startswith("search_") or tool_name.startswith("filter_")):
                base_key = f"{tool_name}_results"
                idx = search_filter_count.get(base_key, 0)
                search_filter_count[base_key] = idx + 1
                cache_key = f"{base_key}_{idx}"
                try:
                    summary = getattr(result_obj, "query_summary", None)
                    save_to_cache(key=cache_key, value=result_obj, summary=summary)
                except Exception:
                    pass

        outputs.append({
            "tool_name": tool_name,
            "parameters": params,
            "output": stripped_output,
            "error": error,
        })

    # Pairwise comparison — find which tool calls produced identical outputs
    matches = []
    for i in range(len(outputs)):
        for j in range(i + 1, len(outputs)):
            if outputs[i]["output"] is None or outputs[j]["output"] is None:
                continue
            if outputs[i]["output"] == outputs[j]["output"]:
                matches.append((i, j))

    return {
        "scenario_idx": scenario_idx,
        "journey_id": journey_id,
        "tool_calls": [
            {"index": i, "tool_name": o["tool_name"], "parameters": o["parameters"], "error": o["error"]}
            for i, o in enumerate(outputs)
        ],
        "pairwise_matches": [
            {
                "tool_a": f"[{i}] {outputs[i]['tool_name']}",
                "tool_b": f"[{j}] {outputs[j]['tool_name']}",
            }
            for i, j in matches
        ],
        "num_matches": len(matches),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Check pairwise tool output matches within each scenario.",
    )
    parser.add_argument(
        "--templates",
        required=True,
        help="Path to the populated templates JSON file.",
    )
    parser.add_argument(
        "--domain",
        nargs="+",
        type=str,
        required=True,
        help="Domain(s) to load tools from (e.g. live_show food_and_dining).",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=None,
        help="Run only a single scenario by 0-based index.",
    )
    args = parser.parse_args()

    # Resolve domain(s)
    domains = args.domain
    for d in domains:
        if d not in DOMAIN_REGISTRY:
            print(f"ERROR: Unknown domain '{d}'. Available: {', '.join(DOMAIN_REGISTRY.keys())}")
            sys.exit(1)

    # Load tools (merge from all domains)
    print(f"[Domains] {domains}")
    if len(domains) == 1:
        domain_cfg = DOMAIN_REGISTRY[domains[0]]
    else:
        domain_cfg = build_combined_domain_cfg(domains, templates_override=args.templates)
    tool_registry = build_tool_registry(domain_cfg)
    print(f"[Tools]   {list(tool_registry.keys())}")

    # Load templates
    templates_path = args.templates
    if not os.path.isabs(templates_path):
        templates_path = os.path.join(_repo_root, templates_path)
    with open(templates_path, "r", encoding="utf-8") as f:
        templates = json.load(f)
    print(f"[Templates] {len(templates)} scenarios loaded")

    # Run validation
    if args.index is not None:
        entries = [(args.index, templates[args.index])]
    else:
        entries = list(enumerate(templates))

    total_scenarios = 0
    scenarios_with_matches = 0
    all_results = []

    print(f"\n{'='*70}")

    for idx, entry in entries:
        result = validate_scenario(idx, entry, tool_registry)
        if result is None:
            continue

        total_scenarios += 1
        all_results.append(result)

        has_matches = result["num_matches"] > 0
        if has_matches:
            scenarios_with_matches += 1
            match_strs = [
                f"{m['tool_a']} == {m['tool_b']}"
                for m in result["pairwise_matches"]
            ]
            print(f"  Scenario {idx:>3}  |  {'; '.join(match_strs)}")

        for tc in result["tool_calls"]:
            if tc["error"]:
                print(f"  Scenario {idx:>3}  |  ERROR [{tc['tool_name']}]: {tc['error']}")

    # Summary
    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"  Total scenarios              : {total_scenarios}")
    print(f"  Scenarios with output matches: {scenarios_with_matches}")
    if total_scenarios:
        print(f"  Match rate                   : {scenarios_with_matches}/{total_scenarios} ({scenarios_with_matches/total_scenarios:.0%})")
    print()


if __name__ == "__main__":
    main()
