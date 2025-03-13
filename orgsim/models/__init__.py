import abc
import typing

import numpy as np

from orgsim import common, framework, metrics
from . import person, recruitment

type WorldSeed = framework.WorldSeed[person.PersonSeed]
type WorldState = framework.WorldState[person.PersonSeed]
type ImmutableWorldState = framework.ImmutableWorldState[person.PersonSeed]


class RewardDistributionStrategy(abc.ABC):
    @abc.abstractmethod
    def distribute_rewards(
        self, *, state: WorldState, metrics: metrics.Metrics
    ) -> None:
        raise NotImplementedError()


class AllEqual(RewardDistributionStrategy):
    def distribute_rewards(
        self, *, state: WorldState, metrics: metrics.Metrics
    ) -> None:
        v = state.total_reward / len(state.people_states)
        for pstate in state.people_states.values():
            pstate.wealth += v
        state.total_reward = 0


class EqualContribution(RewardDistributionStrategy):
    def distribute_rewards(
        self, *, state: WorldState, metrics: metrics.Metrics
    ) -> None:
        N = sum(x.contributions for x in state.people_states.values())
        if N == 0:
            return
        u = state.total_reward / N
        for pstate in state.people_states.values():
            pstate.wealth += pstate.contributions * u
            metrics.log(
                time=state.time,
                name="person_bonus",
                value=pstate.contributions * u,
                labels={"identity": pstate.identity},
            )
        state.total_reward = 0


class DefaultWorldStrategy(framework.WorldStrategy[person.PersonSeed]):
    def __init__(
        self,
        *,
        identity_generator: common.IdentityGenerator,
        reward_distribution_strategy: RewardDistributionStrategy,
        recruitment_strategy: recruitment.RecruitmentStrategy,
        person_action_strategy: person.PersonActionStrategy,
    ) -> None:
        self._reward_distribution_strategy = reward_distribution_strategy
        self._recruitment_strategy = recruitment_strategy
        self._identity_generator = identity_generator
        self._person_action_strategy = person_action_strategy

        self.metrics = metrics.Metrics(data=metrics.MetricsData(series_classes={}))

    def _log_fiscal_base_stats(
        self, *, state: WorldState, name: str, values: list[float]
    ) -> None:
        self.metrics.log(
            time=state.time, name=f"min_{name}", value=float(np.amin(values))
        )
        self.metrics.log(
            time=state.time, name=f"avg_{name}", value=float(np.average(values))
        )
        self.metrics.log(
            time=state.time, name=f"max_{name}", value=float(np.amax(values))
        )

    def distribute_rewards(self, *, state: WorldState) -> None:
        self.metrics.log(
            time=state.time,
            name="population",
            value=len(state.people_states.values()),
        )
        self._log_fiscal_base_stats(
            state=state,
            name="selfishness",
            values=[x.seed.selfishness for x in state.people_states.values()],
        )
        self._log_fiscal_base_stats(
            state=state,
            name="contribution",
            values=[x.contributions for x in state.people_states.values()],
        )

        self._reward_distribution_strategy.distribute_rewards(
            state=state, metrics=self.metrics
        )

        self._log_fiscal_base_stats(
            state=state,
            name="wealth",
            values=[x.wealth for x in state.people_states.values()],
        )

    def pick_role_models(self, *, state: ImmutableWorldState) -> typing.Iterable[str]:
        yield from self._recruitment_strategy.pick_role_models(state=state)

    def generate_recruits(
        self,
        *,
        seed: WorldSeed,
        role_models: typing.Iterable[person.PersonSeed],
    ) -> typing.Iterable[person.PersonSeed]:
        m = np.average([s.selfishness for s in role_models])

        identities = [
            self._identity_generator.generate()
            for _ in range(seed.periodic_recruit_count)
        ]
        selfishness_values = np.clip(
            np.random.normal(
                loc=m,
                scale=0.05,
                size=seed.periodic_recruit_count,
            ),
            0,
            1,
        )
        for i, s in zip(identities, list(selfishness_values)):
            yield person.PersonSeed(selfishness=s)

    def on_before_person_acts(self, *, state: WorldState, identity: str) -> None:
        pass

    def on_after_person_acts(self, *, state: WorldState, identity: str) -> None:
        pass

    def _kill_person(self, *, state: WorldState, identity: str) -> None:
        pstate = state.people_states[identity]
        self.metrics.log(
            time=state.time,
            name="person_age",
            value=pstate.age,
            labels={"identity": str(pstate.identity)},
        )
        del state.people_states[pstate.identity]

    def on_end_of_day(self, *, state: WorldState) -> None:
        for pstate in list(state.people_states.values()):
            pstate.age += 1
            if pstate.age == state.seed.max_age:
                self._kill_person(state=state, identity=pstate.identity)
                continue

            pstate.wealth -= state.seed.daily_living_cost
            if pstate.wealth <= 0:
                self._kill_person(state=state, identity=pstate.identity)

    def on_end_of_period(self, *, state: WorldState) -> None:
        for pstate in state.people_states.values():
            pstate.contributions = 0

        self._log_fiscal_base_stats(
            state=state,
            name="age",
            values=[x.age for x in state.people_states.values()],
        )

    def person_act(self, *, state: WorldState, identity: str) -> float:
        v = self._person_action_strategy.act(state=state, identity=identity)
        self.metrics.log(
            time=state.time,
            name="person_contribution",
            value=v,
            labels={"identity": identity},
        )
        return v
