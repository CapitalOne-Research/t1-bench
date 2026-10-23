import os
import sys
import json
import glob
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.t1_plus_plus.tools import cafe

# Any other model, please add the folder path here.
models = {
    "claude-haiku-4-5": "../simulated_conversation/claude-haiku-4-5",
    "claude-opus-4-6": "../simulated_conversation/claude-opus-4-6",
    "claude-sonnet-4-5": "../simulated_conversation/claude-sonnet-4-5",
    "gpt-5.4": "../simulated_conversation/gpt-5.4",
    "gpt-5.4-mini": "../simulated_conversation/gpt-5.4-mini",
    "gpt-5.4-nano": "../simulated_conversation/gpt-5.4-nano",
    "gpt-oss-120b": "../simulated_conversation/openai/gpt-oss-120b",
    "gpt-oss-20b": "../simulated_conversation/openai/gpt-oss-20b",
    "gemma-4-26B-A4B-it" : "../simulated_conversation/google/gemma-4-26B-A4B-it",
    "gemma-4-31B-it" : "../simulated_conversation/google/gemma-4-31B-it",
    "gemma-4-E2B-it" : "../simulated_conversation/google/gemma-4-E2B-it",
    "gemma-4-E4B-it" : "../simulated_conversation/google/gemma-4-E4B-it",
}

EXCLUDE_DOMAINS = {"attraction", "openai"}

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "token_stats_output"


def get_domains(model_path):
    """Get all domain folders for a model, excluding non-domain entries."""
    if not os.path.isdir(model_path):
        return []
    domains = []
    for entry in sorted(os.listdir(model_path)):
        full_path = os.path.join(model_path, entry)
        if os.path.isdir(full_path) and entry not in EXCLUDE_DOMAINS:
            domains.append(entry)
    return domains


def get_run_folders(domain_path):
    """Get all run_* folders in a domain directory."""
    runs = []
    for entry in sorted(os.listdir(domain_path)):
        if entry.startswith("run_") and os.path.isdir(os.path.join(domain_path, entry)):
            runs.append(os.path.join(domain_path, entry))
    return runs


def extract_metrics_from_run(run_path, domain_name):
    """Extract turns_completed and assistant_agent_tokens from <domain>_<id>.json files."""
    pattern = os.path.join(run_path, f"{domain_name}_*.json")
    files = glob.glob(pattern)

    # Filter out metrics_ files
    files = [f for f in files if not os.path.basename(f).startswith("metrics_")]

    total_turns = 0
    total_tokens = 0
    count = 0

    for filepath in files:
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            metadata = data.get("metadata", {})
            turns = metadata.get("turns_completed", 0)
            tokens = metadata.get("assistant_agent_tokens", 0)
            total_turns += turns
            total_tokens += tokens
            count += 1
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            continue

    return total_turns, total_tokens, count


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    results = []

    for model_name, model_rel_path in models.items():
        model_path = str((SCRIPT_DIR / model_rel_path).resolve())
        domains = get_domains(model_path)

        for domain in domains:
            domain_path = os.path.join(model_path, domain)
            run_folders = get_run_folders(domain_path)

            run_avg_turns = []
            run_avg_tokens = []

            for run_path in run_folders:
                total_turns, total_tokens, count = extract_metrics_from_run(run_path, domain)
                if count > 0:
                    run_avg_turns.append(total_turns / count)
                    run_avg_tokens.append(total_tokens / count)

            if run_avg_turns:
                avg_turn = sum(run_avg_turns) / len(run_avg_turns)
                avg_token = sum(run_avg_tokens) / len(run_avg_tokens)

                results.append({
                    "model": model_name,
                    "domain": domain,
                    "avg_turns_completed": round(avg_turn, 2),
                    "avg_assistant_agent_tokens": round(avg_token, 2)
                })

    # Save JSON output
    json_output_path = OUTPUT_DIR / "token_stats.json"
    with open(json_output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"JSON output saved to: {json_output_path}")

    # Print table
    print(f"\n{'Model':<22} | {'Domain':<40} | {'Avg. Turn':<10} | {'Avg. Token Length':<18}")
    print("-" * 98)
    for row in results:
        print(f"{row['model']:<22} | {row['domain']:<40} | {row['avg_turns_completed']:<10} | {row['avg_assistant_agent_tokens']:<18}")


if __name__ == "__main__":
    main()
