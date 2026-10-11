"""Ronda preflop finita. Estado público separado del reparto privado."""

import random
from dataclasses import dataclass
from functools import lru_cache

from .cards import DECK, evaluar_mano


@lru_cache(maxsize=8192)
def rank(cards):
    return evaluar_mano(cards)


@dataclass(frozen=True)
class Config:
    capital: int = 455
    hands: int = 50
    alpha: float = 0.9
    scenarios: int = 32
    raises: tuple = (10, 30)

    def __post_init__(self):
        if (
            any(
                type(x) is not int or x < 1
                for x in (self.capital, self.hands, self.scenarios)
            )
            or self.hands > 50
            or not 0 <= self.alpha < 1
        ):
            raise ValueError("Configuración inválida")
        if any(type(x) is not int or x <= 2 for x in self.raises):
            raise ValueError("Aumentos enteros mayores que la ciega")


@dataclass(frozen=True)
class Public:
    start: tuple
    paid: tuple
    actor: int
    small: int
    raised: bool = False
    steps: int = 0
    terminal: bool = False
    folded: int | None = None
    history: tuple = ()


@dataclass(frozen=True)
class Observation:
    public: Public
    own: tuple
    raises: tuple


def initial(start, small):
    paid = [0, 0]
    paid[small] = min(1, start[small])
    paid[1 - small] = min(2, start[1 - small])
    return Public(tuple(start), tuple(paid), small, small)


def legal(s, raises=(10, 30)):
    if s.terminal:
        return ()
    i = s.actor
    due = max(s.paid) - s.paid[i]
    actions = ["fold", "call"] if due else ["call"]
    cap = min(s.start)
    if not s.raised:
        for target in sorted(set(min(t, cap) for t in raises)):
            if target > max(s.paid):
                actions.append(f"raise:{target}")
    return tuple(actions)


def step(s, action, raises=(10, 30)):
    if action not in legal(s, raises):
        raise ValueError("Acción ilegal o mano cerrada")
    i = s.actor
    paid = list(s.paid)
    folded = None
    terminal = False
    raised = s.raised
    if action == "fold":
        folded = i
        terminal = True
    elif action == "call":
        paid[i] = min(s.start[i], max(paid))
        terminal = (
            s.raised or s.steps >= 1 or min(s.start[j] - paid[j] for j in (0, 1)) == 0
        )
    else:
        paid[i] = int(action.split(":")[1])
        raised = True
    return Public(
        s.start,
        tuple(paid),
        1 - i,
        s.small,
        raised,
        s.steps + 1,
        terminal,
        folded,
        s.history + ((i, action, tuple(paid)),),
    )


def settle(s, holes, board):
    if not s.terminal:
        raise ValueError("Mano no terminada")
    # Devolución de toda apuesta no cubierta antes de repartir el bote.
    matched = min(s.paid)
    out = [s.start[j] - matched for j in (0, 1)]
    if s.folded is not None:
        winner = 1 - s.folded
    else:
        a, b = (rank(tuple(h) + tuple(board)) for h in holes)
        winner = 0 if a > b else 1 if b > a else None
    if winner is None:
        out = [x + matched for x in out]
    else:
        out[winner] += 2 * matched
    return tuple(out)


def deal(seed, hand):
    # Stream exclusivo del reparto: no depende de decisiones o rollouts.
    deck = list(DECK)
    random.Random(f"deal-v1:{seed}:{hand}").shuffle(deck)
    return (tuple(deck[:2]), tuple(deck[2:4])), tuple(deck[4:9])
