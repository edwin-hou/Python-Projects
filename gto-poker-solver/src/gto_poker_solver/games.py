"""Finite imperfect-information poker games used by the solver."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import ClassVar

from .core import Action, CHANCE_PLAYER, TERMINAL_PLAYER

_RANK_NAMES = ("J", "Q", "K")


@dataclass(frozen=True, slots=True)
class KuhnPokerState:
    """Canonical three-card Kuhn Poker.

    Both players ante one chip.  Player 0 acts first.  There is one possible
    one-chip bet and no raise.
    """

    cards: tuple[int | None, int | None] = (None, None)
    history: str = ""

    TERMINAL_HISTORIES: ClassVar[frozenset[str]] = frozenset(
        {"cc", "bc", "bf", "cbc", "cbf"}
    )

    @property
    def current_player(self) -> int:
        if self.history in self.TERMINAL_HISTORIES:
            return TERMINAL_PLAYER
        if self.cards[0] is None or self.cards[1] is None:
            return CHANCE_PLAYER
        if self.history == "":
            return 0
        if self.history in {"c", "b"}:
            return 1
        if self.history == "cb":
            return 0
        raise ValueError(f"Invalid Kuhn history: {self.history!r}")

    def chance_outcomes(self) -> tuple[tuple[Action, float], ...]:
        if self.current_player != CHANCE_PLAYER:
            return ()
        used = {card for card in self.cards if card is not None}
        remaining = tuple(card for card in range(3) if card not in used)
        probability = 1.0 / len(remaining)
        return tuple((card, probability) for card in remaining)

    def legal_actions(self) -> tuple[Action, ...]:
        if self.history in {"", "c"}:
            return ("check", "bet")
        if self.history in {"b", "cb"}:
            return ("fold", "call")
        return ()

    def child(self, action: Action) -> "KuhnPokerState":
        if self.current_player == CHANCE_PLAYER:
            if not isinstance(action, int):
                raise ValueError("Chance action must be a card id")
            cards = list(self.cards)
            seat = 0 if cards[0] is None else 1
            if action in cards:
                raise ValueError("Card already dealt")
            cards[seat] = action
            return replace(self, cards=(cards[0], cards[1]))

        transitions = {
            ("", "check"): "c",
            ("", "bet"): "b",
            ("c", "check"): "cc",
            ("c", "bet"): "cb",
            ("b", "fold"): "bf",
            ("b", "call"): "bc",
            ("cb", "fold"): "cbf",
            ("cb", "call"): "cbc",
        }
        try:
            next_history = transitions[(self.history, action)]
        except KeyError as exc:
            raise ValueError(
                f"Illegal action {action!r} at history {self.history!r}"
            ) from exc
        return replace(self, history=next_history)

    def information_state_key(self, player: int) -> str:
        card = self.cards[player]
        if card is None:
            raise ValueError("Information state requested before private deal")
        return f"Kuhn|P{player}|card={_RANK_NAMES[card]}|history={self.history or '-'}"

    def utility(self, player: int) -> float:
        if self.current_player != TERMINAL_PLAYER:
            raise ValueError("Utility requested for non-terminal state")
        assert self.cards[0] is not None and self.cards[1] is not None

        if self.history == "bf":
            utility_0 = 1.0
        elif self.history == "cbf":
            utility_0 = -1.0
        else:
            player_0_wins = self.cards[0] > self.cards[1]
            magnitude = 1.0 if self.history == "cc" else 2.0
            utility_0 = magnitude if player_0_wins else -magnitude
        return utility_0 if player == 0 else -utility_0


@dataclass(frozen=True, slots=True)
class OneCardPokerState:
    """Configurable one-card river abstraction.

    Each player receives a distinct rank.  Higher rank wins at showdown.  The
    current pot is treated as jointly owned, so a showdown without betting is
    worth ``pot / 2`` to the winner; a called bet is worth ``pot / 2 + bet``.
    The betting tree is check/bet, check-back or bet, and fold/call.
    """

    rank_count: int = 13
    pot: float = 100.0
    bet: float = 75.0
    cards: tuple[int | None, int | None] = (None, None)
    history: str = ""

    TERMINAL_HISTORIES: ClassVar[frozenset[str]] = KuhnPokerState.TERMINAL_HISTORIES

    def __post_init__(self) -> None:
        if self.rank_count < 3:
            raise ValueError("rank_count must be at least 3")
        if self.pot <= 0.0:
            raise ValueError("pot must be positive")
        if self.bet <= 0.0:
            raise ValueError("bet must be positive")

    @property
    def current_player(self) -> int:
        if self.history in self.TERMINAL_HISTORIES:
            return TERMINAL_PLAYER
        if self.cards[0] is None or self.cards[1] is None:
            return CHANCE_PLAYER
        if self.history == "":
            return 0
        if self.history in {"c", "b"}:
            return 1
        if self.history == "cb":
            return 0
        raise ValueError(f"Invalid one-card history: {self.history!r}")

    def chance_outcomes(self) -> tuple[tuple[Action, float], ...]:
        if self.current_player != CHANCE_PLAYER:
            return ()
        used = {card for card in self.cards if card is not None}
        remaining = tuple(card for card in range(self.rank_count) if card not in used)
        probability = 1.0 / len(remaining)
        return tuple((card, probability) for card in remaining)

    def legal_actions(self) -> tuple[Action, ...]:
        if self.history in {"", "c"}:
            return ("check", "bet")
        if self.history in {"b", "cb"}:
            return ("fold", "call")
        return ()

    def child(self, action: Action) -> "OneCardPokerState":
        if self.current_player == CHANCE_PLAYER:
            if not isinstance(action, int):
                raise ValueError("Chance action must be a rank")
            cards = list(self.cards)
            seat = 0 if cards[0] is None else 1
            if action in cards or not 0 <= action < self.rank_count:
                raise ValueError("Invalid dealt rank")
            cards[seat] = action
            return replace(self, cards=(cards[0], cards[1]))

        transitions = {
            ("", "check"): "c",
            ("", "bet"): "b",
            ("c", "check"): "cc",
            ("c", "bet"): "cb",
            ("b", "fold"): "bf",
            ("b", "call"): "bc",
            ("cb", "fold"): "cbf",
            ("cb", "call"): "cbc",
        }
        try:
            next_history = transitions[(self.history, action)]
        except KeyError as exc:
            raise ValueError(
                f"Illegal action {action!r} at history {self.history!r}"
            ) from exc
        return replace(self, history=next_history)

    def information_state_key(self, player: int) -> str:
        card = self.cards[player]
        if card is None:
            raise ValueError("Information state requested before private deal")
        return (
            f"OneCard|P{player}|rank={card + 1}/{self.rank_count}"
            f"|history={self.history or '-'}"
        )

    def utility(self, player: int) -> float:
        if self.current_player != TERMINAL_PLAYER:
            raise ValueError("Utility requested for non-terminal state")
        assert self.cards[0] is not None and self.cards[1] is not None
        base_value = self.pot / 2.0

        if self.history == "bf":
            utility_0 = base_value
        elif self.history == "cbf":
            utility_0 = -base_value
        else:
            player_0_wins = self.cards[0] > self.cards[1]
            magnitude = base_value if self.history == "cc" else base_value + self.bet
            utility_0 = magnitude if player_0_wins else -magnitude
        return utility_0 if player == 0 else -utility_0


@dataclass(frozen=True, slots=True)
class LeducHoldemState:
    """Heads-up fixed-limit Leduc Hold'em.

    Deck: J, J, Q, Q, K, K.  Each player antes 1 and receives one private card.
    One public card is dealt after the first betting round.  Bets are 2 chips
    before the public card and 4 chips afterward.  Up to two raises are allowed
    after an opening bet.  Player 0 acts first in both rounds.
    """

    private_cards: tuple[int | None, int | None] = (None, None)
    public_card: int | None = None
    stage: str = "deal_private_0"
    histories: tuple[str, ...] = ()
    acting_player: int = 0
    to_call: int = 0
    consecutive_checks: int = 0
    raises: int = 0
    contributions: tuple[int, int] = (1, 1)
    folded_player: int | None = None
    max_raises: int = 2

    @staticmethod
    def rank(card_id: int) -> int:
        return card_id // 2

    @property
    def current_player(self) -> int:
        if self.stage == "terminal":
            return TERMINAL_PLAYER
        if self.stage in {"deal_private_0", "deal_private_1", "deal_public"}:
            return CHANCE_PLAYER
        if self.stage in {"betting_0", "betting_1"}:
            return self.acting_player
        raise ValueError(f"Invalid Leduc stage: {self.stage!r}")

    @property
    def round_index(self) -> int:
        if self.stage in {"deal_private_0", "deal_private_1", "betting_0", "deal_public"}:
            return 0
        return 1

    @property
    def bet_size(self) -> int:
        return 2 if self.round_index == 0 else 4

    def chance_outcomes(self) -> tuple[tuple[Action, float], ...]:
        if self.current_player != CHANCE_PLAYER:
            return ()
        used = {
            card
            for card in (*self.private_cards, self.public_card)
            if card is not None
        }
        remaining = tuple(card for card in range(6) if card not in used)
        probability = 1.0 / len(remaining)
        return tuple((card, probability) for card in remaining)

    def legal_actions(self) -> tuple[Action, ...]:
        if self.current_player not in (0, 1):
            return ()
        if self.to_call == 0:
            return ("check", "bet")
        actions: tuple[Action, ...] = ("fold", "call")
        if self.raises < self.max_raises:
            actions += ("raise",)
        return actions

    def _append_history(self, token: str) -> tuple[str, ...]:
        if not self.histories:
            raise ValueError("Betting history is not initialized")
        updated = list(self.histories)
        updated[-1] += token
        return tuple(updated)

    def _finish_round(
        self,
        *,
        histories: tuple[str, ...],
        contributions: tuple[int, int] | None = None,
    ) -> "LeducHoldemState":
        contributions = contributions or self.contributions
        if self.stage == "betting_0":
            return replace(
                self,
                stage="deal_public",
                histories=histories,
                contributions=contributions,
                acting_player=0,
                to_call=0,
                consecutive_checks=0,
                raises=0,
            )
        return replace(
            self,
            stage="terminal",
            histories=histories,
            contributions=contributions,
            to_call=0,
            consecutive_checks=0,
        )

    def child(self, action: Action) -> "LeducHoldemState":
        if self.current_player == CHANCE_PLAYER:
            if not isinstance(action, int) or not 0 <= action < 6:
                raise ValueError("Chance action must be a valid card id")
            used = {
                card
                for card in (*self.private_cards, self.public_card)
                if card is not None
            }
            if action in used:
                raise ValueError("Card already dealt")

            if self.stage == "deal_private_0":
                return replace(
                    self,
                    private_cards=(action, None),
                    stage="deal_private_1",
                )
            if self.stage == "deal_private_1":
                return replace(
                    self,
                    private_cards=(self.private_cards[0], action),
                    stage="betting_0",
                    histories=("",),
                    acting_player=0,
                )
            if self.stage == "deal_public":
                return replace(
                    self,
                    public_card=action,
                    stage="betting_1",
                    histories=(*self.histories, ""),
                    acting_player=0,
                    to_call=0,
                    consecutive_checks=0,
                    raises=0,
                )
            raise ValueError(f"Unexpected chance stage: {self.stage}")

        if action not in self.legal_actions():
            raise ValueError(
                f"Illegal action {action!r} at {self.stage}, to_call={self.to_call}"
            )

        actor = self.acting_player
        opponent = 1 - actor
        contributions = list(self.contributions)

        if action == "check":
            histories = self._append_history("x")
            if self.consecutive_checks == 1:
                return self._finish_round(histories=histories)
            return replace(
                self,
                histories=histories,
                acting_player=opponent,
                consecutive_checks=1,
            )

        if action == "bet":
            contributions[actor] += self.bet_size
            return replace(
                self,
                histories=self._append_history("b"),
                acting_player=opponent,
                to_call=self.bet_size,
                consecutive_checks=0,
                contributions=(contributions[0], contributions[1]),
            )

        if action == "fold":
            return replace(
                self,
                stage="terminal",
                histories=self._append_history("f"),
                folded_player=actor,
                to_call=0,
            )

        if action == "call":
            contributions[actor] += self.to_call
            return self._finish_round(
                histories=self._append_history("c"),
                contributions=(contributions[0], contributions[1]),
            )

        assert action == "raise"
        contributions[actor] += self.to_call + self.bet_size
        return replace(
            self,
            histories=self._append_history("r"),
            acting_player=opponent,
            to_call=self.bet_size,
            consecutive_checks=0,
            raises=self.raises + 1,
            contributions=(contributions[0], contributions[1]),
        )

    def information_state_key(self, player: int) -> str:
        private_card = self.private_cards[player]
        if private_card is None:
            raise ValueError("Information state requested before private deal")
        private_rank = _RANK_NAMES[self.rank(private_card)]
        public_rank = (
            "-" if self.public_card is None else _RANK_NAMES[self.rank(self.public_card)]
        )
        history = "/".join(part or "-" for part in self.histories)
        return (
            f"Leduc|P{player}|private={private_rank}|public={public_rank}"
            f"|history={history}"
        )

    def utility(self, player: int) -> float:
        if self.current_player != TERMINAL_PLAYER:
            raise ValueError("Utility requested for non-terminal state")

        contribution_0, contribution_1 = self.contributions
        if self.folded_player is not None:
            utility_0 = (
                -float(contribution_0)
                if self.folded_player == 0
                else float(contribution_1)
            )
        else:
            assert self.public_card is not None
            assert self.private_cards[0] is not None
            assert self.private_cards[1] is not None
            public_rank = self.rank(self.public_card)
            rank_0 = self.rank(self.private_cards[0])
            rank_1 = self.rank(self.private_cards[1])
            strength_0 = (rank_0 == public_rank, rank_0)
            strength_1 = (rank_1 == public_rank, rank_1)
            if strength_0 > strength_1:
                utility_0 = float(contribution_1)
            elif strength_0 < strength_1:
                utility_0 = -float(contribution_0)
            else:
                pot = contribution_0 + contribution_1
                utility_0 = pot / 2.0 - contribution_0

        return utility_0 if player == 0 else -utility_0
