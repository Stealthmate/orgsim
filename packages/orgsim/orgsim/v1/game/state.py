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
    stats: individual.IndividualStats
    periodic: PeriodicIndividualStateData

    @classmethod
    def from_stats(cls, stats: individual.IndividualStats) -> typing.Self:
        return cls(
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
        raise NotImplementedError()

    @property
    def cost_of_living(self) -> float:
        raise NotImplementedError()

    @cost_of_living.setter
    def cost_of_living(self, v: float) -> None:
        raise NotImplementedError()

    @property
    def stats(self) -> individual.IndividualStats:
        raise NotImplementedError()

    @property
    def salary(self) -> float:
        raise NotImplementedError()

    @property
    def wealth(self) -> float:
        raise NotImplementedError()

    @wealth.setter
    def wealth(self, v: float) -> None:
        raise NotImplementedError()


class OrgStateImpl(org.OrgState, typing.Generic[seed_.IndividualSeed]):
    def __init__(self, shared_state: SharedStateData[seed_.IndividualSeed]) -> None:
        self._shared_state = shared_state

    @property
    def population(self) -> int:
        raise NotImplementedError()


class MetricsState(metrics.MetricsState, typing.Generic[seed_.IndividualSeed]):
    def __init__(self, shared: SharedStateData[seed_.IndividualSeed]) -> None:
        self._shared = shared

    @property
    def date(self) -> int:
        raise NotImplementedError()

    @property
    def period(self) -> int:
        raise NotImplementedError()

    @property
    def population(self) -> int:
        raise NotImplementedError()

    def wealth_of(self, identity: str) -> float:
        raise NotImplementedError()

    def contribution_of(self, identity: str) -> float:
        raise NotImplementedError()

    def score_of(self, identity: str) -> float:
        raise NotImplementedError()


class StateData(pydantic.BaseModel, typing.Generic[seed_.IndividualSeed]):
    shared: SharedStateData[seed_.IndividualSeed]
    individuals: dict[str, tuple[IndividualStateData, individual.Individual]]
    org: org.Org
    factory: seed_.Factory[seed_.IndividualSeed]

    @classmethod
    def from_seed(
        cls,
        seed: seed_.Seed[seed_.IndividualSeed],
        factory: seed_.Factory[seed_.IndividualSeed],
    ) -> typing.Self:
        shared = SharedStateData.from_seed(seed)
        individuals = {}
        metrics_ = metrics.MetricsLogger(
            state=MetricsState(shared),
            metrics=metrics.Metrics(metrics.MetricsData(series_classes={})),
        )
        for iseed in seed.initial_individuals:
            (i, istats, strategy) = factory.create_individual(iseed)
            istate = IndividualStateData.from_stats(istats)
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
        raise NotImplementedError()

    @property
    def days_in_period(self) -> int:
        raise NotImplementedError()

    @property
    def shareholder_value(self) -> float:
        raise NotImplementedError()

    def value_of(self, identity: str) -> float:
        raise NotImplementedError()

    def obj_of(self, identity: str) -> individual.Individual:
        raise NotImplementedError()

    @property
    def individuals(self) -> set[str]:
        raise NotImplementedError()

    def advance_date(self) -> None:
        raise NotImplementedError()

    def advance_period(self) -> None:
        raise NotImplementedError()

    @property
    def org(self) -> org.Org:
        raise NotImplementedError()

    def delete_individual(self, identity: str) -> None:
        raise NotImplementedError()

    @property
    def metrics(self) -> metrics.MetricsLogger:
        raise NotImplementedError()
