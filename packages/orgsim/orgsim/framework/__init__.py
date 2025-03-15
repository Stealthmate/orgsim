import abc
import typing

import pydantic

T = typing.TypeVar("T", bound=pydantic.BaseModel)


class PersonState(pydantic.BaseModel, typing.Generic[T]):
    seed: T
    identity: str
    age: int = 0
    wealth: float = 0.0
    contributions: float = 0


class WorldSeed(pydantic.BaseModel, typing.Generic[T]):
    initial_people: set[T]
    fiscal_length: int
    productivity: float
    initial_individual_wealth: float
    daily_salary: float
    daily_living_cost: float
    periodic_recruit_count: int
    max_age: int


class WorldTime(pydantic.BaseModel):
    date: int
    fiscal_period: int


class WorldState(pydantic.BaseModel, typing.Generic[T]):
    seed: WorldSeed[T]
    people_states: dict[str, PersonState[T]]
    total_reward: float
    time: WorldTime


type ImmutableWorldState[T] = WorldState[T]


class WorldStrategy(abc.ABC, typing.Generic[T]):
    @abc.abstractmethod
    def generate_identity(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def distribute_rewards(self, *, state: WorldState[T]) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def person_act(self, *, state: ImmutableWorldState[T], identity: str) -> float:
        raise NotImplementedError()

    @abc.abstractmethod
    def pick_role_models(
        self, *, state: ImmutableWorldState[T]
    ) -> typing.Iterable[str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def generate_recruits(
        self, *, seed: WorldSeed[T], role_models: typing.Iterable[T]
    ) -> typing.Iterable[T]:
        raise NotImplementedError()

    @abc.abstractmethod
    def on_before_person_acts(self, *, state: WorldState[T], identity: str) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def on_after_person_acts(self, *, state: WorldState[T], identity: str) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def on_end_of_day(self, *, state: WorldState[T]) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def on_end_of_period(self, *, state: WorldState[T]) -> None:
        raise NotImplementedError()


class World(typing.Generic[T]):
    def __init__(self, *, state: WorldState[T], strategy: WorldStrategy[T]) -> None:
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

        self._state.time.fiscal_period += 1

    def run_day(self) -> None:
        for state in list(self._state.people_states.values()):
            self._person_act(state)
        self._strategy.on_end_of_day(state=self._state)
        self._state.time.date += 1

    def _person_act(self, pstate: PersonState[T]) -> None:
        self._strategy.on_before_person_acts(
            state=self._state, identity=pstate.identity
        )

        contribution = self._strategy.person_act(
            state=self._state, identity=pstate.identity
        )

        pstate.wealth += self._state.seed.daily_salary
        pstate.contributions += contribution
        self._state.total_reward += (
            contribution * self._state.seed.productivity * self._state.seed.daily_salary
        )

        self._strategy.on_after_person_acts(state=self._state, identity=pstate.identity)

    def _recruit_people(self) -> None:
        role_models = [
            self._state.people_states[i].seed
            for i in self._strategy.pick_role_models(state=self._state)
        ]
        for seed in self._strategy.generate_recruits(
            seed=self._state.seed, role_models=role_models
        ):
            identity = self._strategy.generate_identity()
            self._state.people_states[identity] = PersonState(
                seed=seed,
                identity=identity,
                age=0,
                wealth=self._state.seed.initial_individual_wealth,
                contributions=0,
            )


def create_world(seed: WorldSeed[T], strategy: WorldStrategy[T]) -> World[T]:
    identities = [strategy.generate_identity() for _ in range(len(seed.initial_people))]
    state = WorldState(
        seed=seed,
        people_states={
            i: PersonState(seed=p, identity=i, wealth=seed.initial_individual_wealth)
            for p, i in zip(seed.initial_people, identities)
        },
        total_reward=0,
        time=WorldTime(date=0, fiscal_period=0),
    )

    return World(state=state, strategy=strategy)
