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
    def wealth(self) -> float:
        raise NotImplementedError()

    @wealth.setter
    @abc.abstractmethod
    def wealth(self, v: float) -> None:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def salary(self) -> float:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def cost_of_living(self) -> float:
        raise NotImplementedError()

    @cost_of_living.setter
    @abc.abstractmethod
    def cost_of_living(self, v: float) -> None:
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


class IndividualStrategy(abc.ABC):
    @abc.abstractmethod
    def compute_work_coefficient(self, state: IndividualStrategyStateView) -> float:
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
        raise NotImplementedError()

    def do_self_improvement(self, k: float) -> None:
        raise NotImplementedError()
