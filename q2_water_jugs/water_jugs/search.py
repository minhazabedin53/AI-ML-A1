"""Search framework for Question 2.

Follows AIMA 4e, Chapter 3 and the structure of the aima-python reference
code (``search4e``):

* ``Problem``                - formal problem: initial, actions, result, is_goal, action_cost
* ``Node``                   - search-tree node: state, parent, action, path_cost
* ``expand``                 - EXPAND from Figure 3.7
* ``breadth_first_search``   - BREADTH-FIRST-SEARCH from Figure 3.9
* ``path_actions`` / ``path_states`` - recover the solution from a goal node
"""

from __future__ import annotations

import math
from collections import deque
from typing import Any, Hashable, Iterable, Iterator


class Problem:
    """Abstract formal problem.  Subclasses override ``actions`` and
    ``result`` and, if needed, ``is_goal``, ``action_cost`` and ``h``."""

    def __init__(self, initial: Hashable = None, goal: Any = None, **kwds):
        self.initial = initial
        self.goal = goal
        self.__dict__.update(kwds)

    def actions(self, state) -> Iterable:
        raise NotImplementedError

    def result(self, state, action):
        raise NotImplementedError

    def is_goal(self, state) -> bool:
        return state == self.goal

    def action_cost(self, s, action, s1) -> float:
        return 1

    def h(self, node: "Node") -> float:
        return 0

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.initial!r}, {self.goal!r})"


class Node:
    """A node in a search tree (AIMA 4e Section 3.3.2)."""

    def __init__(self, state, parent: "Node | None" = None, action=None,
                 path_cost: float = 0.0):
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost

    def __repr__(self) -> str:
        return f"<{self.state}>"

    def __len__(self) -> int:
        """Depth of the node (number of actions from the root)."""
        return 0 if self.parent is None else 1 + len(self.parent)

    def __lt__(self, other: "Node") -> bool:
        return self.path_cost < other.path_cost


# Special node returned when no solution exists (as in aima-python).
failure = Node("failure", path_cost=math.inf)


def expand(problem: Problem, node: Node) -> Iterator[Node]:
    """AIMA 4e Figure 3.7, EXPAND.

        function EXPAND(problem, node) yields nodes
            s <- node.STATE
            for each action in problem.ACTIONS(s) do
                s' <- problem.RESULT(s, action)
                cost <- node.PATH-COST + problem.ACTION-COST(s, action, s')
                yield NODE(STATE=s', PARENT=node, ACTION=action, PATH-COST=cost)
    """
    s = node.state
    for action in problem.actions(s):
        s1 = problem.result(s, action)
        cost = node.path_cost + problem.action_cost(s, action, s1)
        yield Node(s1, node, action, cost)


def path_actions(node: Node) -> list:
    """The sequence of actions to get to this node."""
    if node.parent is None:
        return []
    return path_actions(node.parent) + [node.action]


def path_states(node: Node) -> list:
    """The sequence of states to get to this node."""
    if node in (failure, None):
        return []
    return path_states(node.parent) + [node.state]


FIFOQueue = deque


def breadth_first_search(problem: Problem) -> Node:
    """AIMA 4e Figure 3.9, BREADTH-FIRST-SEARCH.

        function BREADTH-FIRST-SEARCH(problem) returns a solution node or failure
            node <- NODE(problem.INITIAL)
            if problem.IS-GOAL(node.STATE) then return node
            frontier <- a FIFO queue, with node as an element
            reached  <- {problem.INITIAL}
            while not IS-EMPTY(frontier) do
                node <- POP(frontier)
                for each child in EXPAND(problem, node) do
                    s <- child.STATE
                    if problem.IS-GOAL(s) then return child
                    if s is not in reached then
                        add s to reached
                        add child to frontier
            return failure

    The goal test is applied when a node is *generated* (early goal test),
    exactly as in the figure.  With unit action costs this still returns a
    shallowest - therefore optimal - solution.
    """
    node = Node(problem.initial)
    if problem.is_goal(node.state):
        return node
    frontier = FIFOQueue([node])
    reached = {problem.initial}
    while frontier:
        node = frontier.popleft()
        for child in expand(problem, node):
            s = child.state
            if problem.is_goal(s):
                return child
            if s not in reached:
                reached.add(s)
                frontier.append(child)
    return failure
