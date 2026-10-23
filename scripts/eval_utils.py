"""
eval_utils.py

Shared evaluation utilities for tool-call matching.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

# Params that are free-text user input and cannot be reliably exact-matched
_EXCLUDED_PARAMS: frozenset[str] = frozenset({"reason"})


def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def score_params(
    expected_params: dict, actual_params: dict
) -> tuple[int, int, int, list, list, list]:
    """
    Compare expected vs actual tool parameters.

    Returns (n_matched, n_expected, n_predicted, matched, missing, extra).
    Params in _EXCLUDED_PARAMS and empty actual values are excluded from scoring.
    """
    matched = []
    missing = []
    for param, exp_val in expected_params.items():
        if param in _EXCLUDED_PARAMS:
            continue
        if param in actual_params and _normalize(exp_val) == _normalize(actual_params[param]):
            matched.append(param)
        else:
            missing.append(param)

    extra = [
        p for p in actual_params
        if p not in expected_params
        and p not in _EXCLUDED_PARAMS
        and not _is_empty_value(actual_params[p])
    ]

    n_expected = sum(1 for p in expected_params if p not in _EXCLUDED_PARAMS)
    n_matched = len(matched)
    n_predicted = sum(
        1 for p in actual_params
        if p not in _EXCLUDED_PARAMS
        and (p in expected_params or not _is_empty_value(actual_params[p]))
    )
    return n_matched, n_expected, n_predicted, matched, missing, extra


def best_match_assignment(
    expected_tool_calls: list[dict],
    actual_calls: list[dict],
) -> list[dict | None]:
    """
    For each gold call, pick the predicted call of the same tool name that
    maximises parameter recall, with each predicted call used at most once.

    Returns a list parallel to expected_tool_calls where each element is the
    matched actual call dict, or None if no predicted call exists for that tool.
    """
    predicted_by_tool: dict[str, list[int]] = defaultdict(list)
    for idx, c in enumerate(actual_calls):
        predicted_by_tool[c["tool_name"]].append(idx)

    used: set[int] = set()
    assignments: list[dict | None] = []

    for entry in expected_tool_calls:
        tool_name = entry["name"]
        candidates = [i for i in predicted_by_tool.get(tool_name, []) if i not in used]

        if not candidates:
            assignments.append(None)
            continue

        expected_params = entry.get("parameters", {})
        n_expected = sum(1 for p in expected_params if p not in _EXCLUDED_PARAMS)

        best_idx = None
        best_score = -1.0
        for i in candidates:
            actual_params = actual_calls[i].get("parameters", {})
            n_matched, _, _, _, _, _ = score_params(expected_params, actual_params)
            score = n_matched / n_expected if n_expected > 0 else 1.0
            if score > best_score:
                best_score = score
                best_idx = i

        used.add(best_idx)
        assignments.append(actual_calls[best_idx])

    return assignments


def _normalize(value: Any) -> Any:
    """Normalize a scalar/list/dict for case-insensitive, order-insensitive comparison."""
    import re
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in ("true", "false"):
        return value.strip().lower() == "true"
    if isinstance(value, str):
        normalized = value.replace("‑", "-").replace("‒", "-").replace("–", "-")
        return re.sub(r"[^\w\s]", "", normalized.strip().lower())
    if isinstance(value, list):
        items = [_normalize(v) for v in value]
        try:
            normalized = sorted(items)
        except TypeError:
            normalized = sorted(items, key=lambda x: json.dumps(x, sort_keys=True, default=str))
        if len(normalized) == 1:
            return normalized[0]
        try:
            return sorted(normalized)
        except TypeError:
            return sorted(normalized, key=str)
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in sorted(value.items())}
    return value
