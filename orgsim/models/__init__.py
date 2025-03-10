import abc

import numpy as np
import pandas as pd

from orgsim import common, framework


class MetricsLogger:
    def __init__(self) -> None:
        self._period_series: dict[int, dict[str, float]] = {}

    def log_period_metric(self, period: int, name: str, value: float) -> None:
        if period not in self._period_series:
            self._period_series[period] = {"period": period}
        if name in self._period_series[period]:
            raise Exception(f"Metric {name} already logged for period {period}")
        self._period_series[period][name] = value

    def period_metrics(self) -> pd.DataFrame:
        return pd.DataFrame.from_dict(self._period_series, orient="index")


class RewardDistributionStrategy(abc.ABC):
    @abc.abstractmethod
    def distribute_rewards(self, *, state: framework.WorldState) -> None:
        raise NotImplementedError()


class AllEqual(RewardDistributionStrategy):
    def distribute_rewards(self, *, state: framework.WorldState) -> None:
        v = state.total_reward / len(state.people_states)
        for pstate in state.people_states.values():
            pstate.gain += v
        state.total_reward = 0


class EqualContribution(RewardDistributionStrategy):
    def distribute_rewards(self, *, state: framework.WorldState) -> None:
        N = sum(x.contributions for x in state.people_states.values())
        if N == 0:
            return
        u = state.total_reward / N
        for pstate in state.people_states.values():
            pstate.gain += pstate.contributions * u
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

    def distribute_rewards(self, *, state: framework.WorldState) -> None:
        self.metrics.log_period_metric(
            state.fiscal_period,
            "population",
            len(state.people_states.values()),
        )
        self.metrics.log_period_metric(
            state.fiscal_period,
            "average_wealth",
            float(np.average([x.gain for x in state.people_states.values()])),
        )
        self.metrics.log_period_metric(
            state.fiscal_period,
            "average_selfishness",
            float(
                np.average([x.seed.selfishness for x in state.people_states.values()])
            ),
        )

        self._reward_distribution_strategy.distribute_rewards(state=state)

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
                gain=state.seed.initial_personal_gain,
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

            pstate.gain -= state.seed.daily_loss
            if pstate.gain <= 0:
                del state.people_states[pstate.seed.identity]
        state.date += 1

    def on_end_of_period(self, *, state: framework.WorldState) -> None:
        for pstate in state.people_states.values():
            pstate.contributions = 0

        state.fiscal_period += 1

    def person_act(
        self,
        *,
        state: framework.WorldState,
        identity: str,
        r: float,
    ) -> None:
        pstate = state.people_states[identity]
        if r < pstate.seed.selfishness:
            pstate.gain += state.seed.selfish_gain
        else:
            pstate.gain += state.seed.selfless_gain
            pstate.contributions += 1
            state.total_reward += state.seed.selfless_gain * state.seed.profit_coef
