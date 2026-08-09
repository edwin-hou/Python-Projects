"""Core extensive-form game, CFR/CFR+, and exploitability machinery.

The implementation intentionally uses only the Python standard library.  It is
small enough to read, but it still performs full-tree counterfactual regret
minimization and exact best-response evaluation for finite two-player,
zero-sum, perfect-recall games.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from math import fsum
from typing import Hashable, Mapping, Protocol, Sequence

Action = Hashable
CHANCE_PLAYER = -1
TERMINAL_PLAYER = -2


class GameState(Protocol):
    """Protocol required by :class:`GameTree`."""

    @property
    def current_player(self) -> int:
        """Return 0/1, ``CHANCE_PLAYER``, or ``TERMINAL_PLAYER``."""

    def legal_actions(self) -> tuple[Action, ...]:
        """Return legal actions at a non-terminal decision node."""

    def chance_outcomes(self) -> tuple[tuple[Action, float], ...]:
        """Return ``(action, probability)`` pairs at a chance node."""

    def child(self, action: Action) -> "GameState":
        """Return the state reached after ``action``."""

    def information_state_key(self, player: int) -> str:
        """Return the acting player's information-set identifier."""

    def utility(self, player: int) -> float:
        """Return terminal utility for ``player``."""


@dataclass(frozen=True, slots=True)
class TreeNode:
    """Compact immutable node stored in a prebuilt game tree."""

    player: int
    actions: tuple[Action, ...] = ()
    children: tuple[int, ...] = ()
    chance_probabilities: tuple[float, ...] = ()
    information_set: str | None = None
    utility_player_0: float = 0.0


@dataclass(slots=True)
class GameTree:
    """A prebuilt finite game tree used by the solver.

    Prebuilding removes object allocation from the hot CFR loop and also gives
    exact evaluators a stable integer node index.
    """

    nodes: list[TreeNode]
    root: int
    information_set_nodes: dict[str, tuple[int, ...]]
    information_set_actions: dict[str, tuple[Action, ...]]

    @classmethod
    def from_root(cls, root_state: GameState) -> "GameTree":
        nodes: list[TreeNode] = []
        infoset_nodes_mutable: dict[str, list[int]] = {}
        infoset_actions: dict[str, tuple[Action, ...]] = {}

        def build(state: GameState) -> int:
            node_id = len(nodes)
            # Placeholder; replaced after recursively building children.
            nodes.append(TreeNode(player=TERMINAL_PLAYER))
            player = state.current_player

            if player == TERMINAL_PLAYER:
                nodes[node_id] = TreeNode(
                    player=TERMINAL_PLAYER,
                    utility_player_0=float(state.utility(0)),
                )
                return node_id

            if player == CHANCE_PLAYER:
                outcomes = state.chance_outcomes()
                if not outcomes:
                    raise ValueError("Chance node has no outcomes")
                total_probability = fsum(probability for _, probability in outcomes)
                if abs(total_probability - 1.0) > 1e-10:
                    raise ValueError(
                        f"Chance probabilities sum to {total_probability}, not 1"
                    )
                actions = tuple(action for action, _ in outcomes)
                probabilities = tuple(float(probability) for _, probability in outcomes)
                children = tuple(build(state.child(action)) for action in actions)
                nodes[node_id] = TreeNode(
                    player=CHANCE_PLAYER,
                    actions=actions,
                    children=children,
                    chance_probabilities=probabilities,
                )
                return node_id

            if player not in (0, 1):
                raise ValueError(f"Invalid player id: {player}")

            actions = state.legal_actions()
            if not actions:
                raise ValueError("Decision node has no legal actions")
            information_set = state.information_state_key(player)
            known_actions = infoset_actions.get(information_set)
            if known_actions is None:
                infoset_actions[information_set] = actions
            elif known_actions != actions:
                raise ValueError(
                    "All states in an information set must have identical legal actions: "
                    f"{information_set!r}"
                )

            infoset_nodes_mutable.setdefault(information_set, []).append(node_id)
            children = tuple(build(state.child(action)) for action in actions)
            nodes[node_id] = TreeNode(
                player=player,
                actions=actions,
                children=children,
                information_set=information_set,
            )
            return node_id

        root = build(root_state)
        return cls(
            nodes=nodes,
            root=root,
            information_set_nodes={
                key: tuple(value) for key, value in infoset_nodes_mutable.items()
            },
            information_set_actions=infoset_actions,
        )

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def information_set_count(self) -> int:
        return len(self.information_set_nodes)


@dataclass(slots=True)
class InformationSetData:
    actions: tuple[Action, ...]
    regrets: list[float] = field(default_factory=list)
    strategy_sum: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.regrets:
            self.regrets = [0.0] * len(self.actions)
        if not self.strategy_sum:
            self.strategy_sum = [0.0] * len(self.actions)
        if len(self.regrets) != len(self.actions):
            raise ValueError("regret vector length does not match action count")
        if len(self.strategy_sum) != len(self.actions):
            raise ValueError("strategy-sum vector length does not match action count")


Strategy = dict[str, dict[Action, float]]


class ReferenceCFRTrainer:
    """Full-tree CFR or CFR+ trainer.

    The strategy is frozen within each iteration so all counterfactual values
    are computed against one coherent profile.  Both players' regrets are then
    updated from that same profile.
    """

    def __init__(
        self,
        tree: GameTree,
        *,
        variant: str = "cfr+",
        averaging_delay: int = 0,
    ) -> None:
        normalized_variant = variant.lower().replace("_", "").replace("-", "")
        if normalized_variant not in {"cfr", "cfr+", "cfrplus"}:
            raise ValueError("variant must be 'cfr' or 'cfr+'")
        self.variant = "cfr+" if normalized_variant != "cfr" else "cfr"
        self.averaging_delay = max(0, int(averaging_delay))
        self.tree = tree
        self.iteration = 0
        self.information_sets: dict[str, InformationSetData] = {
            key: InformationSetData(actions=actions)
            for key, actions in tree.information_set_actions.items()
        }

    @staticmethod
    def _regret_matching(regrets: Sequence[float]) -> tuple[float, ...]:
        positive = [max(0.0, value) for value in regrets]
        normalizer = fsum(positive)
        if normalizer > 0.0:
            return tuple(value / normalizer for value in positive)
        probability = 1.0 / len(regrets)
        return tuple(probability for _ in regrets)

    def _frozen_strategy(
        self,
        information_set: str,
        cache: dict[str, tuple[float, ...]],
    ) -> tuple[float, ...]:
        strategy = cache.get(information_set)
        if strategy is None:
            strategy = self._regret_matching(
                self.information_sets[information_set].regrets
            )
            cache[information_set] = strategy
        return strategy

    def _traverse(
        self,
        node_id: int,
        *,
        update_player: int,
        reach_player_0: float,
        reach_player_1: float,
        chance_reach: float,
        frozen_policy: dict[str, tuple[float, ...]],
        average_seen: set[str],
        average_weight: float,
        accumulate_average: bool,
    ) -> float:
        node = self.tree.nodes[node_id]

        if node.player == TERMINAL_PLAYER:
            return (
                node.utility_player_0
                if update_player == 0
                else -node.utility_player_0
            )

        if node.player == CHANCE_PLAYER:
            return fsum(
                probability
                * self._traverse(
                    child,
                    update_player=update_player,
                    reach_player_0=reach_player_0,
                    reach_player_1=reach_player_1,
                    chance_reach=chance_reach * probability,
                    frozen_policy=frozen_policy,
                    average_seen=average_seen,
                    average_weight=average_weight,
                    accumulate_average=accumulate_average,
                )
                for child, probability in zip(
                    node.children, node.chance_probabilities, strict=True
                )
            )

        assert node.information_set is not None
        strategy = self._frozen_strategy(node.information_set, frozen_policy)
        info_data = self.information_sets[node.information_set]

        if accumulate_average and node.information_set not in average_seen:
            average_seen.add(node.information_set)
            own_reach = reach_player_0 if node.player == 0 else reach_player_1
            weighted_reach = average_weight * own_reach
            if weighted_reach:
                for index, probability in enumerate(strategy):
                    info_data.strategy_sum[index] += weighted_reach * probability

        action_values: list[float] = []
        for index, child in enumerate(node.children):
            if node.player == 0:
                child_reach_0 = reach_player_0 * strategy[index]
                child_reach_1 = reach_player_1
            else:
                child_reach_0 = reach_player_0
                child_reach_1 = reach_player_1 * strategy[index]

            action_values.append(
                self._traverse(
                    child,
                    update_player=update_player,
                    reach_player_0=child_reach_0,
                    reach_player_1=child_reach_1,
                    chance_reach=chance_reach,
                    frozen_policy=frozen_policy,
                    average_seen=average_seen,
                    average_weight=average_weight,
                    accumulate_average=accumulate_average,
                )
            )

        node_value = fsum(
            probability * value
            for probability, value in zip(strategy, action_values, strict=True)
        )

        if node.player == update_player:
            opponent_reach = (
                reach_player_1 if update_player == 0 else reach_player_0
            )
            counterfactual_reach = chance_reach * opponent_reach
            for index, action_value in enumerate(action_values):
                info_data.regrets[index] += counterfactual_reach * (
                    action_value - node_value
                )

        return node_value

    def train(self, iterations: int) -> "ReferenceCFRTrainer":
        if iterations < 0:
            raise ValueError("iterations must be non-negative")

        for _ in range(iterations):
            self.iteration += 1
            frozen_policy: dict[str, tuple[float, ...]] = {}
            average_seen: set[str] = set()
            if self.variant == "cfr+":
                average_weight = float(
                    max(0, self.iteration - self.averaging_delay)
                )
            else:
                average_weight = 1.0

            self._traverse(
                self.tree.root,
                update_player=0,
                reach_player_0=1.0,
                reach_player_1=1.0,
                chance_reach=1.0,
                frozen_policy=frozen_policy,
                average_seen=average_seen,
                average_weight=average_weight,
                accumulate_average=True,
            )
            self._traverse(
                self.tree.root,
                update_player=1,
                reach_player_0=1.0,
                reach_player_1=1.0,
                chance_reach=1.0,
                frozen_policy=frozen_policy,
                average_seen=average_seen,
                average_weight=average_weight,
                accumulate_average=False,
            )

            if self.variant == "cfr+":
                for info_data in self.information_sets.values():
                    for index, regret in enumerate(info_data.regrets):
                        if regret < 0.0:
                            info_data.regrets[index] = 0.0

        return self

    def current_strategy(self) -> Strategy:
        output: Strategy = {}
        for key, info_data in self.information_sets.items():
            probabilities = self._regret_matching(info_data.regrets)
            output[key] = {
                action: probability
                for action, probability in zip(
                    info_data.actions, probabilities, strict=True
                )
            }
        return output

    def average_strategy(self) -> Strategy:
        output: Strategy = {}
        for key, info_data in self.information_sets.items():
            normalizer = fsum(info_data.strategy_sum)
            if normalizer > 0.0:
                probabilities = tuple(
                    value / normalizer for value in info_data.strategy_sum
                )
            else:
                probabilities = self._regret_matching(info_data.regrets)
            output[key] = {
                action: probability
                for action, probability in zip(
                    info_data.actions, probabilities, strict=True
                )
            }
        return output


def _probabilities_for_node(
    node: TreeNode,
    strategy: Mapping[str, Mapping[Action, float]],
) -> tuple[float, ...]:
    assert node.information_set is not None
    action_probabilities = strategy.get(node.information_set)
    if action_probabilities is None:
        probability = 1.0 / len(node.actions)
        return tuple(probability for _ in node.actions)

    probabilities = tuple(
        max(0.0, float(action_probabilities.get(action, 0.0)))
        for action in node.actions
    )
    normalizer = fsum(probabilities)
    if normalizer <= 0.0:
        probability = 1.0 / len(node.actions)
        return tuple(probability for _ in node.actions)
    return tuple(value / normalizer for value in probabilities)


def expected_value(
    tree: GameTree,
    strategy: Mapping[str, Mapping[Action, float]],
    *,
    player: int = 0,
) -> float:
    """Compute exact expected value of a complete strategy profile."""

    if player not in (0, 1):
        raise ValueError("player must be 0 or 1")

    @lru_cache(maxsize=None)
    def value(node_id: int) -> float:
        node = tree.nodes[node_id]
        if node.player == TERMINAL_PLAYER:
            return node.utility_player_0 if player == 0 else -node.utility_player_0
        if node.player == CHANCE_PLAYER:
            return fsum(
                probability * value(child)
                for child, probability in zip(
                    node.children, node.chance_probabilities, strict=True
                )
            )
        probabilities = _probabilities_for_node(node, strategy)
        return fsum(
            probability * value(child)
            for probability, child in zip(
                probabilities, node.children, strict=True
            )
        )

    return value(tree.root)


@dataclass(frozen=True, slots=True)
class BestResponseResult:
    player: int
    value: float
    actions: dict[str, Action]


def best_response(
    tree: GameTree,
    strategy: Mapping[str, Mapping[Action, float]],
    *,
    player: int,
) -> BestResponseResult:
    """Compute an exact pure best response against the opponent's strategy.

    Histories in the same information set are aggregated using counterfactual
    reach probabilities, which enforces one consistent action per information
    set rather than granting the responder access to hidden cards.
    """

    if player not in (0, 1):
        raise ValueError("player must be 0 or 1")
    opponent = 1 - player

    counterfactual_reach = [0.0] * tree.node_count
    counterfactual_reach[tree.root] = 1.0

    def propagate(node_id: int) -> None:
        node = tree.nodes[node_id]
        reach = counterfactual_reach[node_id]
        if node.player == TERMINAL_PLAYER:
            return
        if node.player == CHANCE_PLAYER:
            for child, probability in zip(
                node.children, node.chance_probabilities, strict=True
            ):
                counterfactual_reach[child] = reach * probability
                propagate(child)
            return
        if node.player == player:
            for child in node.children:
                # Exclude the responding player's own reach probability.
                counterfactual_reach[child] = reach
                propagate(child)
            return

        assert node.player == opponent
        probabilities = _probabilities_for_node(node, strategy)
        for child, probability in zip(node.children, probabilities, strict=True):
            counterfactual_reach[child] = reach * probability
            propagate(child)

    propagate(tree.root)

    chosen_action_index: dict[str, int] = {}
    chosen_action: dict[str, Action] = {}
    value_cache: dict[int, float] = {}
    choosing: set[str] = set()

    def value(node_id: int) -> float:
        cached = value_cache.get(node_id)
        if cached is not None:
            return cached

        node = tree.nodes[node_id]
        if node.player == TERMINAL_PLAYER:
            result = (
                node.utility_player_0 if player == 0 else -node.utility_player_0
            )
        elif node.player == CHANCE_PLAYER:
            result = fsum(
                probability * value(child)
                for child, probability in zip(
                    node.children, node.chance_probabilities, strict=True
                )
            )
        elif node.player == opponent:
            probabilities = _probabilities_for_node(node, strategy)
            result = fsum(
                probability * value(child)
                for probability, child in zip(
                    probabilities, node.children, strict=True
                )
            )
        else:
            assert node.information_set is not None
            information_set = node.information_set
            if information_set not in chosen_action_index:
                if information_set in choosing:
                    raise ValueError(
                        "Best-response recursion encountered an information-set cycle; "
                        "the game may not have perfect recall"
                    )
                choosing.add(information_set)
                member_nodes = tree.information_set_nodes[information_set]
                action_scores: list[float] = []
                for action_index in range(len(node.actions)):
                    action_scores.append(
                        fsum(
                            counterfactual_reach[member_node]
                            * value(
                                tree.nodes[member_node].children[action_index]
                            )
                            for member_node in member_nodes
                        )
                    )
                best_index = max(
                    range(len(action_scores)), key=action_scores.__getitem__
                )
                chosen_action_index[information_set] = best_index
                chosen_action[information_set] = node.actions[best_index]
                choosing.remove(information_set)
            result = value(node.children[chosen_action_index[information_set]])

        value_cache[node_id] = result
        return result

    return BestResponseResult(
        player=player,
        value=value(tree.root),
        actions=chosen_action,
    )


@dataclass(frozen=True, slots=True)
class Evaluation:
    profile_value_player_0: float
    best_response_value_player_0: float
    best_response_value_player_1: float
    nash_conv: float
    exploitability: float

    def as_dict(self) -> dict[str, float]:
        return {
            "profile_value_player_0": self.profile_value_player_0,
            "best_response_value_player_0": self.best_response_value_player_0,
            "best_response_value_player_1": self.best_response_value_player_1,
            "nash_conv": self.nash_conv,
            "exploitability": self.exploitability,
        }


def evaluate_strategy(
    tree: GameTree,
    strategy: Mapping[str, Mapping[Action, float]],
) -> Evaluation:
    """Return profile value, two exact best responses, NashConv, exploitability."""

    profile_value_0 = expected_value(tree, strategy, player=0)
    profile_value_1 = -profile_value_0
    response_0 = best_response(tree, strategy, player=0)
    response_1 = best_response(tree, strategy, player=1)
    nash_conv = (response_0.value - profile_value_0) + (
        response_1.value - profile_value_1
    )
    # Small negative values can appear from floating-point cancellation.
    nash_conv = max(0.0, nash_conv)
    return Evaluation(
        profile_value_player_0=profile_value_0,
        best_response_value_player_0=response_0.value,
        best_response_value_player_1=response_1.value,
        nash_conv=nash_conv,
        exploitability=nash_conv / 2.0,
    )
