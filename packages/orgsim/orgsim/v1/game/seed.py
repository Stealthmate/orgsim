import abc

import pydantic

from . import base, state


class IndividualSeed(pydantic.BaseModel):
    initial_wealth: float


class OrgSeed(pydantic.BaseModel):
    pass


class Factory(abc.ABC):
    @abc.abstractmethod
    def create_individual(
        self, seed: IndividualSeed
    ) -> tuple[str, base.Individual, state.IndividualData]:
        raise NotImplementedError()

    @abc.abstractmethod
    def create_org(self, seed: OrgSeed) -> base.Org:
        raise NotImplementedError()


class GameSeed(pydantic.BaseModel):
    periods: int
    days_in_period: int
    initial_individuals: list[IndividualSeed]
    initial_org_wealth: float
    org_productivity: float
    org_seed: OrgSeed
