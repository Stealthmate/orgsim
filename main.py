import random

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pydantic

IDENTITY_NUMBER = 0

def generate_identity() -> int:
    global IDENTITY_NUMBER
    IDENTITY_NUMBER += 1
    return str(IDENTITY_NUMBER)

class Person(pydantic.BaseModel):
    identity: str = pydantic.Field(default_factory=generate_identity)
    selfishness: float = pydantic.Field(default_factory=lambda: random.uniform(0, 1))

    def __hash__(self) -> int:
        return hash(self.identity)

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

class PersonalState(pydantic.BaseModel):
    person: Person
    age: int
    gain: float

class World:
    def __init__(
        self,
        *,
        world_params: WorldParams
    ) -> None:
        self._params = world_params

        self.people_state: dict[str, PersonalState] = {
            person.identity: PersonalState(
                person=person,
                age=0,
                gain=world_params.initial_personal_gain
            ) for person in world_params.initial_people
        }

        self._date: int = 0
        self._org_gain: float = 0.0

    def run(self) -> None:
        if len(self.people_state) == 0:
            return

        rands = np.random.uniform(size=len(self.people_state))
        for i, state in enumerate(list(self.people_state.values())):
            self._person_act(state, rands[i])

        self._date += 1

        if len(self.people_state) == 0:
            return
        if self._date % self._params.profit_period == 0:
            self._distribute_profits()
            self._recruit_people()

    def _person_act(self, state: PersonalState, p: float) -> None:
        state.age += 1
        state.gain -= self._params.daily_loss
        if p < state.person.selfishness:
            state.gain += self._params.selfish_gain
        else:
            state.gain += self._params.selfless_gain
            self._org_gain += self._params.selfless_gain

        if state.gain <= 0:
            # print(state.person.identity, "died of starvation.")
            del self.people_state[state.person.identity]
        elif state.age >= self._params.max_age:
            # print(state.person.identity, "died of old age.")
            del self.people_state[state.person.identity]

    def _distribute_profits(self) -> None:
        individual_gain = (self._org_gain * self._params.profit_coef) / len(self.people_state)
        for state in self.people_state.values():
            state.gain += individual_gain
        self._org_gain = 0

    def _recruit_people(self) -> None:
        m = np.average([s.person.selfishness for s in self.people_state.values()])
        # print("Recruiting people similar to", m)
        new_people_params = np.clip(np.random.normal(loc=m, scale=0.1, size=self._params.periodic_recruit_count), 0, 1)
        new_people = [Person(selfishness=p) for p in new_people_params]
        for person in new_people:
            # print("Recruited", person.identity, "with", person.selfishness, "selfishness")
            self.people_state[person.identity] = PersonalState(
                person=person,
                age=0,
                gain=self._params.initial_personal_gain
            )

class Tally(pydantic.BaseModel):
    day: int
    population: int
    average_wealth: float
    average_selfishness: float
    median_selfishness: float

def main():
    world = World(
        world_params=WorldParams(
            initial_people={Person() for _ in range(10)},
            profit_period=5,
            profit_coef=1.5,
            initial_personal_gain=100,
            selfish_gain=30,
            selfless_gain=25,
            daily_loss=43,
            periodic_recruit_count=5,
            max_age=100
        )
    )

    tally: list[Tally] = []

    for i in range(int(1e4)):
        world.run()
        if len(world.people_state) == 0:
            break
        tally.append(Tally(
            day=i,
            population=len(world.people_state),
            average_wealth=np.average([s.gain for s in world.people_state.values()]),
            average_selfishness=np.average([s.person.selfishness for s in world.people_state.values()]),
            median_selfishness=np.median([s.person.selfishness for s in world.people_state.values()])
        ))

    df = pd.DataFrame([
        t.model_dump()
        for t in tally
    ])
    print(df.head())

    fig, axs = plt.subplots(2, 2, figsize=(20, 10))
    sns.lineplot(df, x='day', y='average_wealth', ax=axs[0][0])

    sns.scatterplot(df, x='average_selfishness', y='average_wealth', ax=axs[0][1])
    axs[0][1].set_xlim(-.1, 1.1)

    sns.lineplot(df, x='day', y='average_selfishness', ax=axs[1][0])
    sns.lineplot(df, x='day', y='median_selfishness', ax=axs[1][0])
    axs[1][0].set_ylim(-.1, 1.1)

    sns.lineplot(df, x='day', y='population', ax=axs[1][1])
    plt.show()


if __name__ == "__main__":
    main()
