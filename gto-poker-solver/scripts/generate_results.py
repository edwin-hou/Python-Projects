"""Reproduce the checked-in solver benchmarks and convergence table."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from gto_poker_solver import (
    CFRTrainer,
    GameTree,
    KuhnPokerState,
    LeducHoldemState,
    OneCardPokerState,
    ReferenceCFRTrainer,
    evaluate_strategy,
)
from gto_poker_solver.reporting import result_document, write_json


@dataclass(frozen=True)
class Benchmark:
    name: str
    root_factory: Callable[[], object]
    trainer_factory: Callable[[GameTree], object]
    checkpoints: tuple[int, ...]
    output_name: str
    parameters: dict[str, object]


BENCHMARKS = {
    "kuhn": Benchmark(
        name="kuhn",
        root_factory=KuhnPokerState,
        trainer_factory=lambda tree: ReferenceCFRTrainer(
            tree, variant="cfr+", averaging_delay=1_000
        ),
        checkpoints=(100, 500, 1_000, 5_000, 20_000, 100_000),
        output_name="kuhn_cfr_plus_100k.json",
        parameters={},
    ),
    "one-card": Benchmark(
        name="one-card",
        root_factory=lambda: OneCardPokerState(
            rank_count=13, pot=100.0, bet=75.0
        ),
        trainer_factory=lambda tree: CFRTrainer(
            tree, variant="cfr+", averaging_delay=1_000
        ),
        checkpoints=(100, 500, 1_000, 5_000, 10_000, 20_000),
        output_name="one_card_13r_pot100_bet75_20k.json",
        parameters={"rank_count": 13, "pot": 100.0, "bet": 75.0},
    ),
    "leduc": Benchmark(
        name="leduc",
        root_factory=lambda: LeducHoldemState(max_raises=2),
        trainer_factory=lambda tree: CFRTrainer(
            tree, variant="cfr+", averaging_delay=500
        ),
        checkpoints=(100, 500, 1_000, 2_500, 5_000),
        output_name="leduc_cfr_plus_5k.json",
        parameters={"max_raises": 2},
    ),
}


def run_benchmark(benchmark: Benchmark, output_dir: Path) -> list[dict[str, object]]:
    tree = GameTree.from_root(benchmark.root_factory())  # type: ignore[arg-type]
    trainer = benchmark.trainer_factory(tree)
    rows: list[dict[str, object]] = []
    previous = 0

    for checkpoint in benchmark.checkpoints:
        trainer.train(checkpoint - previous)  # type: ignore[attr-defined]
        previous = checkpoint
        strategy = trainer.average_strategy()  # type: ignore[attr-defined]
        evaluation = evaluate_strategy(tree, strategy)
        row = {
            "game": benchmark.name,
            "iterations": checkpoint,
            **evaluation.as_dict(),
        }
        rows.append(row)
        print(
            f"{benchmark.name:8s} {checkpoint:>7,d} iterations | "
            f"exploitability={evaluation.exploitability:.9f}"
        )

    final_strategy = trainer.average_strategy()  # type: ignore[attr-defined]
    final_evaluation = evaluate_strategy(tree, final_strategy)
    document = result_document(
        game=benchmark.name,
        parameters=benchmark.parameters,
        variant=trainer.variant,  # type: ignore[attr-defined]
        iterations=trainer.iteration,  # type: ignore[attr-defined]
        averaging_delay=trainer.averaging_delay,  # type: ignore[attr-defined]
        tree=tree,
        evaluation=final_evaluation,
        strategy=final_strategy,
    )
    write_json(output_dir / benchmark.output_name, document)
    return rows


def write_convergence_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "game",
        "iterations",
        "profile_value_player_0",
        "best_response_value_player_0",
        "best_response_value_player_1",
        "nash_conv",
        "exploitability",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--game",
        choices=("all", *BENCHMARKS),
        default="all",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    selected = BENCHMARKS.values() if args.game == "all" else [BENCHMARKS[args.game]]
    all_rows: list[dict[str, object]] = []
    for benchmark in selected:
        all_rows.extend(run_benchmark(benchmark, args.output_dir))

    suffix = "" if args.game == "all" else f"_{args.game.replace('-', '_')}"
    write_convergence_csv(
        args.output_dir / f"convergence{suffix}.csv",
        all_rows,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
