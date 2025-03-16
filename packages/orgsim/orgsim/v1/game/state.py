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
    def __init__(self, shared_state: SharedStateData[seed_.IndividualSeed]) -> None:
        self._shared_state = shared_state

    @property
    def population(self) -> int:
        raise NotImplementedError()


class MetricsState(metrics.MetricsState, typing.Generic[seed_.IndividualSeed]):
    def __init__(
        self,
        shared: SharedStateData[seed_.IndividualSeed],
        individuals: dict[str, IndividualStateData],
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
        raise NotImplementedError()

    def wealth_of(self, identity: str) -> float:
        return self._individuals[identity].stats.wealth

    def contribution_of(self, identity: str) -> float:
        return self._individuals[identity].periodic.contribution

    def score_of(self, identity: str) -> float:
        return self._individuals[identity].stats.score


class StateData(pydantic.BaseModel, typing.Generic[seed_.IndividualSeed]):
    shared: SharedStateData[seed_.IndividualSeed]
    individuals: dict[str, tuple[IndividualStateData, individual.Individual]]
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

        metrics_ = metrics.MetricsLogger(
            state=MetricsState(shared, individuals=individual_states),
            metrics=metrics.Metrics(metrics.MetricsData(series_classes={})),
        )

        individuals = {}
        for i, istate in individual_states.items():
            individuals[i] = (
                istate,
                individual.Individual(
                    strategy=strategy,
                    state=IndividualStateImpl(istate, shared_state=shared),
                    metrics=metrics_,
                ),
            )

        return cls(
            shared=shared,
            individuals=individuals,
            org=org.Org(state=OrgStateImpl(shared), metrics=metrics_),
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
        raise NotImplementedError()

    def value_of(self, identity: str) -> float:
        raise NotImplementedError()

    def obj_of(self, identity: str) -> individual.Individual:
        return self._data.individuals[identity][1]

    @property
    def individuals(self) -> set[str]:
        return set(self._data.individuals.keys())

    def advance_date(self) -> None:
        self._data.shared.date += 1

    def advance_period(self) -> None:
        self._data.shared.period += 1

    @property
    def org(self) -> org.Org:
        raise NotImplementedError()

    def delete_individual(self, identity: str) -> None:
        raise NotImplementedError()

    @property
    def metrics(self) -> metrics.MetricsLogger:
        return self._data.metrics
