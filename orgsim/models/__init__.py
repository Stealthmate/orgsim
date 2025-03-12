import abc
import typing

import numpy as np

from orgsim import common, framework
from . import metrics


class RewardDistributionStrategy(abc.ABC):
    @abc.abstractmethod
    def distribute_rewards(
        self, *, state: framework.WorldState, metrics: metrics.Metrics
    ) -> None:
        raise NotImplementedError()


class AllEqual(RewardDistributionStrategy):
    def distribute_rewards(
        self, *, state: framework.WorldState, metrics: metrics.Metrics
    ) -> None:
        v = state.total_reward / len(state.people_states)
        for pstate in state.people_states.values():
            pstate.wealth += v
        state.total_reward = 0


class EqualContribution(RewardDistributionStrategy):
    def distribute_rewards(
        self, *, state: framework.WorldState, metrics: metrics.Metrics
    ) -> None:
        N = sum(x.contributions for x in state.people_states.values())
        if N == 0:
            return
        u = state.total_reward / N
        bonuses: list[float] = []
        for pstate in state.people_states.values():
            pstate.wealth += pstate.contributions * u
            bonuses.append(pstate.contributions * u)
        metrics.log(
            world_state=state, name="avg_bonus", value=float(np.average(bonuses))
        )
        state.total_reward = 0


class DefaultWorldStrategy(framework.WorldStrategy):
    def __init__(
        self,
        *,
        identity_generator: common.IdentityGenerator,
        reward_distribution_strategy: RewardDistributionStrategy,
    ) -> None:
        self._reward_distribution_strategy = reward_distribution_strategy
        self._identity_generator = identity_generator

        self.metrics = metrics.Metrics(data=metrics.MetricsData(series_classes={}))

    def _log_fiscal_base_stats(
        self, *, state: framework.WorldState, name: str, values: list[float]
    ) -> None:
        self.metrics.log(
            world_state=state, name=f"min_{name}", value=float(np.amin(values))
        )
        self.metrics.log(
            world_state=state, name=f"avg_{name}", value=float(np.average(values))
        )
        self.metrics.log(
            world_state=state, name=f"max_{name}", value=float(np.amax(values))
        )

    def distribute_rewards(self, *, state: framework.WorldState) -> None:
        self.metrics.log(
            world_state=state,
            name="population",
            value=len(state.people_states.values()),
        )
        self._log_fiscal_base_stats(
            state=state,
            name="selfishness",
            values=[x.seed.selfishness for x in state.people_states.values()],
        )

        self._reward_distribution_strategy.distribute_rewards(
            state=state, metrics=self.metrics
        )

        self._log_fiscal_base_stats(
            state=state,
            name="wealth",
            values=[x.wealth for x in state.people_states.values()],
        )

    def generate_recruit_candidates(
        self, *, state: framework.ImmutableWorldState
    ) -> typing.Iterable[framework.PersonSeed]:
        m = np.average([s.seed.selfishness for s in state.people_states.values()])

        identities = [
            self._identity_generator.generate()
            for _ in range(state.seed.periodic_recruit_count)
        ]
        selfishness_values = np.clip(
            np.random.normal(
                loc=m,
                scale=0.05,
                size=state.seed.periodic_recruit_count,
            ),
            0,
            1,
        )
        for i, s in zip(identities, list(selfishness_values)):
            yield framework.PersonSeed(identity=i, selfishness=s)

    def on_before_person_acts(
        self, *, state: framework.WorldState, identity: str
    ) -> None:
        pass

    def on_after_person_acts(
        self, *, state: framework.WorldState, identity: str
    ) -> None:
        pass

    def _kill_person(self, *, state: framework.WorldState, identity: str) -> None:
        pstate = state.people_states[identity]
        self.metrics.log(
            world_state=state,
            name="person_age",
            value=pstate.age,
            labels={"identity": str(pstate.seed.identity)},
        )
        del state.people_states[pstate.seed.identity]

    def on_end_of_day(self, *, state: framework.WorldState) -> None:
        for pstate in list(state.people_states.values()):
            pstate.age += 1
            if pstate.age == state.seed.max_age:
                self._kill_person(state=state, identity=pstate.seed.identity)

            pstate.wealth -= state.seed.daily_living_cost
            if pstate.wealth <= 0:
                self._kill_person(state=state, identity=pstate.seed.identity)
        state.date += 1

    def on_end_of_period(self, *, state: framework.WorldState) -> None:
        for pstate in state.people_states.values():
            pstate.contributions = 0

        self._log_fiscal_base_stats(
            state=state,
            name="age",
            values=[x.age for x in state.people_states.values()],
        )

        state.fiscal_period += 1

    def person_act(
        self,
        *,
        state: framework.WorldState,
        identity: str,
        r: float,
    ) -> None:
        pstate = state.people_states[identity]
        pstate.wealth += state.seed.daily_salary
        pstate.contributions += 1 - pstate.seed.selfishness
        state.total_reward += (
            (1 - pstate.seed.selfishness)
            * state.seed.productivity
            * state.seed.daily_salary
        )
