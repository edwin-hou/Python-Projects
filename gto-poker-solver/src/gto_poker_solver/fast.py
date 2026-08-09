"""NumPy-accelerated full-tree CFR and CFR+ training."""

from __future__ import annotations

import numpy as np

from .core import CHANCE_PLAYER, TERMINAL_PLAYER, GameTree, Strategy


class CFRTrainer:
    """Vectorized full-tree CFR/CFR+ trainer.

    The trainer computes the same simultaneous full-tree updates as the small
    reference implementation in :mod:`gto_poker_solver.core`.  Static game-tree
    data is converted into padded NumPy arrays once, after which each iteration
    consists of:

    1. regret matching at every information set,
    2. a top-down reach-probability pass,
    3. a bottom-up expected-value pass, and
    4. vectorized counterfactual-regret accumulation.
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

        self.information_set_keys = list(tree.information_set_actions)
        self._information_set_id = {
            key: index for index, key in enumerate(self.information_set_keys)
        }
        self.actions = [
            tree.information_set_actions[key]
            for key in self.information_set_keys
        ]
        self.information_set_count = len(self.information_set_keys)
        self.max_actions = max(len(node.actions) for node in tree.nodes)
        self._action_indices = np.arange(self.max_actions)

        self._action_count = np.fromiter(
            (len(actions) for actions in self.actions),
            dtype=np.int16,
            count=self.information_set_count,
        )
        self._action_mask = np.zeros(
            (self.information_set_count, self.max_actions), dtype=np.float64
        )
        for index, action_count in enumerate(self._action_count):
            self._action_mask[index, :action_count] = 1.0

        self.regrets = np.zeros_like(self._action_mask)
        self.strategy_sum = np.zeros_like(self._action_mask)

        node_count = tree.node_count
        self._player = np.empty(node_count, dtype=np.int8)
        self._node_information_set = np.full(node_count, -1, dtype=np.int32)
        self._node_action_count = np.zeros(node_count, dtype=np.int16)
        self._children = np.zeros(
            (node_count, self.max_actions), dtype=np.int32
        )
        self._chance_probabilities = np.zeros(
            (node_count, self.max_actions), dtype=np.float64
        )
        self._terminal_utility_player_0 = np.zeros(node_count, dtype=np.float64)
        self._parent = np.full(node_count, -1, dtype=np.int32)
        self._parent_branch = np.full(node_count, -1, dtype=np.int16)
        self._depth = np.zeros(node_count, dtype=np.int16)

        for node_id, node in enumerate(tree.nodes):
            self._player[node_id] = node.player
            self._node_action_count[node_id] = len(node.actions)

            if node.information_set is not None:
                self._node_information_set[node_id] = self._information_set_id[
                    node.information_set
                ]

            if node.children:
                child_count = len(node.children)
                self._children[node_id, :child_count] = node.children
                for branch, child in enumerate(node.children):
                    self._parent[child] = node_id
                    self._parent_branch[child] = branch
                    self._depth[child] = self._depth[node_id] + 1

            if node.chance_probabilities:
                probability_count = len(node.chance_probabilities)
                self._chance_probabilities[
                    node_id, :probability_count
                ] = node.chance_probabilities

            if node.player == TERMINAL_PLAYER:
                self._terminal_utility_player_0[
                    node_id
                ] = node.utility_player_0

        self._max_depth = int(self._depth.max())
        self._nodes_by_depth = [
            np.flatnonzero(self._depth == depth)
            for depth in range(self._max_depth + 1)
        ]
        self._nonterminal_nodes_by_depth = [
            node_ids[self._player[node_ids] != TERMINAL_PLAYER]
            for node_ids in self._nodes_by_depth
        ]
        self._player_0_nodes = np.flatnonzero(self._player == 0)
        self._player_1_nodes = np.flatnonzero(self._player == 1)

        representative_node = np.fromiter(
            (
                tree.information_set_nodes[key][0]
                for key in self.information_set_keys
            ),
            dtype=np.int32,
            count=self.information_set_count,
        )
        self._representative_node = representative_node
        self._information_set_player = self._player[representative_node]

        # Reused working memory.
        self._reach_player_0 = np.empty(node_count, dtype=np.float64)
        self._reach_player_1 = np.empty(node_count, dtype=np.float64)
        self._chance_reach = np.empty(node_count, dtype=np.float64)
        self._values_player_0 = np.empty(node_count, dtype=np.float64)

    def _strategy_matrix(self) -> np.ndarray:
        positive_regret = np.maximum(self.regrets, 0.0) * self._action_mask
        normalizer = positive_regret.sum(axis=1, keepdims=True)
        strategy = np.divide(
            positive_regret,
            normalizer,
            out=np.zeros_like(positive_regret),
            where=normalizer > 0.0,
        )

        uniform_rows = normalizer[:, 0] <= 0.0
        if np.any(uniform_rows):
            strategy[uniform_rows] = (
                self._action_mask[uniform_rows]
                / self._action_count[uniform_rows, None]
            )
        return strategy

    def _compute_reach_probabilities(self, strategy: np.ndarray) -> None:
        reach_0 = self._reach_player_0
        reach_1 = self._reach_player_1
        chance_reach = self._chance_reach
        reach_0.fill(0.0)
        reach_1.fill(0.0)
        chance_reach.fill(0.0)
        reach_0[self.tree.root] = 1.0
        reach_1[self.tree.root] = 1.0
        chance_reach[self.tree.root] = 1.0

        for depth in range(1, self._max_depth + 1):
            node_ids = self._nodes_by_depth[depth]
            parents = self._parent[node_ids]
            branches = self._parent_branch[node_ids]
            parent_players = self._player[parents]

            branch_strategy = np.ones(len(node_ids), dtype=np.float64)
            decision_mask = (parent_players == 0) | (parent_players == 1)
            if np.any(decision_mask):
                decision_parents = parents[decision_mask]
                decision_branches = branches[decision_mask]
                branch_strategy[decision_mask] = strategy[
                    self._node_information_set[decision_parents],
                    decision_branches,
                ]

            chance_factor = np.ones(len(node_ids), dtype=np.float64)
            chance_mask = parent_players == CHANCE_PLAYER
            if np.any(chance_mask):
                chance_parents = parents[chance_mask]
                chance_branches = branches[chance_mask]
                chance_factor[chance_mask] = self._chance_probabilities[
                    chance_parents, chance_branches
                ]

            reach_0[node_ids] = reach_0[parents] * np.where(
                parent_players == 0, branch_strategy, 1.0
            )
            reach_1[node_ids] = reach_1[parents] * np.where(
                parent_players == 1, branch_strategy, 1.0
            )
            chance_reach[node_ids] = chance_reach[parents] * chance_factor

    def _compute_profile_values(self, strategy: np.ndarray) -> None:
        values = self._values_player_0
        values[:] = self._terminal_utility_player_0

        for depth in range(self._max_depth - 1, -1, -1):
            node_ids = self._nonterminal_nodes_by_depth[depth]
            if len(node_ids) == 0:
                continue

            players = self._player[node_ids]
            action_counts = self._node_action_count[node_ids]
            valid_action = (
                self._action_indices[None, :] < action_counts[:, None]
            )
            weights = np.zeros(
                (len(node_ids), self.max_actions), dtype=np.float64
            )

            chance_mask = players == CHANCE_PLAYER
            if np.any(chance_mask):
                weights[chance_mask] = self._chance_probabilities[
                    node_ids[chance_mask]
                ]

            decision_mask = ~chance_mask
            if np.any(decision_mask):
                decision_nodes = node_ids[decision_mask]
                weights[decision_mask] = strategy[
                    self._node_information_set[decision_nodes]
                ]

            child_values = values[self._children[node_ids]]
            values[node_ids] = (
                weights * child_values * valid_action
            ).sum(axis=1)

    def _accumulate_average_strategy(
        self,
        strategy: np.ndarray,
        average_weight: float,
    ) -> None:
        if average_weight <= 0.0:
            return

        own_reach = np.where(
            self._information_set_player == 0,
            self._reach_player_0[self._representative_node],
            self._reach_player_1[self._representative_node],
        )
        self.strategy_sum += (
            average_weight
            * own_reach[:, None]
            * strategy
            * self._action_mask
        )

    def _accumulate_regret_for_player(self, player: int) -> None:
        if player == 0:
            node_ids = self._player_0_nodes
            counterfactual_reach = (
                self._chance_reach[node_ids]
                * self._reach_player_1[node_ids]
            )
        elif player == 1:
            node_ids = self._player_1_nodes
            counterfactual_reach = (
                self._chance_reach[node_ids]
                * self._reach_player_0[node_ids]
            )
        else:
            raise ValueError("player must be 0 or 1")

        information_set_ids = self._node_information_set[node_ids]
        action_counts = self._node_action_count[node_ids]
        valid_action = self._action_indices[None, :] < action_counts[:, None]
        child_values = self._values_player_0[self._children[node_ids]]
        node_values = self._values_player_0[node_ids, None]

        if player == 0:
            advantage = child_values - node_values
        else:
            # Player 1's utility is the negative of player 0's utility.
            advantage = node_values - child_values

        increments = (
            counterfactual_reach[:, None] * advantage * valid_action
        )
        for action_index in range(self.max_actions):
            np.add.at(
                self.regrets[:, action_index],
                information_set_ids,
                increments[:, action_index],
            )

    def train(self, iterations: int) -> "CFRTrainer":
        if iterations < 0:
            raise ValueError("iterations must be non-negative")

        for _ in range(iterations):
            self.iteration += 1
            strategy = self._strategy_matrix()
            self._compute_reach_probabilities(strategy)
            self._compute_profile_values(strategy)

            if self.variant == "cfr+":
                average_weight = float(
                    max(0, self.iteration - self.averaging_delay)
                )
            else:
                average_weight = 1.0
            self._accumulate_average_strategy(strategy, average_weight)

            self._accumulate_regret_for_player(0)
            self._accumulate_regret_for_player(1)
            if self.variant == "cfr+":
                np.maximum(self.regrets, 0.0, out=self.regrets)

        return self

    def average_strategy(self) -> Strategy:
        normalizer = self.strategy_sum.sum(axis=1, keepdims=True)
        probabilities = np.divide(
            self.strategy_sum,
            normalizer,
            out=np.zeros_like(self.strategy_sum),
            where=normalizer > 0.0,
        )
        missing_average = normalizer[:, 0] <= 0.0
        if np.any(missing_average):
            probabilities[missing_average] = self._strategy_matrix()[
                missing_average
            ]
        return self._to_strategy_dict(probabilities)

    def current_strategy(self) -> Strategy:
        return self._to_strategy_dict(self._strategy_matrix())

    def _to_strategy_dict(self, probabilities: np.ndarray) -> Strategy:
        output: Strategy = {}
        for information_set_id, key in enumerate(self.information_set_keys):
            output[key] = {
                action: float(probabilities[information_set_id, action_index])
                for action_index, action in enumerate(
                    self.actions[information_set_id]
                )
            }
        return output
