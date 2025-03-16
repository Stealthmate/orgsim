import abc

import pydantic

from . import metrics


class IndividualStats(pydantic.BaseModel):
    score: float
    wealth: float
    unit_production: float
    salary: float
    cost_of_living: float


class IndividualStrategyStateView(abc.ABC):
    @property
    @abc.abstractmethod
    def stats(self) -> IndividualStats:
        raise NotImplementedError()


class IndividualStrategy(abc.ABC):
    @abc.abstractmethod
    def compute_work_coefficient(self, state: IndividualStrategyStateView) -> float:
        raise NotImplementedError()


class IndividualState(IndividualStrategyStateView, abc.ABC):
    @property
    @abc.abstractmethod
    def identity(self) -> str:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def stats(self) -> IndividualStats:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def contribution(self) -> float:
        raise NotImplementedError()

    @abc.abstractmethod
    def contribute(self, v: float) -> None:
        raise NotImplementedError()


class Individual:
    def __init__(
        self,
        *,
        strategy: IndividualStrategy,
        state: IndividualState,
        metrics: metrics.MetricsLogger,
    ) -> None:
        self._strategy = strategy
        self._state = state
        self._metrics = metrics

    def play(self) -> None:
        k = self._strategy.compute_work_coefficient(self._state)

        self.do_work(k)
        self.do_self_improvement(1 - k)
        self._metrics.log_individual(self._state.identity)

    def do_work(self, k: float) -> None:
        stats = self._state.stats
        production = k * stats.unit_production
        self._state.contribute(production)

    def do_self_improvement(self, k: float) -> None:
        stats = self._state.stats
        percentage = k * 0.05
        investment = percentage * max(stats.score, 10_000)

        if stats.wealth < investment:
            return

        stats.score += investment
        stats.cost_of_living *= 1 + percentage
        stats.wealth -= investment
