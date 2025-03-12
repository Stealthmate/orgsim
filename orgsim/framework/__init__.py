import abc
import typing

import pydantic


class PersonSeed(pydantic.BaseModel):
    identity: str
    selfishness: float

    def __hash__(self) -> int:
        return hash(self.identity)


class PersonState(pydantic.BaseModel):
    seed: PersonSeed
    age: int = 0
    wealth: float = 0.0
    contributions: float = 0


class WorldSeed(pydantic.BaseModel):
    initial_people: set[PersonSeed]
    fiscal_length: int
    productivity: float
    initial_individual_wealth: float
    daily_salary: float
    daily_living_cost: float
    periodic_recruit_count: int
    max_age: int


class WorldState(pydantic.BaseModel):
    seed: WorldSeed
    date: int
    people_states: dict[str, PersonState]
    total_reward: float
    fiscal_period: int


ImmutableWorldState: typing.TypeAlias = WorldState


class WorldStrategy(abc.ABC):
    @abc.abstractmethod
    def distribute_rewards(self, *, state: WorldState) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def person_act(self, *, state: ImmutableWorldState, identity: str) -> float:
        raise NotImplementedError()

    @abc.abstractmethod
    def generate_recruit_candidates(
        self, *, state: ImmutableWorldState
    ) -> typing.Iterable[PersonSeed]:
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
        self._recruit_people()
        self._strategy.on_end_of_period(state=self._state)

    def run_day(self) -> None:
        for state in list(self._state.people_states.values()):
            self._person_act(state)
        self._strategy.on_end_of_day(state=self._state)

    def _person_act(self, pstate: PersonState) -> None:
        self._strategy.on_before_person_acts(
            state=self._state, identity=pstate.seed.identity
        )

        contribution = self._strategy.person_act(
            state=self._state, identity=pstate.seed.identity
        )

        pstate.wealth += self._state.seed.daily_salary
        pstate.contributions += contribution
        self._state.total_reward += (
            (1 - pstate.seed.selfishness)
            * self._state.seed.productivity
            * self._state.seed.daily_salary
        )

        self._strategy.on_after_person_acts(
            state=self._state, identity=pstate.seed.identity
        )

    def _recruit_people(self) -> None:
        for seed in self._strategy.generate_recruit_candidates(state=self._state):
            self._state.people_states[seed.identity] = PersonState(
                seed=seed,
                age=0,
                wealth=self._state.seed.initial_individual_wealth,
                contributions=0,
            )


def create_world(seed: WorldSeed, strategy: WorldStrategy) -> World:
    state = WorldState(
        seed=seed,
        date=0,
        people_states={
            p.identity: PersonState(seed=p, wealth=seed.initial_individual_wealth)
            for p in seed.initial_people
        },
        total_reward=0,
        fiscal_period=0,
    )

    return World(state=state, strategy=strategy)
