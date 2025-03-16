import typing

import pydantic

from . import individual, metrics, org, seed as seed_


class SharedStateData(pydantic.BaseModel, typing.Generic[seed_.IndividualSeed]):
    seed: seed_.Seed[seed_.IndividualSeed]
    date: int
    period: int
    org_wealth: float
    shareholder_value: float

    @classmethod
    def from_seed(cls, seed: seed_.Seed[seed_.IndividualSeed]) -> typing.Self:
        return cls(
            seed=seed,
            date=0,
            period=0,
            org_wealth=seed.initial_org_wealth,
            shareholder_value=0,
        )


class PeriodicIndividualStateData(pydantic.BaseModel):
    contribution: float
    starting_unit_production: float


class IndividualStateData(pydantic.BaseModel):
    identity: str
    stats: individual.IndividualStats
    periodic: PeriodicIndividualStateData

    @classmethod
    def from_stats(
        cls, identity: str, stats: individual.IndividualStats
    ) -> typing.Self:
        return cls(
            identity=identity,
            stats=stats,
            periodic=PeriodicIndividualStateData(
                contribution=0, starting_unit_production=stats.unit_production
            ),
        )


class IndividualStates(pydantic.BaseModel):
    d: dict[str, IndividualStateData]


class IndividualStateImpl(
    individual.IndividualState, typing.Generic[seed_.IndividualSeed]
):
    def __init__(
        self,
        individual_state: IndividualStateData,
        shared_state: SharedStateData[seed_.IndividualSeed],
    ) -> None:
        self._individual_state = individual_state
        self._shared_state = shared_state

    @property
    def identity(self) -> str:
        return self._individual_state.identity

    @property
    def contribution(self) -> float:
        return self._individual_state.periodic.contribution

    def contribute(self, v: float) -> None:
        self._individual_state.periodic.contribution += v
        self._shared_state.org_wealth += self._shared_state.seed.org_productivity * v

    @property
    def stats(self) -> individual.IndividualStats:
        return self._individual_state.stats


class OrgStateImpl(org.OrgState, typing.Generic[seed_.IndividualSeed]):
    def __init__(
        self,
        shared_state: SharedStateData[seed_.IndividualSeed],
        individuals: IndividualStates,
    ) -> None:
        self._shared_state = shared_state
        self._individuals = individuals

    @property
    def wealth(self) -> float:
        return self._shared_state.org_wealth

    @wealth.setter
    def wealth(self, v: float) -> None:
        self._shared_state.org_wealth = v

    @property
    def population(self) -> int:
        return len(self._individuals.d)

    @property
    def individuals(self) -> set[str]:
        return set(self._individuals.d.keys())

    def salary_of(self, identity: str) -> float:
        return self._individuals.d[identity].stats.salary

    @property
    def shareholder_value(self) -> float:
        return self._shared_state.shareholder_value

    @shareholder_value.setter
    def shareholder_value(self, v: float) -> None:
        self._shared_state.shareholder_value = v

    def pay_individual(self, identity: str, v: float) -> None:
        self._individuals.d[identity].stats.wealth += v
        self._shared_state.org_wealth -= v

    def deduct_cost_of_living(self, identity: str) -> bool:
        istats = self._individuals.d[identity].stats
        istats.wealth -= istats.cost_of_living
        return istats.wealth < 0


class MetricsState(metrics.MetricsState, typing.Generic[seed_.IndividualSeed]):
    def __init__(
        self,
        shared: SharedStateData[seed_.IndividualSeed],
        individuals: IndividualStates,
    ) -> None:
        self._shared = shared
        self._individuals = individuals

    @property
    def date(self) -> int:
        return self._shared.date

    @property
    def period(self) -> int:
        return self._shared.period

    @property
    def population(self) -> int:
        return len(self._individuals.d)

    def wealth_of(self, identity: str) -> float:
        return self._individuals.d[identity].stats.wealth

    def contribution_of(self, identity: str) -> float:
        return self._individuals.d[identity].periodic.contribution

    def score_of(self, identity: str) -> float:
        return self._individuals.d[identity].stats.score

    def unit_production_of(self, identity: str) -> float:
        return self._individuals.d[identity].stats.unit_production


class StateData(pydantic.BaseModel, typing.Generic[seed_.IndividualSeed]):
    shared: SharedStateData[seed_.IndividualSeed]
    individual_states: IndividualStates
    individuals: dict[str, individual.Individual]
    org: org.Org
    factory: seed_.Factory[seed_.IndividualSeed]
    metrics: metrics.MetricsLogger

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_seed(
        cls,
        seed: seed_.Seed[seed_.IndividualSeed],
        factory: seed_.Factory[seed_.IndividualSeed],
    ) -> typing.Self:
        shared = SharedStateData.from_seed(seed)
        individual_states = {}
        for iseed in seed.initial_individuals:
            (i, istats, strategy) = factory.create_individual(iseed)
            istate = IndividualStateData.from_stats(i, istats)
            individual_states[i] = istate

        ids = IndividualStates(d=individual_states)
        metrics_ = metrics.MetricsLogger(
            state=MetricsState(shared, individuals=ids),
            metrics=metrics.Metrics(metrics.MetricsData(series_classes={})),
        )

        individuals = {}
        for i, istate in individual_states.items():
            individuals[i] = individual.Individual(
                strategy=strategy,
                state=IndividualStateImpl(istate, shared_state=shared),
                metrics=metrics_,
            )

        return cls(
            shared=shared,
            individual_states=ids,
            individuals=individuals,
            org=org.Org(
                state=OrgStateImpl(shared, individuals=ids),
                metrics=metrics_,
            ),
            factory=factory,
            metrics=metrics_,
        )


class GameState(typing.Generic[seed_.IndividualSeed]):
    @classmethod
    def from_seed(
        cls,
        seed: seed_.Seed[seed_.IndividualSeed],
        factory: seed_.Factory[seed_.IndividualSeed],
    ) -> typing.Self:
        return cls(StateData.from_seed(seed, factory))

    def __init__(self, data: StateData[seed_.IndividualSeed]) -> None:
        self._data = data

    @property
    def periods(self) -> int:
        return self._data.shared.seed.periods

    @property
    def days_in_period(self) -> int:
        return self._data.shared.seed.days_in_period

    @property
    def shareholder_value(self) -> float:
        return self._data.shared.shareholder_value

    def score_of(self, identity: str) -> float:
        return self._data.individual_states.d[identity].stats.score

    def obj_of(self, identity: str) -> individual.Individual:
        return self._data.individuals[identity]

    @property
    def individuals(self) -> set[str]:
        return set(self._data.individuals.keys())

    def advance_date(self) -> None:
        self._data.shared.date += 1

    def advance_period(self) -> None:
        self._data.shared.period += 1

    @property
    def org(self) -> org.Org:
        return self._data.org

    def delete_individual(self, identity: str) -> None:
        del self._data.individuals[identity]
        del self._data.individual_states.d[identity]

    @property
    def metrics(self) -> metrics.MetricsLogger:
        return self._data.metrics
