"""Agent / Environment framework for Question 1.

The design follows AIMA 4e, Chapter 2, and the structure of the aima-python
reference code (``agents.py``) that accompanies the textbook:

* ``Agent``                     - an agent is an agent *program* attached to a body
* ``Environment``               - ``percept`` / ``execute_action`` / ``step`` / ``run``
* ``Rule`` and ``rule_match``   - condition-action rules
* ``SimpleReflexAgentProgram``  - AIMA Figure 2.10 (SIMPLE-REFLEX-AGENT)

Only the pieces needed for this activity are reproduced.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Optional


class Agent:
    """An agent is anything that perceives its environment through sensors and
    acts on it through actuators.  The decision making lives in ``program``,
    a function that maps the current percept to an action (AIMA 2.4)."""

    def __init__(self, program: Callable[[Any], Any]):
        if program is None or not callable(program):
            raise ValueError("An Agent needs a callable agent program")
        self.alive = True
        self.performance = 0
        self.program = program

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


class Environment:
    """Abstract environment, as in aima-python.

    Subclasses implement ``percept`` (what the agent's sensors receive) and
    ``execute_action`` (what the agent's actuators do to the world)."""

    def __init__(self) -> None:
        self.agents: list[Agent] = []

    # --- to be supplied by concrete environments -------------------------
    def percept(self, agent: Agent) -> Any:
        raise NotImplementedError

    def execute_action(self, agent: Agent, action: Any) -> None:
        raise NotImplementedError

    def is_done(self) -> bool:
        return not any(agent.alive for agent in self.agents)

    # --- generic simulation loop (same shape as aima-python) -------------
    def add_agent(self, agent: Agent) -> Agent:
        self.agents.append(agent)
        return agent

    def step(self) -> None:
        """Run the environment for one time step: every agent perceives,
        then every agent acts."""
        if self.is_done():
            return
        actions = [agent.program(self.percept(agent)) for agent in self.agents]
        for agent, action in zip(self.agents, actions):
            self.execute_action(agent, action)

    def run(self, steps: int = 1000) -> None:
        for _ in range(steps):
            if self.is_done():
                return
            self.step()


class Rule:
    """A condition-action rule: *if condition(state) then action*."""

    def __init__(self, name: str, condition: Callable[[Any], bool], action: Any):
        self.name = name
        self.condition = condition
        self.action = action

    def matches(self, state: Any) -> bool:
        return bool(self.condition(state))

    def __repr__(self) -> str:
        return f"Rule({self.name!r} -> {self.action})"


def rule_match(state: Any, rules: Iterable[Rule]) -> Optional[Rule]:
    """RULE-MATCH: return the first rule whose condition matches ``state``."""
    for rule in rules:
        if rule.matches(state):
            return rule
    return None


def SimpleReflexAgentProgram(rules: list[Rule], interpret_input: Callable[[Any], Any]):
    """AIMA 4e Figure 2.10.

        function SIMPLE-REFLEX-AGENT(percept) returns an action
            persistent: rules, a set of condition-action rules
            state  <- INTERPRET-INPUT(percept)
            rule   <- RULE-MATCH(state, rules)
            action <- rule.ACTION
            return action

    ``program.last_rule`` records which rule fired so a run can be explained
    afterwards.  It is a report only: the agent never reads it when deciding,
    so the agent stays memoryless (a pure function of the current percept).
    """

    def program(percept):
        state = interpret_input(percept)
        rule = rule_match(state, rules)
        if rule is None:
            raise LookupError(f"No rule matches state {state!r}")
        action = rule.action
        program.last_rule = rule
        return action

    program.last_rule = None
    return program
