"""Command-line entry point.

    python -m water_jugs                         # the activity: 12, 8, 3 -> 1 gallon
    python -m water_jugs --capacities 5 3 --goal 4
"""

from __future__ import annotations

import argparse

from .jugs_problem import WaterJugsProblem
from .search import breadth_first_search, failure, path_actions, path_states


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Water-jug puzzle solved with BFS (AIMA Fig. 3.9)")
    parser.add_argument("--capacities", type=int, nargs="+", default=[12, 8, 3])
    parser.add_argument("--goal", type=int, default=1, help="amount to measure")
    parser.add_argument("--initial", type=int, nargs="+", default=None)
    args = parser.parse_args(argv)

    problem = WaterJugsProblem(args.capacities, args.goal, args.initial)
    caps = " / ".join(f"{c}-gal" for c in problem.capacities)
    print(f"Jugs: {caps}   start: {problem.initial}   goal: some jug holds {problem.goal} gal")
    print(f"Reachable states: {len(problem.reachable_states())}\n")

    node = breadth_first_search(problem)
    if node is failure:
        print("No solution: the goal amount cannot be measured with these jugs.")
        return 1

    states = path_states(node)
    actions = path_actions(node)
    print(f"Step  {'Action'.ljust(42)}  State")
    print(f"   0  {'(start)'.ljust(42)}  {states[0]}")
    for step, (action, state) in enumerate(zip(actions, states[1:]), start=1):
        print(f"{step:4}  {problem.describe(action).ljust(42)}  {state}")
    print(f"\nSolved in {len(actions)} actions (BFS => fewest possible).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
