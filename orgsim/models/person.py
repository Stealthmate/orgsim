import abc

import numpy as np
import pydantic

from orgsim import framework


class PersonSeed(pydantic.BaseModel):
    selfishness: float


class PersonActionStrategy(abc.ABC):
    @abc.abstractmethod
    def act(
        self, *, state: framework.ImmutableWorldState[PersonSeed], identity: str
    ) -> float:
        raise NotImplementedError()


class ConstantSelfishness(PersonActionStrategy):
    def act(
        self, *, state: framework.ImmutableWorldState[PersonSeed], identity: str
    ) -> float:
        return 1 - state.people_states[identity].seed.selfishness


class ConstantAntiSelfishness(PersonActionStrategy):
    def act(
        self, *, state: framework.ImmutableWorldState[PersonSeed], identity: str
    ) -> float:
        return state.people_states[identity].seed.selfishness


class StrategicSelfishness(PersonActionStrategy):
    def __init__(self, c: float = 2) -> None:
        self._c = c

    def act(
        self, *, state: framework.ImmutableWorldState[PersonSeed], identity: str
    ) -> float:
        base = 1 - state.people_states[identity].seed.selfishness

        total_contributions = sum(
            [pstate.contributions for pstate in state.people_states.values()]
        )
        if total_contributions == 0:
            return base

        my_bonus_forecast = (
            state.people_states[identity].contributions
            * state.total_reward
            / total_contributions
        )
        qol = (
            my_bonus_forecast + state.seed.fiscal_length * state.seed.daily_salary
        ) / (state.seed.fiscal_length * state.seed.daily_living_cost)
        c = self._c
        cf = np.clip((c - c * qol) / qol, 0, 1)

        return float(base * cf)
