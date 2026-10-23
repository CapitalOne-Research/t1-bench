"""
eval_tool_conversations.py

Evaluates tool-calling accuracy of simulated conversations against benchmark
success criteria. Computes precision, recall, accuracy, and F1 at both the
tool-name level and the parameter level, plus tool output exact match and a
binary pass score.

Usage:
    python scripts/eval_tool_conversations.py \\
        --benchmark path/to/populated_fast_food_user_policy_templates.json \\
        --conversations path/to/simulated_fast_food/ \\
        [--output results.json]

    # Or match a single conversation file against a specific benchmark entry:
    python scripts/eval_tool_conversations.py \\
        --benchmark path/to/populated_fast_food_user_policy_templates.json \\
        --conversations path/to/simulated_fast_food/sim_results_123.json \\
        --benchmark-index 0

Input formats
-------------
Benchmark JSON  – list of entries, each with:
    {
        "benchmark_success_criteria": {
            "exact_match": {
                "tool_calls": [
                    {"name": "tool_name", "parameters": {"param": "value", ...}},
                    ...
                ]
            },
            "llm_as_judge": {
                "metric": { ... }
            }
        }
    }

Conversation JSON (single simulation output):
    {
        "conversation_id": 1,
        "tools": [
            {"turn": 1, "step": 1, "tool_name": "search_fast_food", "parameters": {...}},
            {"turn": 1, "step": 2, "tool_name": "None",             "parameters": {}},
            ...
        ],
        "conversation": [...]
    }

Conversations directory: folder of sim_results_*.json files matched in sorted
order to benchmark entries (entry[0] -> first file, etc.).

Matching approach
-----------------
Best-match assignment: for each expected tool call, the predicted call with the
same tool name that maximises parameter recall is selected. Each predicted call
can be matched to at most one gold call (one-to-one within tool name). Parameter
values are compared with case-insensitive string normalization.

Pass
    A conversation receives pass=1 if and only if tool-level recall, parameter-level
    recall, and tool output exact match score are all 1.0.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path

from t1_plus_plus.tools.general.cache import save_to_cache, reset_cache
from eval_utils import score_params, best_match_assignment, _normalize, _is_empty_value, _EXCLUDED_PARAMS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool-log helpers
# ---------------------------------------------------------------------------

def _extract_actual_tool_calls(tool_log: list[dict]) -> list[dict]:
    """Return only the real tool calls (strip sentinel 'None' entries)."""
    return [
        entry for entry in tool_log
        if entry.get("tool_name") and entry["tool_name"] != "None"
    ]


# ---------------------------------------------------------------------------
# Tool Output Exact Match
# ---------------------------------------------------------------------------

def _strip_freeform_fields(output: str) -> str:
    """Remove volatile fields (query_summary, reason_logged) from a JSON tool output for comparison."""
    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict):
            parsed.pop("query_summary", None)
            parsed.pop("reason_logged", None)
            return json.dumps(parsed, sort_keys=True)
        return json.dumps(parsed, sort_keys=True)
    except (json.JSONDecodeError, TypeError):
        return output


def _extract_actual_tool_outputs(conversation: list[dict]) -> list[str]:
    """Extract tool output strings from the conversation's role=tool messages."""
    outputs = []
    for msg in conversation:
        if msg.get("role") == "tool":
            content = msg.get("content", "")
            if content:
                outputs.append(_strip_freeform_fields(content))
    return outputs


def evaluate_tool_output_exact_match(
    expected_tool_calls: list[dict],
    conversation: list[dict],
    tool_registry: dict,
) -> dict:
    """
    Compute Tool Output Exact Match: execute each expected (annotation) tool call
    using the tool registry, then check if its output exactly matches any of the
    actual tool outputs in the conversation.

    Returns:
        {
            "score": float,          # matches / total expected tool calls
            "matches": int,
            "total": int,
            "per_tool_detail": [...]  # per-tool breakdown
        }
    """
    actual_outputs = _extract_actual_tool_outputs(conversation)
    total = len(expected_tool_calls)
    if total == 0:
        return {"score": 0.0, "matches": 0, "total": 0, "per_tool_detail": []}

    reset_cache()
    matches = 0
    per_tool_detail = []
    search_filter_count = {}

    for entry in expected_tool_calls:
        tool_name = entry["name"]
        params = entry.get("parameters", {})

        expected_output = None
        error = None
        matched = False
        result_obj = None

        if tool_name not in tool_registry:
            error = f"tool '{tool_name}' not in registry"
        else:
            try:
                from pydantic import BaseModel
                sanitized_args = {k: v for k, v in params.items() if v is not None}
                result_obj = tool_registry[tool_name](**sanitized_args)
                if isinstance(result_obj, BaseModel):
                    expected_output = _strip_freeform_fields(result_obj.model_dump_json())
                else:
                    expected_output = _strip_freeform_fields(json.dumps(result_obj))
            except Exception as e:
                error = str(e)

        # Auto-save search/filter results to cache for subsequent tool calls
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

        _MESSAGE_EMBED_TOOLS = {"cancel_kayak_reservation", "cancel_sport_event_tickets"}

        if expected_output is not None:
            def _normalize(s):
                try:
                    d = json.loads(s)
                    if isinstance(d, dict) and tool_name in _MESSAGE_EMBED_TOOLS:
                        d.pop("message", None)
                        return json.dumps(d, sort_keys=True)
                except (json.JSONDecodeError, TypeError):
                    pass
                return s

            for actual_output in actual_outputs:
                if _normalize(actual_output) == _normalize(expected_output):
                    matched = True
                    break

        if matched:
            matches += 1

        per_tool_detail.append({
            "tool_name": tool_name,
            "parameters": params,
            "expected_output": expected_output,
            "matched": matched,
            "error": error,
        })

    score = matches / total if total > 0 else 0.0

    return {
        "score": round(score, 4),
        "matches": matches,
        "total": total,
        "per_tool_detail": per_tool_detail,
    }


# ---------------------------------------------------------------------------
# Core conversation evaluation
# ---------------------------------------------------------------------------

def evaluate_single_conversation(
    expected_tool_calls: list[dict],
    actual_tool_log: list[dict],
) -> dict:
    """
    Compare one conversation's tool log against its expected tool calls using
    best-match assignment: each gold call is paired with the predicted call of
    the same tool name that maximises parameter recall; each predicted call can
    be matched to at most one gold call.

    Returns a dict with tool_level P/R/F1, parameter_level P/R/F1, and per_tool_detail.
    """
    actual_calls = _extract_actual_tool_calls(actual_tool_log)
    actual_tool_names = [c["tool_name"] for c in actual_calls]

    # Tool-level counts (multiset semantics)
    expected_counts = Counter(entry["name"] for entry in expected_tool_calls)
    predicted_counts = Counter(actual_tool_names)

    tp_count = sum((expected_counts & predicted_counts).values())
    n_predicted_total = sum(predicted_counts.values())
    n_expected_total = sum(expected_counts.values())

    tool_precision = tp_count / n_predicted_total if n_predicted_total else 0.0
    tool_recall = tp_count / n_expected_total if n_expected_total else 0.0
    tool_f1 = (
        2 * tool_precision * tool_recall / (tool_precision + tool_recall)
        if (tool_precision + tool_recall) > 0
        else 0.0
    )

    expected_names = set(expected_counts)
    predicted_names = set(predicted_counts)
    tp_names = expected_names & predicted_names
    fp_names = predicted_names - expected_names
    fn_names = expected_names - predicted_names

    # Best-match assignment: one predicted call per gold call
    assignments = best_match_assignment(expected_tool_calls, actual_calls)

    per_tool_results: dict[str, dict] = {}
    total_expected_params = 0
    total_matched_params = 0
    total_predicted_params = 0

    for entry_idx, (entry, matched_call) in enumerate(zip(expected_tool_calls, assignments)):
        tool_name = entry["name"]
        expected_params = entry.get("parameters", {})

        result_key = f"{tool_name}_{entry_idx}" if tool_name in per_tool_results else tool_name

        if matched_call is None:
            scoreable_params = [p for p in expected_params if p not in _EXCLUDED_PARAMS]
            per_tool_results[result_key] = {
                "tool_called": False,
                "param_precision": 0.0,
                "param_recall": 0.0,
                "param_f1": 0.0,
                "all_params_matched": False,
                "expected_params": scoreable_params,
                "matched_params": [],
                "missing_params": scoreable_params,
                "extra_params": [],
            }
            total_expected_params += len(scoreable_params)
            continue

        actual_params = matched_call.get("parameters", {})
        n_matched, n_expected, n_predicted, matched, missing, extra = score_params(
            expected_params, actual_params
        )

        precision = n_matched / n_predicted if n_predicted > 0 else 0.0
        recall = n_matched / n_expected if n_expected > 0 else 1.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        domain_matched = None

        tool_entry = {
            "tool_called": True,
            "param_precision": round(precision, 4),
            "param_recall": round(recall, 4),
            "param_f1": round(f1, 4),
            "all_params_matched": len(missing) == 0,
            "n_predicted": n_predicted,
            "expected_params": [p for p in expected_params if p not in _EXCLUDED_PARAMS],
            "matched_params": matched,
            "missing_params": missing,
            "extra_params": extra,
        }
        per_tool_results[result_key] = tool_entry

        total_expected_params += n_expected
        total_matched_params += n_matched
        total_predicted_params += n_predicted

    agg_param_precision = (
        total_matched_params / total_predicted_params if total_predicted_params > 0 else 0.0
    )
    agg_param_recall = (
        total_matched_params / total_expected_params if total_expected_params > 0 else 0.0
    )
    agg_param_f1 = (
        2 * agg_param_precision * agg_param_recall / (agg_param_precision + agg_param_recall)
        if (agg_param_precision + agg_param_recall) > 0
        else 0.0
    )

    tools_fully_matched = [
        t for t, d in per_tool_results.items()
        if d["tool_called"] and d["all_params_matched"]
    ]

    tool_accuracy = 1.0 if [e["name"] for e in expected_tool_calls] == [c["tool_name"] for c in _extract_actual_tool_calls(actual_tool_log)] else 0.0

    n_expected_tools = len(expected_tool_calls)
    param_accuracy = (
        round(len(tools_fully_matched) / n_expected_tools, 4)
        if n_expected_tools > 0 else 0.0
    )

    result = {
        "tool_level": {
            "precision": round(tool_precision, 4),
            "recall": round(tool_recall, 4),
            "f1": round(tool_f1, 4),
            "accuracy": tool_accuracy,
            "expected_tools": sorted(expected_names),
            "predicted_tools": sorted(predicted_names),
            "true_positives": sorted(tp_names),
            "false_positives": sorted(fp_names),
            "false_negatives": sorted(fn_names),
        },
        "parameter_level": {
            "precision": round(agg_param_precision, 4),
            "recall": round(agg_param_recall, 4),
            "f1": round(agg_param_f1, 4),
            "accuracy": param_accuracy,
        },
        "tools_fully_matched": tools_fully_matched,
        "per_tool_detail": per_tool_results,
    }
    return result


def compute_pass(exact_match_result: dict, tool_output_result: dict) -> int:
    """Return 1 if tool recall, parameter recall, and tool output score are all 1.0."""
    return 1 if (
        exact_match_result["tool_level"]["recall"] == 1.0
        and exact_match_result["parameter_level"]["recall"] == 1.0
        and tool_output_result.get("score", 0.0) == 1.0
    ) else 0


# ---------------------------------------------------------------------------
# Aggregate across multiple conversations
# ---------------------------------------------------------------------------

def aggregate_metrics(results: list[dict]) -> dict:
    """Compute macro-average P/R/F1 across all evaluated conversations."""
    if not results:
        return {}

    n = len(results)

    def _avg(key_path: list[str]) -> float:
        vals = []
        for r in results:
            node = r
            for k in key_path:
                node = node.get(k, {})
            if isinstance(node, (int, float)):
                vals.append(node)
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    return {
        "num_conversations": n,
        "tool_level": {
            "avg_precision": _avg(["tool_level", "precision"]),
            "avg_recall": _avg(["tool_level", "recall"]),
            "avg_f1": _avg(["tool_level", "f1"]),
        },
        "parameter_level": {
            "avg_precision": _avg(["parameter_level", "precision"]),
            "avg_recall": _avg(["parameter_level", "recall"]),
            "avg_f1": _avg(["parameter_level", "f1"]),
        },
    }


# ---------------------------------------------------------------------------
# File loading helpers
# ---------------------------------------------------------------------------

def load_benchmark(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Benchmark file must be a JSON array, got {type(data)}")
    return data


def load_conversation(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_conversations_dir(directory: str) -> tuple[list[dict], list[str]]:
    """Load all sim_results_*.json files from a directory, sorted by filename."""
    dir_path = Path(directory)
    files = sorted(dir_path.glob("sim_results_*.json"))
    if not files:
        files = sorted(dir_path.glob("*.json"))
    return [load_conversation(str(f)) for f in files], [str(f) for f in files]


def get_expected_tool_calls(benchmark_entry: dict) -> list[dict]:
    """Extract the exact_match tool_calls list from a benchmark entry."""
    try:
        raw = benchmark_entry["benchmark_success_criteria"]["exact_match"]["tool_calls"]
    except KeyError:
        return []
    # Normalize dict-keyed format {"tool_name": {"parameters": {...}}, ...}
    # into the standard list format [{"name": "tool_name", "parameters": {...}}, ...]
    if isinstance(raw, dict):
        return [{"name": name, **entry} for name, entry in raw.items()]
    return raw


def get_llm_judge_metrics(benchmark_entry: dict) -> dict:
    """Extract the llm_as_judge metric descriptions from a benchmark entry."""
    try:
        return benchmark_entry["benchmark_success_criteria"]["llm_as_judge"]["metric"]
    except KeyError:
        return {}


def get_actual_tool_log(conversation: dict) -> list[dict]:
    """Extract tools log from a conversation record."""
    tools = conversation.get("tools", conversation.get("csv_ready_tool_log", []))
    # New format: tools is a dict with gold/predicted keys
    if isinstance(tools, dict):
        return tools.get("predicted", [])
    return tools


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------

def _print_summary(
    aggregate: dict,
    per_conv_results: list[dict],
    filenames: list[str],
    judge_metrics: list[dict] | None = None,
) -> None:
    SEP = "=" * 65

    print("\n" + SEP)
    print("  TOOL CALLING EVALUATION RESULTS")
    print(SEP)

    n = aggregate["num_conversations"]
    print(f"\nConversations evaluated : {n}")

    # ---- Fine-grained ----
    print("\n--- Tool-Name Level  (macro avg) ---")
    tl = aggregate["tool_level"]
    print(f"  Precision : {tl['avg_precision']:.4f}")
    print(f"  Recall    : {tl['avg_recall']:.4f}")
    print(f"  F1        : {tl['avg_f1']:.4f}")

    print("\n--- Parameter Level  (macro avg) ---")
    pl = aggregate["parameter_level"]
    print(f"  Precision : {pl['avg_precision']:.4f}")
    print(f"  Recall    : {pl['avg_recall']:.4f}")
    print(f"  F1        : {pl['avg_f1']:.4f}")

    # ---- Per-conversation breakdown ----
    print("\n--- Per-Conversation Breakdown ---")
    for i, (res, fname) in enumerate(zip(per_conv_results, filenames)):
        label = Path(fname).name if fname else f"conv_{i}"
        tl = res["tool_level"]
        pl = res["parameter_level"]

        print(
            f"  [{label}]  "
            f"tool F1={tl['f1']:.3f}  param F1={pl['f1']:.3f}"
        )
        print(
            f"    expected={tl['expected_tools']}"
        )
        if tl["false_negatives"]:
            print(f"    missed tools        : {tl['false_negatives']}")
        if tl["false_positives"]:
            print(f"    unexpected tools    : {tl['false_positives']}")
        if res["tools_fully_matched"]:
            print(f"    fully matched tools : {res['tools_fully_matched']}")

        for tool_name, detail in res["per_tool_detail"].items():
            if not detail["tool_called"]:
                print(f"    [{tool_name}] NOT CALLED")
                continue
            status = "OK" if detail["all_params_matched"] else "PARTIAL"
            print(f"    [{tool_name}] {status}  param F1={detail['param_f1']:.3f}")
            if detail.get("missing_params"):
                print(f"      missing params : {detail['missing_params']}")
            if detail.get("extra_params"):
                print(f"      extra   params : {detail['extra_params']}")

        # Optionally show the llm_as_judge targets for this conversation
        if judge_metrics and i < len(judge_metrics):
            jm = judge_metrics[i]
            if jm:
                print(
                    f"    llm_as_judge targets: "
                    f"SR={str(jm.get('Success Rate','?'))[:40]}  "
                    f"GR={str(jm.get('Goal Rate','?'))[:40]}"
                )

    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate tool-calling accuracy of simulated conversations against "
            "benchmark success criteria, computing Goal Rate, Success Rate, "
            "and parameter-level P/R/F1."
        )
    )
    parser.add_argument(
        "--benchmark",
        required=True,
        help=(
            "Path to the benchmark JSON file "
            "(e.g. populated_fast_food_user_policy_templates.json)."
        ),
    )
    parser.add_argument(
        "--conversations",
        required=True,
        help=(
            "Path to a simulated conversation JSON file OR a directory of "
            "sim_results_*.json files. Files in a directory are matched to "
            "benchmark entries in sorted order."
        ),
    )
    parser.add_argument(
        "--benchmark-index",
        type=int,
        default=None,
        help=(
            "If --conversations points to a single file, use this benchmark "
            "entry index (0-based). Defaults to 0."
        ),
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write the full results as JSON.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help=(
            "Emit DEBUG-level logs to stderr showing per-tool and per-param "
            "evaluation decisions (tool presence, value matching, placeholder "
            "handling, prior_results contract checks)."
        ),
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(message)s",
        stream=sys.stderr,
    )

    benchmark = load_benchmark(args.benchmark)

    conv_path = Path(args.conversations)
    if conv_path.is_dir():
        conversations, filenames = load_conversations_dir(str(conv_path))
    elif conv_path.is_file():
        conversations = [load_conversation(str(conv_path))]
        filenames = [str(conv_path)]
    else:
        print(f"Error: --conversations path not found: {conv_path}", file=sys.stderr)
        sys.exit(1)

    if not conversations:
        print("Error: no conversation files found.", file=sys.stderr)
        sys.exit(1)

    # Pair conversations with benchmark entries
    if args.benchmark_index is not None:
        if args.benchmark_index >= len(benchmark):
            print(
                f"Error: --benchmark-index {args.benchmark_index} out of range "
                f"(benchmark has {len(benchmark)} entries).",
                file=sys.stderr,
            )
            sys.exit(1)
        pairs = [(benchmark[args.benchmark_index], conversations[0], filenames[0])]
    else:
        if len(conversations) != len(benchmark):
            print(
                f"Warning: {len(conversations)} conversation file(s) but "
                f"{len(benchmark)} benchmark entries. Pairing by index up to "
                f"min({len(conversations)}, {len(benchmark)}).",
                file=sys.stderr,
            )
        pairs = [
            (benchmark[i], conversations[i], filenames[i])
            for i in range(min(len(conversations), len(benchmark)))
        ]

    per_conv_results = []
    paired_filenames = []
    judge_metrics_list = []
    full_output = []

    for bench_entry, conversation, fname in pairs:
        expected = get_expected_tool_calls(bench_entry)
        actual_log = get_actual_tool_log(conversation)

        if not expected:
            print(
                f"Warning: no exact_match tool_calls in benchmark entry for "
                f"journey '{bench_entry.get('journey_id', '?')}'. Skipping.",
                file=sys.stderr,
            )
            continue

        result = evaluate_single_conversation(expected, actual_log)
        per_conv_results.append(result)
        paired_filenames.append(fname)
        judge_metrics_list.append(get_llm_judge_metrics(bench_entry))

        full_output.append(
            {
                "file": fname,
                "journey_id": bench_entry.get("journey_id", "unknown"),
                "llm_as_judge_targets": get_llm_judge_metrics(bench_entry),
                "metrics": result,
            }
        )

    if not per_conv_results:
        print("No valid pairs to evaluate.", file=sys.stderr)
        sys.exit(1)

    aggregate = aggregate_metrics(per_conv_results)
    _print_summary(aggregate, per_conv_results, paired_filenames, judge_metrics_list)

    output_data = {"aggregate": aggregate, "conversations": full_output}
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Full results written to: {args.output}")
    else:
        print(json.dumps(output_data, indent=2))


if __name__ == "__main__":
    main()
