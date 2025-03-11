import abc
import json
import typing

import numpy as np
import pandas as pd
import pydantic

from orgsim import common, framework

SeriesIdentity = frozenset[tuple[str, str]]


def generate_series_identity(name: str, labels: dict[str, str]) -> SeriesIdentity:
    return frozenset({"__name": name, **labels}.items())


class MetricsDump(pydantic.BaseModel):
    fiscal: dict[str, dict[int, float]]
    daily: dict[str, dict[int, float]]


class MetricsLogger:
    def __init__(self) -> None:
        self._fiscal_series: dict[SeriesIdentity, dict[int, float]] = {}
        self._daily_series: dict[SeriesIdentity, dict[int, float]] = {}

    def log_fiscal_metric(
        self,
        period: int,
        name: str,
        value: float,
        labels: typing.Optional[dict[str, str]] = None,
    ) -> None:
        the_labels: dict[str, str] = labels if labels is not None else {}

        id_ = generate_series_identity(name, the_labels)
        if id_ not in self._fiscal_series:
            self._fiscal_series[id_] = {}

        series = self._fiscal_series[id_]

        if period in series:
            raise Exception(f"Double record. {name}, {period}, {the_labels}")

        series[period] = value

    def log_daily_metric(
        self,
        day: int,
        name: str,
        value: float,
        labels: typing.Optional[dict[str, str]] = None,
    ) -> None:
        the_labels: dict[str, str] = labels if labels is not None else {}

        id_ = generate_series_identity(name, the_labels)
        if id_ not in self._daily_series:
            self._daily_series[id_] = {}

        series = self._daily_series[id_]

        if day in series:
            raise Exception(f"Double record. {name}, {day}, {the_labels}")

        series[day] = value

    def get_fiscal_metric(
        self,
        name: str,
        labels: typing.Optional[dict[str, str]] = None,
    ) -> "pd.Series[float]":
        the_labels: dict[str, str] = labels if labels is not None else {}
        id_ = generate_series_identity(name, the_labels)

        if id_ not in self._fiscal_series:
            raise Exception(f"No such series: {name}, {the_labels}")

        return pd.Series(self._fiscal_series[id_])

    def dump(self) -> MetricsDump:
        return MetricsDump(
            fiscal={json.dumps(dict(id_)): s for id_, s in self._fiscal_series.items()},
            daily={json.dumps(dict(id_)): s for id_, s in self._daily_series.items()},
        )


class RewardDistributionStrategy(abc.ABC):
    @abc.abstractmethod
    def distribute_rewards(
        self, *, state: framework.WorldState, metrics: MetricsLogger
    ) -> None:
        raise NotImplementedError()


class AllEqual(RewardDistributionStrategy):
    def distribute_rewards(self, *, state: framework.WorldState) -> None:
        v = state.total_reward / len(state.people_states)
        for pstate in state.people_states.values():
            pstate.wealth += v
        state.total_reward = 0


class EqualContribution(RewardDistributionStrategy):
    def distribute_rewards(
        self, *, state: framework.WorldState, metrics: MetricsLogger
    ) -> None:
        N = sum(x.contributions for x in state.people_states.values())
        if N == 0:
            return
        u = state.total_reward / N
        bonuses: list[float] = []
        for pstate in state.people_states.values():
            pstate.wealth += pstate.contributions * u
            bonuses.append(pstate.contributions * u)
        metrics.log_fiscal_metric(
            state.fiscal_period, "avg_bonus", float(np.average(bonuses))
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

        self.metrics = MetricsLogger()

    def _log_fiscal_base_stats(
        self, *, period: int, name: str, values: list[float]
    ) -> None:
        self.metrics.log_fiscal_metric(period, f"min_{name}", float(np.amin(values)))
        self.metrics.log_fiscal_metric(period, f"avg_{name}", float(np.average(values)))
        self.metrics.log_fiscal_metric(period, f"max_{name}", float(np.amax(values)))

    def distribute_rewards(self, *, state: framework.WorldState) -> None:
        self.metrics.log_fiscal_metric(
            state.fiscal_period,
            "population",
            len(state.people_states.values()),
        )
        self._log_fiscal_base_stats(
            period=state.fiscal_period,
            name="selfishness",
            values=[x.seed.selfishness for x in state.people_states.values()],
        )

        self._reward_distribution_strategy.distribute_rewards(
            state=state, metrics=self.metrics
        )

        self._log_fiscal_base_stats(
            period=state.fiscal_period,
            name="wealth",
            values=[x.wealth for x in state.people_states.values()],
        )

    def recruit_people(self, *, state: framework.WorldState) -> None:
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

        for id_, s in zip(identities, selfishness_values):
            state.people_states[id_] = framework.PersonState(
                seed=framework.PersonSeed(identity=id_, selfishness=s),
                wealth=state.seed.initial_individual_wealth,
            )

    def on_before_person_acts(
        self, *, state: framework.WorldState, identity: str
    ) -> None:
        pass

    def on_after_person_acts(
        self, *, state: framework.WorldState, identity: str
    ) -> None:
        pass

    def on_end_of_day(self, *, state: framework.WorldState) -> None:
        for pstate in list(state.people_states.values()):
            pstate.age += 1
            if pstate.age == state.seed.max_age:
                del state.people_states[pstate.seed.identity]

            pstate.wealth -= state.seed.daily_living_cost
            if pstate.wealth <= 0:
                del state.people_states[pstate.seed.identity]
        state.date += 1

    def on_end_of_period(self, *, state: framework.WorldState) -> None:
        for pstate in state.people_states.values():
            pstate.contributions = 0

        self._log_fiscal_base_stats(
            period=state.fiscal_period,
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
