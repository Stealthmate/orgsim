import abc
import typing

import pydantic

OrgState = typing.TypeVar("OrgState")
NatureState = typing.TypeVar("NatureState")
IndividualState = typing.TypeVar("IndividualState")
CommonState = typing.TypeVar("CommonState")
CandidatePublicData = typing.TypeVar("CandidatePublicData")
CandidatePrivateData = typing.TypeVar("CandidatePrivateData")


class State(
    pydantic.BaseModel,
    typing.Generic[OrgState, NatureState, IndividualState, CommonState],
):
    org: OrgState
    nature: NatureState
    individuals: dict[str, IndividualState]
    common_state: CommonState


class Candidate(
    pydantic.BaseModel, typing.Generic[CandidatePublicData, CandidatePrivateData]
):
    public_data: CandidatePublicData
    private_data: CandidatePrivateData


class BaseWorldSeed(pydantic.BaseModel):
    fiscal_length: int


class BaseWorldState(pydantic.BaseModel):
    seed: BaseWorldSeed
    date: int
    fiscal_period: int
    n_fiscal_suicides: int
    n_fiscal_killed: int

    @classmethod
    def from_seed(cls, seed: BaseWorldSeed) -> typing.Self:
        return cls(
            seed=seed, date=0, fiscal_period=0, n_fiscal_suicides=0, n_fiscal_killed=0
        )


Labels: typing.TypeAlias = dict[str, str]


class MetricsConfig(pydantic.BaseModel):
    daily: bool
    fiscal: bool


class Metrics(abc.ABC):
    POPULATION: str = "population"
    SUICIDES: str = "suicides"
    KILLED: str = "killed"
    RECRUITED: str = "recruited"

    @abc.abstractmethod
    def get_config(self) -> MetricsConfig:
        raise NotImplementedError()

    @abc.abstractmethod
    def log(
        self,
        *,
        state: BaseWorldState,
        name: str,
        value: float,
        labels: typing.Optional[Labels] = None,
    ) -> None:
        raise NotImplementedError()


class Individual(
    abc.ABC, typing.Generic[OrgState, NatureState, IndividualState, CommonState]
):
    @abc.abstractmethod
    def init(
        self,
        *,
        state: State[OrgState, NatureState, IndividualState, CommonState],
        identity: str,
    ) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def act(
        self,
        *,
        state: State[OrgState, NatureState, IndividualState, CommonState],
        identity: str,
    ) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def die(
        self,
        *,
        state: State[OrgState, NatureState, IndividualState, CommonState],
        identity: str,
    ) -> None:
        raise NotImplementedError()


class Nature(
    abc.ABC,
    typing.Generic[
        OrgState,
        NatureState,
        IndividualState,
        CommonState,
        CandidatePublicData,
        CandidatePrivateData,
    ],
):
    @abc.abstractmethod
    def init(
        self, *, state: State[OrgState, NatureState, IndividualState, CommonState]
    ) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def act_on_individual(
        self,
        *,
        state: State[OrgState, NatureState, IndividualState, CommonState],
        identity: str,
    ) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def generate_candidates(
        self,
        *,
        state: State[OrgState, NatureState, IndividualState, CommonState],
        role_models: dict[str, float],
    ) -> typing.Iterable[
        tuple[str, Candidate[CandidatePublicData, CandidatePrivateData]]
    ]:
        raise NotImplementedError()

    @abc.abstractmethod
    def generate_individual(
        self, *, candidate: Candidate[CandidatePublicData, CandidatePrivateData]
    ) -> Individual[OrgState, NatureState, IndividualState, CommonState]:
        raise NotImplementedError()


class Org(
    abc.ABC,
    typing.Generic[
        OrgState, NatureState, IndividualState, CommonState, CandidatePublicData
    ],
):
    @abc.abstractmethod
    def init(
        self,
        *,
        state: State[OrgState, NatureState, IndividualState, CommonState],
        initial_people: set[str],
    ) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def react_to_individual(
        self,
        *,
        state: State[OrgState, NatureState, IndividualState, CommonState],
        identity: str,
        dead: bool,
    ) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def recruit(
        self,
        *,
        state: State[OrgState, NatureState, IndividualState, CommonState],
        identity: str,
        candidate: CandidatePublicData,
    ) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def evaluate_individuals(
        self, *, state: State[OrgState, NatureState, IndividualState, CommonState]
    ) -> dict[str, float]:
        raise NotImplementedError()

    @abc.abstractmethod
    def evaluate_candidate(
        self,
        *,
        state: State[OrgState, NatureState, IndividualState, CommonState],
        candidate: CandidatePublicData,
    ) -> bool:
        raise NotImplementedError()


class WorldConfig(
    pydantic.BaseModel,
    typing.Generic[
        OrgState,
        NatureState,
        IndividualState,
        CommonState,
        CandidatePublicData,
        CandidatePrivateData,
    ],
):
    base_state: BaseWorldState
    state: State[OrgState, NatureState, IndividualState, CommonState]
    org: Org[OrgState, NatureState, IndividualState, CommonState, CandidatePublicData]
    individuals: dict[
        str, Individual[OrgState, NatureState, IndividualState, CommonState]
    ]
    nature: Nature[
        OrgState,
        NatureState,
        IndividualState,
        CommonState,
        CandidatePublicData,
        CandidatePrivateData,
    ]
    metrics: Metrics

    class Config:
        arbitrary_types_allowed = True


class World(
    typing.Generic[
        OrgState,
        NatureState,
        IndividualState,
        CommonState,
        CandidatePublicData,
        CandidatePrivateData,
    ]
):
    def __init__(
        self,
        *,
        config: WorldConfig[
            OrgState,
            NatureState,
            IndividualState,
            CommonState,
            CandidatePublicData,
            CandidatePrivateData,
        ],
    ) -> None:
        self._config = config
        self._metrics_config = self._config.metrics.get_config()

    def _log(self, name: str, value: float) -> None:
        self._config.metrics.log(state=self._config.base_state, name=name, value=value)

    def init(self) -> None:
        s = self._config.state
        self._config.nature.init(state=s)
        for identity, individual in self._config.individuals.items():
            individual.init(state=s, identity=identity)
        self._config.org.init(
            state=s, initial_people=set(self._config.individuals.keys())
        )

    def is_empty(self) -> bool:
        return len(self._config.individuals) == 0

    def run_period(self) -> None:
        for _ in range(self._config.base_state.seed.fiscal_length):
            if self.is_empty():
                return
            self.run_day()

        if self.is_empty():
            return

        if self._metrics_config.fiscal:
            self._log(Metrics.POPULATION, len(self._config.individuals.keys()))
            self._log(Metrics.SUICIDES, self._config.base_state.n_fiscal_suicides)
            self._log(Metrics.KILLED, self._config.base_state.n_fiscal_killed)

        self.perform_recruitment()
        self._config.base_state.fiscal_period += 1

    def run_day(self) -> None:
        bstate = self._config.base_state
        n_suicides = 0
        n_killed = 0

        for identity, individual in list(self._config.individuals.items()):
            dead = individual.act(state=self._config.state, identity=identity)
            n_suicides += 1 if dead else 0
            if not dead:
                dead = self._config.nature.act_on_individual(
                    state=self._config.state, identity=identity
                )
                n_killed += 1 if dead else 0

            if dead:
                self._config.individuals[identity].die(
                    state=self._config.state, identity=identity
                )
                del self._config.individuals[identity]

            self._config.org.react_to_individual(
                state=self._config.state, identity=identity, dead=dead
            )

        bstate.n_fiscal_suicides += n_suicides
        bstate.n_fiscal_killed += n_killed

        if self._metrics_config.daily:
            self._log(
                Metrics.POPULATION,
                len(self._config.individuals.keys()),
            )
            self._log(
                Metrics.SUICIDES,
                n_suicides,
            )
            self._log(
                Metrics.KILLED,
                n_killed,
            )
        self._config.base_state.date += 1

    def perform_recruitment(self) -> None:
        cs = self._config.state
        evaluations = self._config.org.evaluate_individuals(state=cs)

        candidates = self._config.nature.generate_candidates(
            state=cs, role_models=evaluations
        )

        recruited: int = 0

        try:
            for identity, candidate in candidates:
                accepted = self._config.org.evaluate_candidate(
                    state=cs, candidate=candidate.public_data
                )
                if not accepted:
                    continue
                individual = self._config.nature.generate_individual(
                    candidate=candidate
                )
                self._config.individuals[identity] = individual
                recruited += 1
                individual.init(state=self._config.state, identity=identity)
                self._config.org.recruit(
                    state=cs, identity=identity, candidate=candidate.public_data
                )
        except StopIteration:
            pass

        if self._metrics_config.fiscal:
            self._log(Metrics.RECRUITED, recruited)
