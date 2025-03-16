import abc
import typing

import pydantic

from . import individual

IndividualSeed = typing.TypeVar("IndividualSeed")


class Factory(abc.ABC, typing.Generic[IndividualSeed]):
    @abc.abstractmethod
    def create_individual(
        self, seed: IndividualSeed
    ) -> tuple[str, individual.IndividualStats, individual.IndividualStrategy]:
        raise NotImplementedError()


class Seed(pydantic.BaseModel, typing.Generic[IndividualSeed]):
    periods: int
    days_in_period: int
    initial_individuals: list[IndividualSeed]
    initial_org_wealth: float
    org_productivity: float
    production_to_value_coef: float
    max_invest_coef: float
