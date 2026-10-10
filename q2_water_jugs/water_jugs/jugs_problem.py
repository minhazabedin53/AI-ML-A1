"""The three-jug problem as an AIMA search Problem.

State       (a, b, c) - gallons currently in the 12-, 8- and 3-gallon jugs
Initial     (0, 0, 0) - all jugs empty
Goal        any state in which some jug holds exactly 1 gallon
Actions     ('Fill', i)     fill jug i from the faucet          (if not full)
            ('Empty', i)    pour jug i onto the ground          (if not empty)
            ('Pour', i, j)  pour jug i into jug j until i is empty or j is full
                            (if i is not empty and j is not full)
Transition  Fill:  s[i] = cap[i]
            Empty: s[i] = 0
            Pour:  t = min(s[i], cap[j] - s[j]);  s[i] -= t;  s[j] += t
Cost        1 per action

Capacities, goal amount and initial state are parameters so the same code
can be tested on other jug puzzles.
"""

from __future__ import annotations

from typing import Optional, Sequence

from .search import Node, Problem, breadth_first_search, expand

State = tuple[int, ...]


class WaterJugsProblem(Problem):

    def __init__(self, capacities: Sequence[int] = (12, 8, 3), goal: int = 1,
                 initial: Optional[Sequence[int]] = None):
        capacities = tuple(int(c) for c in capacities)
        if not capacities or any(c <= 0 for c in capacities):
            raise ValueError("capacities must be positive integers")
        initial = tuple(0 for _ in capacities) if initial is None else tuple(initial)
        if len(initial) != len(capacities) or any(
                not 0 <= x <= c for x, c in zip(initial, capacities)):
            raise ValueError("initial state does not fit the jug capacities")
        if goal < 0:
            raise ValueError("goal amount must be non-negative")
        super().__init__(initial=initial, goal=goal, capacities=capacities)

    # ------------------------------------------------------------------ model
    def actions(self, state: State) -> list[tuple]:
        cap = self.capacities
        n = len(cap)
        acts: list[tuple] = []
        acts += [("Fill", i) for i in range(n) if state[i] < cap[i]]
        acts += [("Empty", i) for i in range(n) if state[i] > 0]
        acts += [("Pour", i, j) for i in range(n) for j in range(n)
                 if i != j and state[i] > 0 and state[j] < cap[j]]
        return acts

    def result(self, state: State, action: tuple) -> State:
        s = list(state)
        kind = action[0]
        if kind == "Fill":
            s[action[1]] = self.capacities[action[1]]
        elif kind == "Empty":
            s[action[1]] = 0
        elif kind == "Pour":
            i, j = action[1], action[2]
            amount = min(s[i], self.capacities[j] - s[j])
            s[i] -= amount
            s[j] += amount
        else:
            raise ValueError(f"Unknown action {action!r}")
        return tuple(s)

    def is_goal(self, state: State) -> bool:
        return self.goal in state

    # -------------------------------------------------------------- heuristic
    def h(self, node: Node) -> int:
        """Informal heuristic from the written answer (not needed by BFS):
        0 if a jug already holds the goal amount, 1 if a single action can
        produce it, otherwise 2.  It never overestimates (admissible)."""
        if self.is_goal(node.state):
            return 0
        if any(self.is_goal(child.state) for child in expand(self, node)):
            return 1
        return 2

    # ------------------------------------------------------------ utilities
    def describe(self, action: tuple) -> str:
        cap = self.capacities
        kind = action[0]
        if kind == "Fill":
            return f"Fill the {cap[action[1]]}-gal jug from the faucet"
        if kind == "Empty":
            return f"Empty the {cap[action[1]]}-gal jug onto the ground"
        return f"Pour the {cap[action[1]]}-gal jug into the {cap[action[2]]}-gal jug"

    def reachable_states(self) -> set[State]:
        """Every state reachable from the initial state (size of the space)."""
        seen = {self.initial}
        frontier = [self.initial]
        while frontier:
            s = frontier.pop()
            for a in self.actions(s):
                s1 = self.result(s, a)
                if s1 not in seen:
                    seen.add(s1)
                    frontier.append(s1)
        return seen


def solve(capacities=(12, 8, 3), goal=1, initial=None) -> Node:
    return breadth_first_search(WaterJugsProblem(capacities, goal, initial))
