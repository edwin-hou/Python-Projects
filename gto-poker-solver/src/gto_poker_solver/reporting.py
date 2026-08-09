"""Result serialization and compact human-readable strategy summaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .core import Action, Evaluation, GameTree, Strategy


def rounded_strategy(strategy: Strategy, digits: int = 8) -> dict[str, dict[str, float]]:
    return {
        key: {str(action): round(probability, digits) for action, probability in actions.items()}
        for key, actions in sorted(strategy.items())
    }


def result_document(
    *,
    game: str,
    parameters: Mapping[str, Any],
    variant: str,
    iterations: int,
    averaging_delay: int,
    tree: GameTree,
    evaluation: Evaluation,
    strategy: Strategy,
) -> dict[str, Any]:
    return {
        "game": game,
        "parameters": dict(parameters),
        "solver": {
            "algorithm": variant,
            "iterations": iterations,
            "averaging_delay": averaging_delay,
            "full_tree": True,
            "exact_best_response_evaluation": True,
        },
        "game_tree": {
            "nodes": tree.node_count,
            "information_sets": tree.information_set_count,
        },
        "evaluation": {
            key: round(value, 12) for key, value in evaluation.as_dict().items()
        },
        "average_strategy": rounded_strategy(strategy),
    }


def write_json(path: str | Path, document: Mapping[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def strategy_rows(
    strategy: Mapping[str, Mapping[Action, float]],
    *,
    prefix: str,
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for key in sorted(key for key in strategy if key.startswith(prefix)):
        actions = strategy[key]
        rendered = ", ".join(
            f"{action}={probability:.3%}" for action, probability in actions.items()
        )
        rows.append((key, rendered))
    return rows
