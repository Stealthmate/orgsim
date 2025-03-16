import abc
import typing

import pydantic

from . import base, state

IndividualSeed = typing.TypeVar("IndividualSeed")
OrgSeed = typing.TypeVar("OrgSeed")


class Factory(abc.ABC, typing.Generic[IndividualSeed, OrgSeed]):
    @abc.abstractmethod
    def create_individual(
        self, seed: IndividualSeed
    ) -> tuple[str, base.Individual, state.IndividualData]:
        raise NotImplementedError()

    @abc.abstractmethod
    def create_org(self, seed: OrgSeed) -> base.Org:
        raise NotImplementedError()


class Seed(pydantic.BaseModel, typing.Generic[IndividualSeed, OrgSeed]):
    periods: int
    days_in_period: int
    initial_individuals: list[IndividualSeed]
    initial_org_wealth: float
    org_productivity: float
    org_seed: OrgSeed
    production_to_value_coef: float
    max_invest_coef: float
