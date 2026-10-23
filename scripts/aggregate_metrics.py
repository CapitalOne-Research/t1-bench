"""
Aggregate metrics across all conversations in a run directory.

Supports three modes:
  1. Model-level: point at a model folder to get per-domain + overall averages.
  2. Domain-level / multi-run: point at a domain folder with multiple run_*
     subdirectories. Computes per-run aggregates, then mean ± std dev across runs.
  3. Single run: point at a folder with metrics_*.json files directly.

Usage:
    # Model-level: per-domain summaries + overall across all domains
    python scripts/aggregate_metrics.py simulated_conversation/claude_code_claude-4.6-opus
    python scripts/aggregate_metrics.py simulated_conversation/openai/gpt-oss-120b

    # Domain-level with k repetitions: mean ± std dev across runs
    python scripts/aggregate_metrics.py simulated_conversation/claude_code_claude-4.6-opus/food_and_dining
    python scripts/aggregate_metrics.py simulated_conversation/openai/gpt-oss-120b/live_show

    # Single run
    python scripts/aggregate_metrics.py simulated_conversation/claude_code_claude-4.6-opus/food_and_dining/run_20260522_120000
    python scripts/aggregate_metrics.py simulated_conversation/openai/gpt-oss-120b/bar/run_20260522_130000

    # With options
    python scripts/aggregate_metrics.py simulated_conversation/claude_code_claude-4.6-opus --failures
    python scripts/aggregate_metrics.py simulated_conversation/claude_code_claude-4.6-opus --output results.json
"""

import argparse
import json
import math
import os
import sys
from collections import defaultdict

_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_results_dir = os.path.join(_repo_root, "results")


def _save_result(subpath: str, data, is_text=False):
    """Save data to results/<subpath>. Creates directories as needed."""
    path = os.path.join(_results_dir, subpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if is_text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    print(f"  Saved: results/{subpath}")


def find_metrics_files(run_dir: str) -> list[str]:
    results = []
    for root, dirs, files in os.walk(run_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.startswith("metrics_") and f.endswith(".json"):
                results.append(os.path.join(root, f))
    return sorted(results)


def find_run_subdirs(domain_dir: str) -> list[str]:
    """Find run_* subdirectories that contain metrics files."""
    subdirs = []
    for entry in sorted(os.listdir(domain_dir)):
        full = os.path.join(domain_dir, entry)
        if os.path.isdir(full) and entry.startswith("run_"):
            if find_metrics_files(full):
                subdirs.append(full)
    return subdirs


def find_domain_subdirs(model_dir: str) -> list[str]:
    """Find domain subdirectories (non-run_* dirs that contain metrics files somewhere)."""
    subdirs = []
    for entry in sorted(os.listdir(model_dir)):
        full = os.path.join(model_dir, entry)
        if os.path.isdir(full) and not entry.startswith("."):
            if find_metrics_files(full):
                subdirs.append(full)
    return subdirs


def find_model_dirs(top_dir: str) -> list[tuple[str, str]]:
    """Discover model directories under a top-level dir.

    Handles both flat (claude_code_claude-4.6-opus/) and nested (openai/gpt-oss-120b/)
    structures. Returns list of (display_name, path) tuples.
    """
    results = []
    for entry in sorted(os.listdir(top_dir)):
        entry_path = os.path.join(top_dir, entry)
        if not os.path.isdir(entry_path) or entry.startswith("."):
            continue
        # Check if this dir directly contains domain/run dirs with metrics
        if find_metrics_files(entry_path):
            # Check if it has domain-like subdirs (meaning it IS a model dir)
            subdirs = [
                e for e in os.listdir(entry_path)
                if os.path.isdir(os.path.join(entry_path, e))
                and not e.startswith(".")
                and (e.startswith("run_") or find_metrics_files(os.path.join(entry_path, e)))
            ]
            if subdirs:
                # Could be a model dir OR a provider dir (like "openai/")
                # Check if subdirs look like model names (have their own domain dirs)
                is_provider = False
                for sub in subdirs:
                    sub_path = os.path.join(entry_path, sub)
                    if not sub.startswith("run_") and os.path.isdir(sub_path):
                        # Check if this subdir has non-run_* subdirs with metrics
                        # (i.e. it looks like a model with domain dirs underneath)
                        sub_subdirs = [
                            e2 for e2 in os.listdir(sub_path)
                            if os.path.isdir(os.path.join(sub_path, e2))
                            and not e2.startswith(".")
                            and not e2.startswith("run_")
                        ]
                        if any(find_metrics_files(os.path.join(sub_path, ss)) for ss in sub_subdirs):
                            is_provider = True
                            break

                if is_provider:
                    # Nested: openai/gpt-oss-120b/, openai/gpt-oss-20b/
                    for sub in sorted(os.listdir(entry_path)):
                        sub_path = os.path.join(entry_path, sub)
                        if os.path.isdir(sub_path) and not sub.startswith("."):
                            if find_metrics_files(sub_path):
                                results.append((f"{entry}/{sub}", sub_path))
                else:
                    results.append((entry, entry_path))
        else:
            # No metrics directly — check if it's a provider dir with nested models
            for sub in sorted(os.listdir(entry_path)):
                sub_path = os.path.join(entry_path, sub)
                if os.path.isdir(sub_path) and not sub.startswith("."):
                    if find_metrics_files(sub_path):
                        results.append((f"{entry}/{sub}", sub_path))
    return results


def extract_domain(filepath: str) -> str:
    basename = os.path.basename(filepath)
    parts = basename.removeprefix("metrics_").removesuffix(".json")
    segments = parts.rsplit("_", 1)
    if len(segments) == 2 and segments[1].isdigit():
        return segments[0]
    return parts


def aggregate(metrics_list: list[dict]) -> dict:
    n = len(metrics_list)
    if n == 0:
        return {}

    tool_p, tool_r, tool_f1, tool_acc = [], [], [], []
    param_p, param_r, param_f1, param_acc = [], [], [], []
    tool_output_scores = []
    judge_scores = []
    judge_helpfulness = []
    judge_coherence = []
    pass_count = 0

    for m in metrics_list:
        # Support both old format (exact_match.tool_level) and new format (tool_call)
        em = m.get("exact_match", {})
        tl = em.get("tool_level", {}) or m.get("tool_call", {})
        pl = em.get("parameter_level", {}) or m.get("parameter", {})

        if tl:
            tool_p.append(tl.get("precision", 0))
            tool_r.append(tl.get("recall", 0))
            tool_f1.append(tl.get("f1", 0))
            if tl.get("accuracy") is not None:
                tool_acc.append(tl.get("accuracy", 0))
        if pl:
            param_p.append(pl.get("precision", 0))
            param_r.append(pl.get("recall", 0))
            param_f1.append(pl.get("f1", 0))
            if pl.get("accuracy") is not None:
                param_acc.append(pl.get("accuracy", 0))

        # Support both old (tool_output_exact_match.score) and new (tool_output.exact_match)
        toem = m.get("tool_output_exact_match", {})
        if toem and "score" in toem:
            tool_output_scores.append(toem["score"])
        else:
            to = m.get("tool_output", {})
            if to and "exact_match" in to and to["exact_match"] is not None:
                tool_output_scores.append(to["exact_match"])

        judge = m.get("llm_as_judge", {})
        if judge and judge.get("overall_score") is not None:
            judge_scores.append(judge["overall_score"])
        scores = judge.get("scores", {})
        if scores.get("helpfulness", {}).get("score") is not None:
            judge_helpfulness.append(scores["helpfulness"]["score"])
        if scores.get("coherence", {}).get("score") is not None:
            judge_coherence.append(scores["coherence"]["score"])

        if m.get("pass"):
            pass_count += 1

    def _avg(lst):
        return sum(lst) / len(lst) if lst else None

    return {
        "count": n,
        "pass_rate": pass_count / n,
        "pass_count": pass_count,
        "tool_level": {
            "precision": _avg(tool_p),
            "recall": _avg(tool_r),
            "f1": _avg(tool_f1),
            "accuracy": _avg(tool_acc),
        },
        "parameter_level": {
            "precision": _avg(param_p),
            "recall": _avg(param_r),
            "f1": _avg(param_f1),
            "accuracy": _avg(param_acc),
        },
        "tool_output_exact_match": _avg(tool_output_scores),
        "llm_as_judge": _avg(judge_scores),
        "judge_helpfulness": _avg(judge_helpfulness),
        "judge_coherence": _avg(judge_coherence),
    }


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def aggregate_across_runs(run_aggregates: list[dict], per_run_metrics: list[list[dict]] = None) -> dict:
    """Compute mean ± std dev of each metric across multiple run aggregates.

    If per_run_metrics is provided (list of metrics lists, one per run),
    also computes Pass@k (passed in at least one run) and Pass^k (passed in all runs).
    """
    k = len(run_aggregates)
    if k == 0:
        return {}

    def _collect(key_path):
        values = []
        for agg in run_aggregates:
            obj = agg
            for key in key_path:
                obj = obj.get(key) if isinstance(obj, dict) else None
                if obj is None:
                    break
            if obj is not None:
                values.append(obj)
        return values

    def _mean_std(values):
        if not values:
            return None, None
        return sum(values) / len(values), _std(values)

    pass_rates = _collect(["pass_rate"])
    tool_f1s = _collect(["tool_level", "f1"])
    tool_ps = _collect(["tool_level", "precision"])
    tool_rs = _collect(["tool_level", "recall"])
    tool_accs = _collect(["tool_level", "accuracy"])
    param_f1s = _collect(["parameter_level", "f1"])
    param_ps = _collect(["parameter_level", "precision"])
    param_rs = _collect(["parameter_level", "recall"])
    param_accs = _collect(["parameter_level", "accuracy"])
    toem_scores = _collect(["tool_output_exact_match"])
    judge_scores = _collect(["llm_as_judge"])
    help_scores = _collect(["judge_helpfulness"])
    coh_scores = _collect(["judge_coherence"])

    result = {
        "num_runs": k,
        "pass_rate": {"mean": _mean_std(pass_rates)[0], "std": _mean_std(pass_rates)[1]},
        "tool_level": {
            "precision": {"mean": _mean_std(tool_ps)[0], "std": _mean_std(tool_ps)[1]},
            "recall": {"mean": _mean_std(tool_rs)[0], "std": _mean_std(tool_rs)[1]},
            "f1": {"mean": _mean_std(tool_f1s)[0], "std": _mean_std(tool_f1s)[1]},
            "accuracy": {"mean": _mean_std(tool_accs)[0], "std": _mean_std(tool_accs)[1]},
        },
        "parameter_level": {
            "precision": {"mean": _mean_std(param_ps)[0], "std": _mean_std(param_ps)[1]},
            "recall": {"mean": _mean_std(param_rs)[0], "std": _mean_std(param_rs)[1]},
            "f1": {"mean": _mean_std(param_f1s)[0], "std": _mean_std(param_f1s)[1]},
            "accuracy": {"mean": _mean_std(param_accs)[0], "std": _mean_std(param_accs)[1]},
        },
        "tool_output_exact_match": {"mean": _mean_std(toem_scores)[0], "std": _mean_std(toem_scores)[1]},
        "llm_as_judge": {"mean": _mean_std(judge_scores)[0], "std": _mean_std(judge_scores)[1]},
        "judge_helpfulness": {"mean": _mean_std(help_scores)[0], "std": _mean_std(help_scores)[1]},
        "judge_coherence": {"mean": _mean_std(coh_scores)[0], "std": _mean_std(coh_scores)[1]},
    }

    # Pass@k and Pass^k: per-conversation across runs
    if per_run_metrics and len(per_run_metrics) == k:
        # Build {conversation_id: [pass_in_run_0, pass_in_run_1, ...]}
        per_conv = defaultdict(list)
        for run_metrics in per_run_metrics:
            for m in run_metrics:
                cid = m.get("conversation_id")
                if cid is not None:
                    per_conv[cid].append(bool(m.get("pass")))

        n_conv = len(per_conv)
        if n_conv > 0:
            pass_at_k = sum(1 for passes in per_conv.values() if any(passes)) / n_conv
            pass_all_k = sum(1 for passes in per_conv.values() if all(passes) and len(passes) == k) / n_conv
            result["pass_at_k"] = pass_at_k
            result["pass_all_k"] = pass_all_k

    return result


def print_summary(label: str, agg: dict):
    if not agg:
        return
    print(f"\n{'─' * 60}")
    print(f"  {label}  (n={agg['count']})")
    print(f"{'─' * 60}")
    print(f"  Pass rate          : {agg['pass_rate']:.2%} ({agg['pass_count']}/{agg['count']})")

    tl = agg["tool_level"]
    if tl["f1"] is not None:
        print(f"  Tool-level    F1   : {tl['f1']:.4f}  (P={tl['precision']:.4f}  R={tl['recall']:.4f})")

    pl = agg["parameter_level"]
    if pl["f1"] is not None:
        print(f"  Param-level   F1   : {pl['f1']:.4f}  (P={pl['precision']:.4f}  R={pl['recall']:.4f})")

    if agg["tool_output_exact_match"] is not None:
        print(f"  Tool output match  : {agg['tool_output_exact_match']:.4f}")

    if agg["llm_as_judge"] is not None:
        print(f"  LLM-as-Judge       : {agg['llm_as_judge']:.2f}/5")


def _fmt(mean, std):
    if mean is None:
        return "N/A"
    if std is None or std == 0:
        return f"{mean:.4f}"
    return f"{mean:.4f} ± {std:.4f}"


def _fmt_pct(mean, std):
    if mean is None:
        return "N/A"
    if std is None or std == 0:
        return f"{mean:.2%}"
    return f"{mean:.2%} ± {std:.2%}"


def print_multi_run_summary(label: str, summary: dict):
    if not summary:
        return
    print(f"\n{'═' * 60}")
    print(f"  {label}  (k={summary['num_runs']} runs)")
    print(f"{'═' * 60}")

    pr = summary["pass_rate"]
    print(f"  Pass rate          : {_fmt_pct(pr['mean'], pr['std'])}")
    if "pass_at_k" in summary:
        print(f"  Pass@k             : {summary['pass_at_k']:.2%}")
    if "pass_all_k" in summary:
        print(f"  Pass^k             : {summary['pass_all_k']:.2%}")

    tl = summary["tool_level"]
    print(f"  Tool-level    F1   : {_fmt(tl['f1']['mean'], tl['f1']['std'])}")
    print(f"                P    : {_fmt(tl['precision']['mean'], tl['precision']['std'])}")
    print(f"                R    : {_fmt(tl['recall']['mean'], tl['recall']['std'])}")

    pl = summary["parameter_level"]
    print(f"  Param-level   F1   : {_fmt(pl['f1']['mean'], pl['f1']['std'])}")
    print(f"                P    : {_fmt(pl['precision']['mean'], pl['precision']['std'])}")
    print(f"                R    : {_fmt(pl['recall']['mean'], pl['recall']['std'])}")

    toem = summary["tool_output_exact_match"]
    print(f"  Tool output match  : {_fmt(toem['mean'], toem['std'])}")

    judge = summary["llm_as_judge"]
    if judge["mean"] is not None:
        print(f"  LLM-as-Judge       : {_fmt(judge['mean'], judge['std'])}")
    helpfulness = summary.get("judge_helpfulness", {})
    if helpfulness.get("mean") is not None:
        print(f"    Helpfulness      : {_fmt(helpfulness['mean'], helpfulness['std'])}")
    coherence = summary.get("judge_coherence", {})
    if coherence.get("mean") is not None:
        print(f"    Coherence        : {_fmt(coherence['mean'], coherence['std'])}")


def print_failures(metrics_list: list[dict], domain: str):
    failures = []
    for m in metrics_list:
        if not m.get("pass"):
            failures.append(m)
    if not failures:
        print(f"  No failures in {domain}.")
        return
    print(f"\n  Failures in {domain} ({len(failures)}):")
    for m in failures:
        cid = m.get("conversation_id", "?")
        toem = m.get("tool_output_exact_match", {})
        score = toem.get("score", "N/A")
        em = m.get("exact_match", {})
        tl_f1 = em.get("tool_level", {}).get("f1", "N/A")
        print(f"    id={cid}  tool_f1={tl_f1}  output_match={score}")
        for detail in toem.get("per_tool_detail", []):
            if not detail.get("matched"):
                err = f" ({detail.get('error', '')})" if detail.get("error") else ""
                print(f"      MISS: {detail['tool_name']}{err}")


# ---------------------------------------------------------------------------
# LaTeX table generation
# ---------------------------------------------------------------------------

MODEL_DISPLAY_NAMES = {
    "claude_code_claude-4.6-opus": "Claude Opus 4.6",
    "claude_code_claude-sonnet-4-6": "Claude Sonnet 4.6",
    "claude-haiku-4-5": "Claude Haiku 4.5",
    "claude-sonnet-4-5": "Claude Sonnet 4.5",
    "claude-opus-4-6": "Claude Opus 4.6",
    "openai/gpt-oss-120b": "GPT-OSS-120B",
    "openai/gpt-oss-20b": "GPT-OSS-20B",
    "google/gemma-4-31B-it": "Gemma4-31B-it",
    "google/gemma-4-26B-A4B-it": "Gemma4-26B-A4B-it",
    "google/gemma-4-e2b-it": "Gemma4-E2B-it",
    "google/gemma-4-e4b-it": "Gemma4-E4B-it",
    "meta-llama/Llama-3.3-70B-Instruct": "Llama3.3-70B-Instruct",
    "gpt-5.4": "GPT-5.4",
    "gpt-5.4-mini": "GPT-5.4-Mini",
    "gpt-5.4-nano": "GPT-5.4-Nano",
    "gpt-5.5": "GPT-5.5",
    "gemini-3.5": "Gemini3.5",
}

# Groups control \midrule separators between model families.
# Each group is a list of model_dir keys. Order within and between groups is preserved.
MODEL_GROUPS = [
    # Open-weight / self-hosted
    [
        "google/gemma-4-e2b-it",
        "google/gemma-4-e4b-it",
        "google/gemma-4-26B-A4B-it",
        "google/gemma-4-31B-it",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
    ],
    # Proprietary API
    [
        "claude-haiku-4-5",
        "claude-sonnet-4-5",
        "claude-opus-4-6",
        "claude_code_claude-sonnet-4-6",
        "claude_code_claude-4.6-opus",
        "gpt-5.4-nano",
        "gpt-5.4-mini",
        "gpt-5.4",
        "gpt-5.5",
        "gemini-3.5",
    ],
]


def _ordered_model_keys(model_keys: list[str]) -> list[str | None]:
    """Return model keys ordered by MODEL_GROUPS, with None as a group separator.

    Models not listed in any group are appended at the end (no separator).
    """
    key_set = set(model_keys)
    ordered = []
    for group in MODEL_GROUPS:
        group_present = [k for k in group if k in key_set]
        if group_present:
            if ordered:
                ordered.append(None)  # separator
            ordered.extend(group_present)
    # Append any ungrouped models
    grouped = {k for g in MODEL_GROUPS for k in g}
    ungrouped = [k for k in model_keys if k not in grouped]
    if ungrouped:
        if ordered:
            ordered.append(None)
        ordered.extend(ungrouped)
    return ordered if ordered else list(model_keys)


def _latex_val(value, is_pct=False, std=None, show_stddev=False):
    if value is None:
        return "--"
    if is_pct:
        mean_str = f"{value * 100:.2f}"
    else:
        mean_str = f"{value:.2f}"
    if show_stddev and std is not None and std > 0:
        if is_pct:
            std_str = f"{std * 100:.2f}"
        else:
            std_str = f"{std:.2f}"
        return mean_str + r" {\scriptsize $\pm$ " + std_str + "}"
    return mean_str


def generate_latex_table(model_results: dict[str, dict], caption: str = None, show_stddev: bool = False) -> str:
    """Generate a LaTeX table from model-level aggregated results.

    model_results: {model_dir_name: aggregate_dict or multi_run_summary_dict}
    caption: optional caption/label for the table
    show_stddev: if True, display mean ± std (std in smaller font)
    """
    lines = []
    lines.append(r"\begin{table*}[!th]")
    lines.append(r"\centering")
    if caption:
        lines.append(r"\caption{" + caption.replace("_", r"\_") + "}")
    lines.append(r"\resizebox{\textwidth}{!}{")
    lines.append(r"\begin{tabular}{lcc c|ccc c|c|cc|cc}")
    lines.append(r"\toprule")
    lines.append(
        r"\textsc{Model} & \multicolumn{3}{c|}{\textsc{Tool Call}} & "
        r"\multicolumn{3}{c|}{\textsc{Param. Call}} & "
        r"\multicolumn{1}{c|}{\textsc{Tool Output}} & "
        r"\multicolumn{2}{c|}{\textsc{Pass Rate}} & "
        r"\multicolumn{2}{c|}{\textsc{LLM-as-a-Judge}} \\"
    )
    lines.append(
        r" & \textsc{Acc.} & \textsc{Recall} & \textsc{F1} & "
        r"\textsc{Acc.} & \textsc{Recall} & \textsc{F1} & "
        r"\textsc{EM} & "
        r"\textsc{Pass@k} & \textsc{Pass$^k$} & "
        r"\textsc{Help.} & \textsc{Coh.} \\"
    )
    lines.append(r"\midrule")

    for model_dir in _ordered_model_keys(list(model_results.keys())):
        if model_dir is None:
            lines.append(r"\midrule")
            continue
        result = model_results[model_dir]
        display_name = MODEL_DISPLAY_NAMES.get(model_dir, model_dir)

        # Handle both multi-run summary (has nested mean/std) and single aggregate
        if "num_runs" in result:
            # Multi-run summary
            tool_r = result.get("tool_level", {}).get("recall", {}).get("mean")
            tool_r_std = result.get("tool_level", {}).get("recall", {}).get("std")
            tool_f1 = result.get("tool_level", {}).get("f1", {}).get("mean")
            tool_f1_std = result.get("tool_level", {}).get("f1", {}).get("std")
            tool_acc = result.get("tool_level", {}).get("accuracy", {}).get("mean")
            tool_acc_std = result.get("tool_level", {}).get("accuracy", {}).get("std")
            param_r = result.get("parameter_level", {}).get("recall", {}).get("mean")
            param_r_std = result.get("parameter_level", {}).get("recall", {}).get("std")
            param_f1 = result.get("parameter_level", {}).get("f1", {}).get("mean")
            param_f1_std = result.get("parameter_level", {}).get("f1", {}).get("std")
            param_acc = result.get("parameter_level", {}).get("accuracy", {}).get("mean")
            param_acc_std = result.get("parameter_level", {}).get("accuracy", {}).get("std")
            toem = result.get("tool_output_exact_match", {}).get("mean")
            toem_std = result.get("tool_output_exact_match", {}).get("std")
            pass_at_k = result.get("pass_at_k")
            pass_all_k = result.get("pass_all_k")
            helpfulness = result.get("judge_helpfulness", {}).get("mean")
            helpfulness_std = result.get("judge_helpfulness", {}).get("std")
            coherence = result.get("judge_coherence", {}).get("mean")
            coherence_std = result.get("judge_coherence", {}).get("std")
        else:
            # Single aggregate
            tool_r = result.get("tool_level", {}).get("recall")
            tool_r_std = None
            tool_f1 = result.get("tool_level", {}).get("f1")
            tool_f1_std = None
            tool_acc = result.get("tool_level", {}).get("accuracy")
            tool_acc_std = None
            param_r = result.get("parameter_level", {}).get("recall")
            param_r_std = None
            param_f1 = result.get("parameter_level", {}).get("f1")
            param_f1_std = None
            param_acc = result.get("parameter_level", {}).get("accuracy")
            param_acc_std = None
            toem = result.get("tool_output_exact_match")
            toem_std = None
            pass_at_k = result.get("pass_rate")
            pass_all_k = result.get("pass_rate")
            helpfulness = result.get("judge_helpfulness")
            helpfulness_std = None
            coherence = result.get("judge_coherence")
            coherence_std = None

        row = (
            f"\\textsc{{{display_name}}} & "
            f"{_latex_val(tool_acc, is_pct=True, std=tool_acc_std, show_stddev=show_stddev)} & "
            f"{_latex_val(tool_r, is_pct=True, std=tool_r_std, show_stddev=show_stddev)} & "
            f"{_latex_val(tool_f1, is_pct=True, std=tool_f1_std, show_stddev=show_stddev)} & "
            f"{_latex_val(param_acc, is_pct=True, std=param_acc_std, show_stddev=show_stddev)} & "
            f"{_latex_val(param_r, is_pct=True, std=param_r_std, show_stddev=show_stddev)} & "
            f"{_latex_val(param_f1, is_pct=True, std=param_f1_std, show_stddev=show_stddev)} & "
            f"{_latex_val(toem, is_pct=True, std=toem_std, show_stddev=show_stddev)} & "
            f"{_latex_val(pass_at_k, is_pct=True)} & "
            f"{_latex_val(pass_all_k, is_pct=True)} & "
            f"{_latex_val(helpfulness, std=helpfulness_std, show_stddev=show_stddev)} & "
            f"{_latex_val(coherence, std=coherence_std, show_stddev=show_stddev)} \\\\"
        )
        lines.append(row)

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"}")
    lines.append(r"\end{table*}")

    return "\n".join(lines)


# Single-domain columns shown in the per-domain pass-rate table (Table 2/3)
SINGLE_DOMAINS = [
    ("attraction",       "Attr."),
    ("bar",              "Bar"),
    ("cafe",             "Café"),
    ("cruise",           "Cruise"),
    ("dessert",          "Dessert"),
    ("flight",           "Flight"),
    ("food_and_dining",  "F\\&D"),
    ("hotel",            "Hotel"),
    ("kayak_rental",     "Kayak"),
    ("live_show",        "Live"),
    ("vehicle_rental",   "Vehicle"),
]


def generate_pass_rate_table(
    domain_model_results: dict[str, dict[str, dict]],
    overall_model_results: dict[str, dict],
    caption: str = None,
    show_stddev: bool = False,
    metric: str = "pass_at_k",
) -> str:
    """Generate a per-domain pass-rate table (rows=models, cols=domains + Avg.).

    domain_model_results: {domain_name: {model_dir: result_dict}}
    overall_model_results: {model_dir: result_dict}  (for the Avg. column)
    metric: which pass metric to use — 'pass_at_k' or 'pass_all_k'
    """
    n_single = len(SINGLE_DOMAINS)
    col_spec = "l" + "r" * n_single + "|r"

    lines = []
    lines.append(r"\begin{table*}[t]")
    lines.append(r"\centering")
    if caption:
        lines.append(r"\caption{" + caption.replace("_", r"\_") + "}")
    lines.append(r"\resizebox{\textwidth}{!}{")
    lines.append(r"\begin{tabular}{" + col_spec + "}")
    lines.append(r"\toprule")

    domain_headers = " & ".join(r"\textsc{" + abbr + "}" for _, abbr in SINGLE_DOMAINS)
    lines.append(r"\textsc{Model} & " + domain_headers + r" & \textsc{Avg.} \\")
    lines.append(r"\midrule")

    for model_dir in _ordered_model_keys(list(overall_model_results.keys())):
        if model_dir is None:
            lines.append(r"\midrule")
            continue
        display_name = MODEL_DISPLAY_NAMES.get(model_dir, model_dir)
        cells = []
        for domain_key, _ in SINGLE_DOMAINS:
            domain_data = domain_model_results.get(domain_key, {})
            result = domain_data.get(model_dir)
            if result is None:
                cells.append("--")
                continue
            if "num_runs" in result:
                val = result.get(metric)
                std = None
            else:
                val = result.get("pass_rate")
                std = None
            cells.append(_latex_val(val, is_pct=True, std=std, show_stddev=show_stddev))

        # Avg. column from overall results
        overall = overall_model_results.get(model_dir, {})
        if "num_runs" in overall:
            avg_val = overall.get(metric)
        else:
            avg_val = overall.get("pass_rate")
        avg_str = _latex_val(avg_val, is_pct=True)

        row = f"\\textsc{{{display_name}}} & " + " & ".join(cells) + " & " + avg_str + r" \\"
        lines.append(row)

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"}")
    lines.append(r"\end{table*}")

    return "\n".join(lines)


def _aggregate_model(model_path: str):
    """Aggregate a model dir, using multi-run logic when run_* dirs exist per domain."""
    domain_subdirs = find_domain_subdirs(model_path)
    # Check if any domain has multiple run_* dirs
    has_runs = False
    for d in domain_subdirs:
        if not os.path.basename(d).startswith("run_"):
            runs = find_run_subdirs(d)
            if len(runs) > 1:
                has_runs = True
                break

    if has_runs:
        # Multi-run: group metrics by positional index (latest 3 runs per domain)
        run_groups = defaultdict(list)  # {position_index: [metrics...]}
        for d in domain_subdirs:
            if os.path.basename(d).startswith("run_"):
                continue
            domain_name = os.path.basename(d)
            runs = find_run_subdirs(d)
            if runs:
                runs = runs[-3:]
                for i, run_path in enumerate(runs):
                    for fp in find_metrics_files(run_path):
                        with open(fp, "r", encoding="utf-8") as f:
                            m = json.load(f)
                        if m.get("conversation_id") is not None:
                            m["conversation_id"] = f"{domain_name}_{m['conversation_id']}"
                        run_groups[i].append(m)
            else:
                # Domain has metrics directly (no run_* subdirs)
                for fp in find_metrics_files(d):
                    with open(fp, "r", encoding="utf-8") as f:
                        m = json.load(f)
                    if m.get("conversation_id") is not None:
                        m["conversation_id"] = f"{domain_name}_{m['conversation_id']}"
                    run_groups["_direct"].append(m)

        if not run_groups:
            return None

        sorted_runs = sorted(run_groups.keys())
        run_aggregates = [aggregate(run_groups[r]) for r in sorted_runs]
        per_run_metrics = [run_groups[r] for r in sorted_runs]
        return aggregate_across_runs(run_aggregates, per_run_metrics=per_run_metrics)
    else:
        # Single run: just pool all metrics
        all_files = find_metrics_files(model_path)
        if not all_files:
            return None
        all_metrics = []
        for fp in all_files:
            with open(fp, "r", encoding="utf-8") as f:
                all_metrics.append(json.load(f))
        return aggregate(all_metrics)


def _check_metrics_file(filepath):
    """Check a single metrics file for issues. Returns list of issue strings."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        issues.append(f"invalid JSON: {e}")
        return issues

    em = data.get("exact_match", {})
    tl = em.get("tool_level", {}) or data.get("tool_call", {})
    pl = em.get("parameter_level", {}) or data.get("parameter", {})

    if not tl:
        issues.append("missing tool_level metrics")
    elif tl.get("f1") is None:
        issues.append("tool_level.f1 is null")

    if not pl:
        issues.append("missing parameter_level metrics")
    elif pl.get("f1") is None:
        issues.append("parameter_level.f1 is null")

    toem = data.get("tool_output_exact_match", {})
    to = data.get("tool_output", {})
    if toem:
        if toem.get("score") is None:
            issues.append("tool_output_exact_match.score is null")
    elif to:
        if to.get("exact_match") is None:
            issues.append("tool_output.exact_match is null")
    else:
        issues.append("missing tool_output metrics")

    return issues


def audit_runs(run_dir, expected_runs=3):
    """Audit all domains under run_dir for missing/extra runs and metrics issues.

    Always runs and saves report to results/audit_report.json.
    """
    domain_subdirs = find_domain_subdirs(run_dir)
    non_run_dirs = [d for d in domain_subdirs if not os.path.basename(d).startswith("run_")]

    if not non_run_dirs:
        return

    report = {
        "model_dir": run_dir,
        "expected_runs": expected_runs,
        "domains": {},
        "summary": {
            "total_domains": len(non_run_dirs),
            "domains_missing_runs": [],
            "domains_extra_runs": [],
            "domains_with_metrics_issues": [],
            "total_metrics_issues": 0,
        },
    }

    for domain_path in non_run_dirs:
        domain_name = os.path.basename(domain_path)
        run_dirs_list = find_run_subdirs(domain_path)
        num_runs = len(run_dirs_list)

        domain_report = {
            "num_runs": num_runs,
            "status": "ok",
            "runs": {},
            "issues": [],
        }

        if num_runs < expected_runs:
            domain_report["status"] = "missing_runs"
            domain_report["issues"].append(f"have {num_runs}, expected {expected_runs}")
            report["summary"]["domains_missing_runs"].append(domain_name)
        elif num_runs > expected_runs:
            domain_report["status"] = "extra_runs"
            domain_report["issues"].append(f"have {num_runs}, expected {expected_runs}")
            report["summary"]["domains_extra_runs"].append(domain_name)

        first_run_count = None
        for run_path in run_dirs_list:
            run_name = os.path.basename(run_path)
            metrics_files = find_metrics_files(run_path)
            num_metrics = len(metrics_files)

            run_report = {"num_metrics_files": num_metrics, "issues": []}

            if first_run_count is None:
                first_run_count = num_metrics
            elif num_metrics != first_run_count:
                run_report["issues"].append(
                    f"inconsistent metrics count: {num_metrics} vs {first_run_count} in first run"
                )

            for mf in metrics_files:
                file_issues = _check_metrics_file(mf)
                if file_issues:
                    basename = os.path.basename(mf)
                    for issue in file_issues:
                        run_report["issues"].append(f"{basename}: {issue}")

            domain_report["runs"][run_name] = run_report
            if run_report["issues"]:
                report["summary"]["total_metrics_issues"] += len(run_report["issues"])

        if any(r["issues"] for r in domain_report["runs"].values()):
            report["summary"]["domains_with_metrics_issues"].append(domain_name)

        report["domains"][domain_name] = domain_report

    s = report["summary"]
    has_issues = s["domains_missing_runs"] or s["domains_extra_runs"] or s["domains_with_metrics_issues"]

    print(f"\n{'─' * 60}")
    print(f"  AUDIT: {run_dir}")
    print(f"{'─' * 60}")
    print(f"  Domains: {s['total_domains']}  |  Expected runs: {expected_runs}")

    if s["domains_missing_runs"]:
        print(f"\n  MISSING RUNS:")
        for d in s["domains_missing_runs"]:
            dr = report["domains"][d]
            run_names = sorted(dr["runs"].keys())
            print(f"    {d}: {dr['num_runs']}/{expected_runs} — have: {', '.join(run_names) if run_names else 'none'}")

    if s["domains_extra_runs"]:
        print(f"\n  EXTRA RUNS:")
        for d in s["domains_extra_runs"]:
            dr = report["domains"][d]
            run_names = sorted(dr["runs"].keys())
            print(f"    {d}: {dr['num_runs']}/{expected_runs} — have: {', '.join(run_names)}")

    if s["domains_with_metrics_issues"]:
        print(f"\n  METRICS ISSUES:")
        for d in s["domains_with_metrics_issues"]:
            dr = report["domains"][d]
            for run_name, run_report in sorted(dr["runs"].items()):
                if run_report["issues"]:
                    print(f"    {d}/{run_name}:")
                    for issue in run_report["issues"]:
                        print(f"      - {issue}")

    if not has_issues:
        print(f"\n  All {s['total_domains']} domains have {expected_runs} runs with valid metrics.")

    model_name = os.path.basename(run_dir)
    _save_result(f"{model_name}/audit_report.json", report)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate simulation metrics (single or multi-run).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("run_dir", help="Path to run, domain, or model directory with metrics_*.json files.")
    parser.add_argument("--output", type=str, default=None, help="Write results as JSON to this path.")
    parser.add_argument("--failures", action="store_true", help="Show details for failing conversations.")
    parser.add_argument("--latex", action="store_true", help="Output LaTeX tables (overall + per-domain). Point at simulated_conversation/ to compare all models.")
    args = parser.parse_args()

    run_dir = args.run_dir
    if not os.path.isabs(run_dir):
        run_dir = os.path.join(_repo_root, run_dir)

    if not os.path.isdir(run_dir):
        print(f"ERROR: Directory not found: {run_dir}")
        sys.exit(1)

    # --latex mode: find all model directories and generate overall + per-domain tables
    if args.latex:
        model_results = {}
        discovered = find_model_dirs(run_dir)

        if discovered:
            model_dirs = discovered
            for model_name, model_path in discovered:
                model_results[model_name] = _aggregate_model(model_path)
        else:
            # run_dir itself is a model dir
            model_name = os.path.basename(run_dir)
            result = _aggregate_model(run_dir)
            if result:
                model_results[model_name] = result
            model_dirs = [(model_name, run_dir)]

        # Overall table
        if model_results:
            print("% === Overall ===")
            latex = generate_latex_table(model_results)
            latex_std = generate_latex_table(model_results, show_stddev=True)
            print(latex)
            print()
            _save_result("latex/overall.tex", latex, is_text=True)
            _save_result("latex/overall_with_std.tex", latex_std, is_text=True)
            _save_result("latex/overall.json", model_results)
        else:
            print("No model results found for LaTeX table.")
            return

        # Per-domain tables
        domain_model_results = defaultdict(dict)
        for model_name, model_path in model_dirs:
            for entry in sorted(os.listdir(model_path)):
                domain_path = os.path.join(model_path, entry)
                if not os.path.isdir(domain_path) or entry.startswith("."):
                    continue
                files = find_metrics_files(domain_path)
                if not files:
                    continue
                runs = find_run_subdirs(domain_path)
                if len(runs) > 1:
                    runs = runs[-3:]
                    run_aggregates = []
                    per_run_metrics = []
                    for r in runs:
                        rfiles = find_metrics_files(r)
                        metrics = [json.load(open(fp)) for fp in rfiles]
                        run_aggregates.append(aggregate(metrics))
                        per_run_metrics.append(metrics)
                    domain_model_results[entry][model_name] = aggregate_across_runs(
                        run_aggregates, per_run_metrics=per_run_metrics
                    )
                else:
                    metrics = [json.load(open(fp)) for fp in files]
                    domain_model_results[entry][model_name] = aggregate(metrics)

        if domain_model_results:
            all_latex_parts = []
            all_latex_std_parts = []
            for domain_name in sorted(domain_model_results.keys()):
                print(f"% === {domain_name} ===")
                latex = generate_latex_table(
                    domain_model_results[domain_name],
                    caption=domain_name,
                )
                latex_std = generate_latex_table(
                    domain_model_results[domain_name],
                    caption=domain_name,
                    show_stddev=True,
                )
                print(latex)
                print()
                all_latex_parts.append(f"% === {domain_name} ===\n{latex}")
                all_latex_std_parts.append(f"% === {domain_name} ===\n{latex_std}")
                _save_result(f"latex/per_domain/{domain_name}/{domain_name}.tex", latex, is_text=True)
                _save_result(f"latex/per_domain/{domain_name}/{domain_name}_with_std.tex", latex_std, is_text=True)
                _save_result(f"latex/per_domain/{domain_name}/{domain_name}.json", domain_model_results[domain_name])
            _save_result("latex/per_domain.tex", "\n\n".join(all_latex_parts), is_text=True)
            _save_result("latex/per_domain_with_std.tex", "\n\n".join(all_latex_std_parts), is_text=True)

            # Pass-rate summary tables (rows=models, cols=single domains + Avg.)
            pr_table = generate_pass_rate_table(
                domain_model_results, model_results,
                caption="Overall Pass@k results on T1-Bench averaged over single-domain tasks.",
                metric="pass_at_k",
            )
            pr_table_k = generate_pass_rate_table(
                domain_model_results, model_results,
                caption=r"Overall Pass$^K$ results on T1-Bench averaged over single-domain tasks.",
                metric="pass_all_k",
            )
            _save_result("latex/pass_rate_at_k.tex", pr_table, is_text=True)
            _save_result("latex/pass_rate_all_k.tex", pr_table_k, is_text=True)
            print("% === Pass-rate table (pass_at_k) ===")
            print(pr_table)
            print()
            print("% === Pass-rate table (pass_all_k) ===")
            print(pr_table_k)

        return


    #   1. Model-level: has domain subdirs (non-run_*) containing metrics
    #   2. Domain-level / multi-run: has run_* subdirs with metrics
    #   3. Single-run: has metrics_*.json directly
    run_subdirs = find_run_subdirs(run_dir)
    domain_subdirs = find_domain_subdirs(run_dir)
    direct_metrics = find_metrics_files(run_dir)

    # Model-level: multiple domain subdirs that aren't run_* folders
    # (run_* folders indicate domain-level multi-run instead)
    has_domain_dirs = any(
        not os.path.basename(d).startswith("run_") for d in domain_subdirs
    )

    if has_domain_dirs and not run_subdirs:
        # Model-level mode: aggregate per domain, then overall
        non_run_dirs = [d for d in domain_subdirs if not os.path.basename(d).startswith("run_")]
        model_name = os.path.basename(run_dir)
        print(f"Model-level mode: found {len(non_run_dirs)} domain(s) under: {run_dir}")
        for d in non_run_dirs:
            print(f"  {os.path.basename(d)}")

        all_metrics = []
        domain_summaries = {}
        for domain_dir in non_run_dirs:
            domain_name = os.path.basename(domain_dir)
            files = find_metrics_files(domain_dir)
            metrics = []
            for fp in files:
                with open(fp, "r", encoding="utf-8") as f:
                    metrics.append(json.load(f))
            all_metrics.extend(metrics)
            agg = aggregate(metrics)
            domain_summaries[domain_name] = agg
            print_summary(domain_name, agg)
            _save_result(f"{model_name}/{domain_name}.json", agg)
            if args.failures:
                print_failures(metrics, domain_name)

        if len(non_run_dirs) > 1:
            overall = aggregate(all_metrics)
            print_summary("OVERALL", overall)
            domain_summaries["_overall"] = overall
            _save_result(f"{model_name}/overall.json", overall)

        if args.output:
            output_path = args.output if os.path.isabs(args.output) else os.path.join(_repo_root, args.output)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(domain_summaries, f, indent=2)
            print(f"\nSaved to: {output_path}")

    elif run_subdirs:
        # Multi-run mode
        domain_name = os.path.basename(run_dir)
        model_name = os.path.basename(os.path.dirname(run_dir))
        print(f"Found {len(run_subdirs)} run(s) under: {run_dir}")
        for rd in run_subdirs:
            print(f"  {os.path.basename(rd)}")

        run_aggregates = []
        per_run_metrics = []
        for rd in run_subdirs:
            files = find_metrics_files(rd)
            metrics = []
            for fp in files:
                with open(fp, "r", encoding="utf-8") as f:
                    metrics.append(json.load(f))
            agg = aggregate(metrics)
            if agg:
                run_aggregates.append(agg)
                per_run_metrics.append(metrics)
                print_summary(os.path.basename(rd), agg)
                if args.failures:
                    print_failures(metrics, os.path.basename(rd))

        if len(run_aggregates) > 1:
            summary = aggregate_across_runs(run_aggregates, per_run_metrics=per_run_metrics)
            print_multi_run_summary("MEAN ± STD ACROSS RUNS", summary)
            _save_result(f"{model_name}/{domain_name}_multi_run.json", {
                "per_run": [{"run": os.path.basename(rd), **agg} for rd, agg in zip(run_subdirs, run_aggregates)],
                "summary": summary,
            })

            if args.output:
                output_path = args.output if os.path.isabs(args.output) else os.path.join(_repo_root, args.output)
                out = {"per_run": [{"run": os.path.basename(rd), **agg} for rd, agg in zip(run_subdirs, run_aggregates)], "summary": summary}
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(out, f, indent=2)
                print(f"\nSaved to: {output_path}")
    else:
        # Single-run mode
        run_name = os.path.basename(run_dir)
        domain_name = os.path.basename(os.path.dirname(run_dir))
        model_name = os.path.basename(os.path.dirname(os.path.dirname(run_dir)))

        files = find_metrics_files(run_dir)
        if not files:
            print(f"No metrics_*.json files found under: {run_dir}")
            sys.exit(1)

        print(f"Found {len(files)} metrics file(s) under: {run_dir}")

        by_domain = defaultdict(list)
        for fp in files:
            domain = extract_domain(fp)
            with open(fp, "r", encoding="utf-8") as f:
                by_domain[domain].append(json.load(f))

        all_metrics = []
        domain_summaries = {}
        for domain in sorted(by_domain.keys()):
            metrics = by_domain[domain]
            all_metrics.extend(metrics)
            agg = aggregate(metrics)
            domain_summaries[domain] = agg
            print_summary(domain, agg)
            if args.failures:
                print_failures(metrics, domain)

        if len(by_domain) > 1:
            overall = aggregate(all_metrics)
            print_summary("OVERALL", overall)
            domain_summaries["_overall"] = overall

        _save_result(f"{model_name}/{domain_name}/{run_name}.json", domain_summaries)

        if args.output:
            output_path = args.output if os.path.isabs(args.output) else os.path.join(_repo_root, args.output)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(domain_summaries, f, indent=2)
            print(f"\nSaved to: {output_path}")

    audit_runs(run_dir)


if __name__ == "__main__":
    main()
