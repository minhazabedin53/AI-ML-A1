"""Breadth-first search (AIMA Figure 3.9) on the jug problem and test data."""

import contextlib
import io
import json
import unittest
from pathlib import Path

from water_jugs.__main__ import main as cli_main
from water_jugs.jugs_problem import WaterJugsProblem
from water_jugs.search import (
    Node, Problem, breadth_first_search, expand, failure, path_actions, path_states,
)

CASES = json.loads((Path(__file__).resolve().parent.parent / "test_data" /
                    "jug_cases.json").read_text(encoding="utf-8"))


def make_problem(case):
    return WaterJugsProblem(case["capacities"], case["goal"], case.get("initial"))


def shortest_by_layers(problem):
    """Independent check that does NOT use search.py: grow the set of states
    reachable in exactly d steps, d = 0, 1, 2, ..., until a goal appears."""
    layer, seen, depth = {problem.initial}, {problem.initial}, 0
    while layer:
        if any(problem.is_goal(s) for s in layer):
            return depth
        layer = {problem.result(s, a) for s in layer for a in problem.actions(s)} - seen
        seen |= layer
        depth += 1
    return None


class TestBreadthFirstSearch(unittest.TestCase):

    def test_activity_problem(self):
        p = WaterJugsProblem()
        node = breadth_first_search(p)
        self.assertIsNot(node, failure)
        self.assertEqual(len(path_actions(node)), 3)
        self.assertTrue(p.is_goal(node.state))
        self.assertEqual(path_states(node)[0], (0, 0, 0))
        self.assertEqual(node.path_cost, 3)

    def test_cases_from_test_data(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                node = breadth_first_search(make_problem(case))
                if case["expected_length"] is None:
                    self.assertIs(node, failure)
                else:
                    self.assertIsNot(node, failure)
                    self.assertEqual(len(path_actions(node)), case["expected_length"])

    def test_solutions_replay_correctly(self):
        """Applying the returned actions from the start really reaches the goal,
        and every action was legal in the state where it was taken."""
        for case in CASES:
            if case["expected_length"] is None:
                continue
            with self.subTest(case=case["name"]):
                p = make_problem(case)
                node = breadth_first_search(p)
                state = p.initial
                for action, expected_state in zip(path_actions(node), path_states(node)[1:]):
                    self.assertIn(action, p.actions(state))
                    state = p.result(state, action)
                    self.assertEqual(state, expected_state)
                self.assertTrue(p.is_goal(state))

    def test_bfs_is_optimal_matches_independent_check(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                p = make_problem(case)
                node = breadth_first_search(p)
                bfs_len = None if node is failure else len(path_actions(node))
                self.assertEqual(bfs_len, shortest_by_layers(p))

    def test_no_goal_within_two_actions_for_activity_problem(self):
        """Why 3 is the minimum: no state reachable in <= 2 actions holds 1 gallon."""
        p = WaterJugsProblem()
        within_two = {p.initial}
        for _ in range(2):
            within_two |= {p.result(s, a) for s in within_two for a in p.actions(s)}
        self.assertFalse(any(p.is_goal(s) for s in within_two))

    def test_bfs_explores_shallowest_nodes_first(self):
        """On a small explicit graph BFS returns the shallowest goal even when
        a deeper one would be generated first by depth-first order."""
        class Graph(Problem):
            edges = {"S": ["A", "B"], "A": ["C"], "B": ["G"], "C": ["G2"], "G": [], "G2": []}
            def actions(self, s): return self.edges[s]
            def result(self, s, a): return a
            def is_goal(self, s): return s in ("G", "G2")
        node = breadth_first_search(Graph("S"))
        self.assertEqual(path_states(node), ["S", "B", "G"])

    def test_heuristic_is_admissible(self):
        """h(n) <= true number of actions to a goal for every reachable state."""
        base = WaterJugsProblem()
        for s in base.reachable_states():
            p = WaterJugsProblem(base.capacities, base.goal, initial=s)
            true_cost = shortest_by_layers(p)
            self.assertLessEqual(p.h(Node(s)), true_cost)


class TestSearchFramework(unittest.TestCase):

    def test_expand_builds_child_nodes(self):
        p = WaterJugsProblem()
        root = Node(p.initial)
        children = list(expand(p, root))
        self.assertEqual([c.state for c in children], [(12, 0, 0), (0, 8, 0), (0, 0, 3)])
        self.assertTrue(all(c.parent is root and c.path_cost == 1 for c in children))
        self.assertEqual(len(children[0]), 1)

    def test_path_helpers_on_root(self):
        root = Node("x")
        self.assertEqual(path_actions(root), [])
        self.assertEqual(path_states(root), ["x"])
        self.assertEqual(path_states(failure), [])

    def test_command_line_interface(self):
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            self.assertEqual(cli_main([]), 0)
            self.assertEqual(cli_main(["--capacities", "6", "4", "--goal", "1"]), 1)
        self.assertIn("Solved in 3 actions", printed.getvalue())
        self.assertIn("No solution", printed.getvalue())


if __name__ == "__main__":
    unittest.main()
