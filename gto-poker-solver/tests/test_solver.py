from __future__ import annotations

from gto_poker_solver import (
    CFRTrainer,
    GameTree,
    KuhnPokerState,
    LeducHoldemState,
    OneCardPokerState,
    ReferenceCFRTrainer,
    evaluate_strategy,
)


def test_kuhn_cfr_plus_converges_to_known_game_value() -> None:
    tree = GameTree.from_root(KuhnPokerState())
    trainer = CFRTrainer(tree, variant="cfr+", averaging_delay=100)
    trainer.train(2_000)
    evaluation = evaluate_strategy(tree, trainer.average_strategy())

    assert tree.node_count == 58
    assert tree.information_set_count == 12
    assert abs(evaluation.profile_value_player_0 + 1.0 / 18.0) < 0.003
    assert evaluation.exploitability < 0.01


def test_vectorized_engine_matches_reference_updates() -> None:
    tree = GameTree.from_root(KuhnPokerState())
    fast = CFRTrainer(tree, variant="cfr+", averaging_delay=10).train(100)
    reference = ReferenceCFRTrainer(
        tree, variant="cfr+", averaging_delay=10
    ).train(100)

    fast_evaluation = evaluate_strategy(tree, fast.average_strategy())
    reference_evaluation = evaluate_strategy(tree, reference.average_strategy())
    assert abs(
        fast_evaluation.profile_value_player_0
        - reference_evaluation.profile_value_player_0
    ) < 1e-12
    assert abs(
        fast_evaluation.exploitability - reference_evaluation.exploitability
    ) < 1e-12


def test_one_card_three_rank_game_matches_kuhn_payoffs() -> None:
    kuhn_tree = GameTree.from_root(KuhnPokerState())
    one_card_tree = GameTree.from_root(
        OneCardPokerState(rank_count=3, pot=2.0, bet=1.0)
    )
    kuhn = CFRTrainer(kuhn_tree, variant="cfr+", averaging_delay=10).train(500)
    one_card = CFRTrainer(
        one_card_tree, variant="cfr+", averaging_delay=10
    ).train(500)
    kuhn_value = evaluate_strategy(kuhn_tree, kuhn.average_strategy())
    one_card_value = evaluate_strategy(one_card_tree, one_card.average_strategy())

    assert abs(
        kuhn_value.profile_value_player_0
        - one_card_value.profile_value_player_0
    ) < 1e-12


def test_leduc_tree_and_training_are_zero_sum() -> None:
    tree = GameTree.from_root(LeducHoldemState(max_raises=2))
    trainer = CFRTrainer(tree, variant="cfr+", averaging_delay=5).train(20)
    evaluation = evaluate_strategy(tree, trainer.average_strategy())

    assert tree.node_count == 18_277
    assert tree.information_set_count == 528
    assert evaluation.nash_conv >= 0.0
    assert evaluation.exploitability == evaluation.nash_conv / 2.0
