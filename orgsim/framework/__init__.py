import abc

import numpy as np
import pydantic


class PersonSeed(pydantic.BaseModel):
    identity: str
    selfishness: float

    def __hash__(self) -> int:
        return hash(self.identity)


class PersonState(pydantic.BaseModel):
    seed: PersonSeed
    age: int = 0
    gain: float = 0.0
    contributions: int = 0


class WorldSeed(pydantic.BaseModel):
    initial_people: set[PersonSeed]
    fiscal_length: int
    productivity: float
    initial_personal_gain: float
    selfish_gain: float
    selfless_gain: float
    living_cost: float
    periodic_recruit_count: int
    max_age: int


class WorldState(pydantic.BaseModel):
    seed: WorldSeed
    date: int
    people_states: dict[str, PersonState]
    total_reward: float
    fiscal_period: int


class WorldStrategy(abc.ABC):
    @abc.abstractmethod
    def distribute_rewards(self, *, state: WorldState) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def person_act(
        self,
        *,
        state: WorldState,
        identity: str,
        r: float,
    ) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def recruit_people(self, *, state: WorldState) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def on_before_person_acts(self, *, state: WorldState, identity: str) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def on_after_person_acts(self, *, state: WorldState, identity: str) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def on_end_of_day(self, *, state: WorldState) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def on_end_of_period(self, *, state: WorldState) -> None:
        raise NotImplementedError()


class World:
    def __init__(self, *, state: WorldState, strategy: WorldStrategy) -> None:
        self._state = state
        self._strategy = strategy

    def is_empty(self) -> bool:
        return len(self._state.people_states) == 0

    def run_period(self) -> None:
        for i in range(self._state.seed.fiscal_length):
            if self.is_empty():
                return
            self.run_day()

        if self.is_empty():
            return

        self._strategy.distribute_rewards(state=self._state)
        self._strategy.recruit_people(state=self._state)
        self._strategy.on_end_of_period(state=self._state)

    def run_day(self) -> None:
        rands = np.random.uniform(size=len(self._state.people_states))
        for i, state in enumerate(list(self._state.people_states.values())):
            self._strategy.on_before_person_acts(
                state=self._state, identity=state.seed.identity
            )
            self._strategy.person_act(
                state=self._state,
                identity=state.seed.identity,
                r=rands[i],
            )
            self._strategy.on_after_person_acts(
                state=self._state, identity=state.seed.identity
            )
        self._strategy.on_end_of_day(state=self._state)


def create_world(seed: WorldSeed, strategy: WorldStrategy) -> World:
    state = WorldState(
        seed=seed,
        date=0,
        people_states={
            p.identity: PersonState(seed=p, gain=seed.initial_personal_gain)
            for p in seed.initial_people
        },
        total_reward=0,
        fiscal_period=0,
    )

    return World(state=state, strategy=strategy)
