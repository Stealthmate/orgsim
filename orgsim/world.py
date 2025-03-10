import abc

import numpy as np
import pydantic

import orgsim.common as common
import orgsim.person as person


class PersonState(pydantic.BaseModel):
    params: person.PersonParams
    age: int = 0
    gain: float = 0.0
    contributions: int = 0


class RewardDistributionStrategy(abc.ABC):
    @abc.abstractmethod
    def compute_rewards(
        self, *, total: float, people: list[PersonState]
    ) -> dict[str, float]:
        raise NotImplementedError()


class WorldParams(pydantic.BaseModel):
    initial_people: set[person.PersonParams]
    profit_period: int
    profit_coef: float
    initial_personal_gain: float
    selfish_gain: float
    selfless_gain: float
    daily_loss: float
    periodic_recruit_count: int
    max_age: int
    reward_distribution_strategy: RewardDistributionStrategy
    identity_generator: common.IdentityGenerator

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)


class AllEqual(RewardDistributionStrategy):
    def compute_rewards(
        self,
        *,
        total: float,
        people: list[PersonState],
    ) -> dict[str, float]:
        N = len(people)
        return {p.params.identity: total / N for p in people}


class EqualContribution(RewardDistributionStrategy):
    def compute_rewards(
        self,
        *,
        total: float,
        people: list[PersonState],
    ) -> dict[str, float]:
        N = sum(x.contributions for x in people)
        if N == 0:
            return {}
        return {p.params.identity: p.contributions * total / N for p in people}


class World:
    def __init__(self, *, world_params: WorldParams) -> None:
        self._params = world_params

        self._people_states: dict[str, PersonState] = {
            p.identity: PersonState(params=p, gain=self._params.initial_personal_gain)
            for p in self._params.initial_people
        }

        self._date: int = 0
        self._period: int = 0
        self._org_gain: float = 0.0

        self.period_metrics: list[dict[str, float]] = {}

    def is_empty(self) -> bool:
        return len(self._people_states) == 0

    def run_period(self) -> None:
        for i in range(self._params.profit_period):
            self.run_day()

        if self.is_empty():
            return

        self._record_period_metric("population", len(self._people_states))
        self._record_period_metric(
            "average_selfishness",
            np.average([x.params.selfishness for x in self._people_states.values()]),
        )
        self._record_period_metric("total_reward", self._org_gain)

        self._distribute_profits()
        self._record_period_metric(
            "average_wealth", np.average([x.gain for x in self._people_states.values()])
        )

        self._recruit_people()

        self._period += 1

    def run_day(self) -> None:
        rands = np.random.uniform(size=len(self._people_states))
        for i, state in enumerate(list(self._people_states.values())):
            self._person_act(state, rands[i])
        self._date += 1

    def _record_period_metric(self, name: str, value: float) -> None:
        if self._period not in self.period_metrics:
            self.period_metrics[self._period] = {"period": self._period}

        row = self.period_metrics[self._period]
        if name in row:
            raise Exception(f"{name} already recorded for {self._period}")
        row[name] = value

    def _person_act(self, state: PersonState, p: float) -> None:
        state.age += 1
        state.gain -= self._params.daily_loss
        if p < state.params.selfishness:
            state.gain += self._params.selfish_gain
        else:
            state.gain += self._params.selfless_gain
            self._org_gain += self._params.selfless_gain * self._params.profit_coef
            state.contributions += 1

        if state.gain <= 0:
            # print(state.person.identity, "died of starvation.")
            del self._people_states[state.params.identity]
        elif state.age >= self._params.max_age:
            # print(state.person.identity, "died of old age.")
            del self._people_states[state.params.identity]

    def _distribute_profits(self) -> None:
        rewards = self._params.reward_distribution_strategy.compute_rewards(
            total=self._org_gain, people=list(self._people_states.values())
        )
        for id_, r in rewards.items():
            self._people_states[id_].gain += r
            self._people_states[id_].contributions = 0
            self._org_gain -= r

    def _recruit_people(self) -> None:
        m = np.average([s.params.selfishness for s in self._people_states.values()])

        self._record_period_metric("recruit_average_selfishness", m)

        identities = [
            self._params.identity_generator.generate()
            for _ in range(self._params.periodic_recruit_count)
        ]
        selfishness_values = np.clip(
            np.random.normal(
                loc=m,
                scale=0.05,
                size=self._params.periodic_recruit_count,
            ),
            0,
            1,
        )

        for id_, s in zip(identities, selfishness_values):
            self._people_states[id_] = PersonState(
                params=person.PersonParams(identity=id_, selfishness=s),
                gain=self._params.initial_personal_gain,
            )
