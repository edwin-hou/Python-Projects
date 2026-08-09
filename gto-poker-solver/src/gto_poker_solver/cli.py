"""Command-line interface for training and evaluating poker strategies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import GameTree, evaluate_strategy
from .fast import CFRTrainer
from .games import KuhnPokerState, LeducHoldemState, OneCardPokerState
from .reporting import result_document, write_json


def _build_game(args: argparse.Namespace) -> tuple[str, dict[str, Any], object]:
    if args.game == "kuhn":
        return "kuhn", {}, KuhnPokerState()
    if args.game == "leduc":
        parameters = {"max_raises": args.max_raises}
        return (
            "leduc",
            parameters,
            LeducHoldemState(max_raises=args.max_raises),
        )
    parameters = {
        "rank_count": args.ranks,
        "pot": args.pot,
        "bet": args.bet,
    }
    return (
        "one-card",
        parameters,
        OneCardPokerState(rank_count=args.ranks, pot=args.pot, bet=args.bet),
    )


def solve(args: argparse.Namespace) -> int:
    game_name, parameters, root_state = _build_game(args)
    tree = GameTree.from_root(root_state)  # type: ignore[arg-type]
    trainer = CFRTrainer(
        tree,
        variant=args.variant,
        averaging_delay=args.averaging_delay,
    )
    trainer.train(args.iterations)
    strategy = trainer.average_strategy()
    evaluation = evaluate_strategy(tree, strategy)
    document = result_document(
        game=game_name,
        parameters=parameters,
        variant=trainer.variant,
        iterations=trainer.iteration,
        averaging_delay=trainer.averaging_delay,
        tree=tree,
        evaluation=evaluation,
        strategy=strategy,
    )

    if args.output:
        write_json(args.output, document)

    summary = {
        "game": game_name,
        "parameters": parameters,
        "iterations": trainer.iteration,
        "variant": trainer.variant,
        "nodes": tree.node_count,
        "information_sets": tree.information_set_count,
        **document["evaluation"],
        "output": str(Path(args.output)) if args.output else None,
    }
    print(json.dumps(summary, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gto-solver",
        description="Solve finite heads-up poker games with CFR/CFR+.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    solve_parser = subparsers.add_parser("solve", help="train and evaluate a game")
    solve_parser.add_argument("game", choices=("kuhn", "leduc", "one-card"))
    solve_parser.add_argument("--iterations", type=int, default=100_000)
    solve_parser.add_argument("--variant", choices=("cfr", "cfr+"), default="cfr+")
    solve_parser.add_argument("--averaging-delay", type=int, default=1_000)
    solve_parser.add_argument("--output", type=str)
    solve_parser.add_argument("--max-raises", type=int, default=2)
    solve_parser.add_argument("--ranks", type=int, default=13)
    solve_parser.add_argument("--pot", type=float, default=100.0)
    solve_parser.add_argument("--bet", type=float, default=75.0)
    solve_parser.set_defaults(handler=solve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.iterations < 0:
        parser.error("--iterations must be non-negative")
    if args.max_raises < 0:
        parser.error("--max-raises must be non-negative")
    return int(args.handler(args))
