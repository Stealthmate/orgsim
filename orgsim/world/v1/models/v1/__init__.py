import typing

import numpy as np
import pandas as pd
import pydantic

from orgsim.world.v1 import base, explore

TimeSeriesEntry: typing.TypeAlias = tuple[int, int, float]


class TimeSeriesClass(pydantic.BaseModel):
    label_mapping: dict[int, base.Labels]
    series: dict[int, list[TimeSeriesEntry]]


class MetricsData(pydantic.BaseModel):
    series_classes: dict[str, TimeSeriesClass]


class Metrics(base.Metrics, explore.MetricsStore):
    def __init__(self) -> None:
        self._data = MetricsData(series_classes={})

    def get_config(self) -> base.MetricsConfig:
        return base.MetricsConfig(daily=True, fiscal=True)

    def log(
        self,
        *,
        state: base.BaseWorldState,
        name: str,
        value: float,
        labels: typing.Optional[base.Labels] = None,
    ) -> None:
        if name not in self._data.series_classes:
            self._data.series_classes[name] = TimeSeriesClass(
                label_mapping={}, series={}
            )
        sc = self._data.series_classes[name]

        the_labels = labels if labels else {}
        lid = self._generate_labels_identity(the_labels)
        if lid not in sc.label_mapping:
            sc.label_mapping[lid] = the_labels
        if lid not in sc.series:
            sc.series[lid] = []

        ts = sc.series[lid]
        ts.append((state.date, state.fiscal_period, value))

    def _generate_labels_identity(self, labels: base.Labels) -> int:
        return hash(frozenset(list(labels.items())))

    def get_series_in_class(
        self, name: str, filter_labels: typing.Optional[base.Labels] = None
    ) -> typing.Iterable[tuple[pd.DataFrame, base.Labels]]:
        if name not in self._data.series_classes:
            raise Exception(f"No such series class: {name}")
        sc = self._data.series_classes[name]

        the_filter_labels = filter_labels if filter_labels else {}
        for lid, labels in sc.label_mapping.items():
            if not all(
                (fk in labels) and (labels[fk] == fv)
                for fk, fv in the_filter_labels.items()
            ):
                continue
            yield (
                pd.DataFrame(sc.series[lid], columns=["date", "period", "value"]),
                labels,
            )

    def get_fiscal_series(
        self, name: str, labels: typing.Optional[base.Labels] = None
    ) -> "pd.Series[float]":
        if name not in self._data.series_classes:
            raise Exception(f"No such series class: {name}")
        sc = self._data.series_classes[name]

        the_labels = labels if labels is not None else {}
        lid = self._generate_labels_identity(the_labels)
        if lid not in sc.label_mapping or lid not in sc.series:
            raise Exception(f"Series {name} does not have label set: {the_labels}")

        series = sc.series[lid]
        return pd.Series([s[2] for s in series], index=[s[1] for s in series])


class CandidatePublicData(pydantic.BaseModel):
    pass


class CandidatePrivateData(pydantic.BaseModel):
    selfishness: float


Candidate = base.Candidate[CandidatePublicData, CandidatePrivateData]


class OrgSeed(pydantic.BaseModel):
    recruit_count_per_period: int


class OrgState(pydantic.BaseModel):
    seed: OrgSeed
    recruited_this_period: int

    @classmethod
    def from_seed(cls, seed: OrgSeed) -> typing.Self:
        return cls(seed=seed, recruited_this_period=0)


class NatureSeed(pydantic.BaseModel):
    initial_candidates: list[CandidatePrivateData]


class NatureState(pydantic.BaseModel):
    seed: NatureSeed
    identity_counter: int

    @classmethod
    def from_seed(cls, seed: NatureSeed) -> typing.Self:
        return cls(seed=seed, identity_counter=0)


class IndividualState(pydantic.BaseModel):
    candidate: Candidate
    age: int


class CommonSeed(pydantic.BaseModel):
    daily_salary: float
    daily_living_cost: float
    productivity: float
    max_age: int
    initial_individual_reward: float


class CommonState(pydantic.BaseModel):
    seed: CommonSeed
    total_reward: float
    individual_contributions: dict[str, float]
    individual_rewards: dict[str, float]

    @classmethod
    def from_seed(cls, seed: CommonSeed) -> typing.Self:
        return cls(
            seed=seed,
            total_reward=0,
            individual_contributions={},
            individual_rewards={},
        )


State = base.State[OrgState, NatureState, IndividualState, CommonState]


class Individual(base.Individual[OrgState, NatureState, IndividualState, CommonState]):
    def init(
        self,
        *,
        state: State,
        identity: str,
    ) -> None:
        istate = state.individuals[identity]
        istate.age = 0

        cstate = state.common_state
        cstate.individual_contributions[identity] = 0
        cstate.individual_rewards[identity] = cstate.seed.initial_individual_reward

    def act(
        self,
        *,
        state: State,
        identity: str,
    ) -> bool:
        cstate = state.common_state
        istate = state.individuals[identity]
        contribution = istate.candidate.private_data.selfishness
        cstate.individual_contributions[identity] += contribution
        cstate.total_reward += contribution * cstate.seed.productivity
        cstate.individual_rewards[identity] += cstate.seed.daily_salary
        cstate.individual_rewards[identity] -= cstate.seed.daily_living_cost
        if cstate.individual_rewards[identity] <= 0:
            return True

        istate.age += 1
        return istate.age > cstate.seed.max_age * state.base.seed.fiscal_length

    def die(self, *, state: State, identity: str) -> None:
        return


class Nature(
    base.Nature[
        OrgState,
        NatureState,
        IndividualState,
        CommonState,
        CandidatePublicData,
        CandidatePrivateData,
    ]
):
    def init(self, *, state: State) -> None:
        state.nature.identity_counter = 0

    def act_on_individual(
        self,
        *,
        state: State,
        identity: str,
    ) -> bool:
        return False

    def generate_candidates(
        self,
        *,
        state: State,
        role_models: dict[str, float],
    ) -> typing.Iterable[tuple[str, Candidate]]:
        m = np.average(
            [
                state.individuals[i].candidate.private_data.selfishness
                for i in role_models.keys()
            ]
        )
        N = 10
        while True:
            rands = np.random.normal(loc=m, scale=0.05, size=N)
            for r in rands:
                identity = self._generate_identity(state=state.nature)
                yield (
                    identity,
                    Candidate(
                        public_data=CandidatePublicData(),
                        private_data=CandidatePrivateData(selfishness=r),
                    ),
                )

    def _generate_identity(self, state: NatureState) -> str:
        state.identity_counter += 1
        return str(state.identity_counter)

    def generate_individual(
        self,
        *,
        candidate: Candidate,
    ) -> tuple[Individual, IndividualState]:
        return (Individual(), IndividualState(candidate=candidate, age=0))

    def generate_initial_individuals(
        self, state: NatureState
    ) -> dict[
        str,
        tuple[
            base.Individual[OrgState, NatureState, IndividualState, CommonState],
            IndividualState,
        ],
    ]:
        result: dict[
            str,
            tuple[
                base.Individual[OrgState, NatureState, IndividualState, CommonState],
                IndividualState,
            ],
        ] = {}
        for c in state.seed.initial_candidates:
            result[self._generate_identity(state)] = (
                Individual(),
                IndividualState(
                    candidate=Candidate(
                        public_data=CandidatePublicData(), private_data=c
                    ),
                    age=0,
                ),
            )

        return result


class Org(
    base.Org[
        OrgState,
        NatureState,
        IndividualState,
        CommonState,
        CandidatePublicData,
    ]
):
    def init(self, state: State, initial_people: set[str]) -> None:
        state.org.recruited_this_period = 0

    def react_to_individual(
        self,
        *,
        state: State,
        identity: str,
        dead: bool,
    ) -> None:
        return

    def recruit(
        self,
        *,
        state: State,
        identity: str,
        candidate: CandidatePublicData,
    ) -> None:
        state.org.recruited_this_period += 1

    def evaluate_individuals(self, *, state: State) -> dict[str, float]:
        state.org.recruited_this_period = 0
        return {i: 1.0 for i in state.individuals.keys()}

    def evaluate_candidate(
        self,
        *,
        state: State,
        candidate: CandidatePublicData,
    ) -> bool:
        if state.org.recruited_this_period >= state.org.seed.recruit_count_per_period:
            raise StopIteration()
        return True


class Seed(pydantic.BaseModel):
    base: base.BaseWorldSeed
    org: OrgSeed
    nature: NatureSeed
    common: CommonSeed


def create_model(
    seed: Seed, metrics: base.Metrics
) -> base.World[
    OrgState,
    NatureState,
    IndividualState,
    CommonState,
    CandidatePublicData,
    CandidatePrivateData,
]:
    nature = Nature()
    return base.World(
        config=base.WorldConfig(
            state=State(
                base=base.BaseWorldState.from_seed(seed.base),
                org=OrgState.from_seed(seed.org),
                individuals={},
                nature=NatureState.from_seed(seed.nature),
                common_state=CommonState.from_seed(seed.common),
            ),
            org=Org(),
            individuals={},
            nature=nature,
            metrics=metrics,
        )
    )
