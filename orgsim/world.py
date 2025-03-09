import numpy as np
import pydantic

from orgsim.common import Person, PersonalState
from orgsim.reward_distribution import RewardDistributionStrategy


class WorldParams(pydantic.BaseModel):
    initial_people: set[Person]
    profit_period: int
    profit_coef: float
    initial_personal_gain: float
    selfish_gain: float
    selfless_gain: float
    daily_loss: float
    periodic_recruit_count: int
    max_age: int
    reward_distribution_strategy: RewardDistributionStrategy

    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)


class World:
    def __init__(self, *, world_params: WorldParams) -> None:
        self._params = world_params

        self.people_state: dict[str, PersonalState] = {
            person.identity: PersonalState(
                person=person,
                age=0,
                gain=world_params.initial_personal_gain,
            )
            for person in world_params.initial_people
        }

        self._date: int = 0
        self._period: int = 0
        self._org_gain: float = 0.0

        self.period_metrics: list[dict[str, float]] = {}

    def run_period(self) -> None:
        for i in range(self._params.profit_period):
            self.run_day()

        if len(self.people_state) == 0:
            return

        self._record_period_metric("population", len(self.people_state))
        self._record_period_metric(
            "average_selfishness",
            np.average([x.person.selfishness for x in self.people_state.values()]),
        )
        self._record_period_metric("total_reward", self._org_gain)

        self._distribute_profits()
        self._record_period_metric(
            "average_wealth", np.average([x.gain for x in self.people_state.values()])
        )

        self._recruit_people()

        self._period += 1

    def run_day(self) -> None:
        rands = np.random.uniform(size=len(self.people_state))
        for i, state in enumerate(list(self.people_state.values())):
            self._person_act(state, rands[i])
        self._date += 1

    def _record_period_metric(self, name: str, value: float) -> None:
        if self._period not in self.period_metrics:
            self.period_metrics[self._period] = {"period": self._period}

        row = self.period_metrics[self._period]
        if name in row:
            raise Exception(f"{name} already recorded for {self._period}")
        row[name] = value

    def _person_act(self, state: PersonalState, p: float) -> None:
        state.age += 1
        state.gain -= self._params.daily_loss
        if p < state.person.selfishness:
            state.gain += self._params.selfish_gain
        else:
            state.gain += self._params.selfless_gain
            self._org_gain += self._params.selfless_gain * self._params.profit_coef
            state.contributions += 1

        if state.gain <= 0:
            # print(state.person.identity, "died of starvation.")
            del self.people_state[state.person.identity]
        elif state.age >= self._params.max_age:
            # print(state.person.identity, "died of old age.")
            del self.people_state[state.person.identity]

    def _distribute_profits(self) -> None:
        rewards = self._params.reward_distribution_strategy.compute_rewards(
            total=self._org_gain, people=list(self.people_state.values())
        )
        for id_, r in rewards.items():
            self.people_state[id_].gain += r
            self.people_state[id_].contributions = 0
            self._org_gain -= r

    def _recruit_people(self) -> None:
        m = np.average([s.person.selfishness for s in self.people_state.values()])

        self._record_period_metric("recruit_average_selfishness", m)

        # print("Recruiting people similar to", m)
        new_people_params = np.clip(
            np.random.normal(
                loc=m,
                scale=0.05,
                size=self._params.periodic_recruit_count,
            ),
            0,
            1,
        )
        new_people = [Person(selfishness=p) for p in new_people_params]
        for person in new_people:
            # print("Recruited", person.identity, "with", person.selfishness, "selfishness")
            self.people_state[person.identity] = PersonalState(
                person=person,
                age=0,
                gain=self._params.initial_personal_gain,
            )
