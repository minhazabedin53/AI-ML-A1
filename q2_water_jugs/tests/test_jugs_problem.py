"""The problem formulation: states, actions and transition model."""

import unittest

from water_jugs.jugs_problem import WaterJugsProblem


class TestFormulation(unittest.TestCase):

    def setUp(self):
        self.p = WaterJugsProblem()  # 12, 8, 3 -> 1

    def test_initial_state_and_goal(self):
        self.assertEqual(self.p.initial, (0, 0, 0))
        self.assertEqual(self.p.capacities, (12, 8, 3))
        self.assertFalse(self.p.is_goal((0, 0, 0)))
        self.assertTrue(self.p.is_goal((1, 8, 3)))
        self.assertTrue(self.p.is_goal((0, 1, 0)))
        self.assertTrue(self.p.is_goal((5, 0, 1)))

    def test_actions_from_empty_state_are_only_fills(self):
        self.assertEqual(self.p.actions((0, 0, 0)), [("Fill", 0), ("Fill", 1), ("Fill", 2)])

    def test_useless_actions_are_not_offered(self):
        acts = self.p.actions((12, 8, 3))  # everything full
        self.assertTrue(all(a[0] == "Empty" for a in acts))
        acts = self.p.actions((12, 0, 0))
        self.assertNotIn(("Fill", 0), acts)
        self.assertNotIn(("Empty", 1), acts)
        self.assertNotIn(("Pour", 1, 0), acts)

    def test_fill_and_empty(self):
        self.assertEqual(self.p.result((0, 5, 1), ("Fill", 0)), (12, 5, 1))
        self.assertEqual(self.p.result((7, 5, 1), ("Empty", 1)), (7, 0, 1))

    def test_pour_until_destination_full(self):
        self.assertEqual(self.p.result((12, 0, 0), ("Pour", 0, 1)), (4, 8, 0))

    def test_pour_until_source_empty(self):
        self.assertEqual(self.p.result((0, 2, 0), ("Pour", 1, 0)), (2, 0, 0))

    def test_water_is_conserved_by_pouring(self):
        for state in [(12, 0, 0), (4, 8, 0), (7, 3, 2), (1, 8, 3)]:
            for a in self.p.actions(state):
                if a[0] == "Pour":
                    self.assertEqual(sum(self.p.result(state, a)), sum(state))

    def test_results_stay_within_capacities(self):
        for s in self.p.reachable_states():
            self.assertTrue(all(0 <= x <= c for x, c in zip(s, self.p.capacities)))

    def test_size_of_state_space(self):
        """13*9*4 = 468 possible triples, but every action leaves at least one
        jug empty or full, so the 11*7*2 = 154 'all partly filled' triples are
        unreachable: 468 - 154 = 314."""
        states = self.p.reachable_states()
        self.assertEqual(len(states), 314)
        for s in states:
            self.assertTrue(any(x in (0, c) for x, c in zip(s, self.p.capacities)))

    def test_branching_factor_is_at_most_12(self):
        self.assertLessEqual(max(len(self.p.actions(s)) for s in self.p.reachable_states()), 12)

    def test_describe(self):
        self.assertEqual(self.p.describe(("Pour", 0, 2)), "Pour the 12-gal jug into the 3-gal jug")

    def test_invalid_problems_rejected(self):
        with self.assertRaises(ValueError):
            WaterJugsProblem((12, 0, 3))
        with self.assertRaises(ValueError):
            WaterJugsProblem((12, 8, 3), initial=(13, 0, 0))
        with self.assertRaises(ValueError):
            WaterJugsProblem((12, 8, 3), goal=-1)
        with self.assertRaises(ValueError):
            WaterJugsProblem().result((0, 0, 0), ("Drink", 0))


if __name__ == "__main__":
    unittest.main()
