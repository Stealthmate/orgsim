import pydantic


class PublicIndividualData(pydantic.BaseModel):
    pass


class OrgIndividualState(pydantic.BaseModel):
    public_data: PublicIndividualData
    contribution: float


class IndividualData(pydantic.BaseModel):
    accumulated_value: float
    wealth: float
    base_production: float
    salary: float
    cost_of_living: float
    contribution: float


class GameState(pydantic.BaseModel):
    period: int
    individuals: dict[str, IndividualData]
    org_wealth: float
    shareholder_value: float


class StateView:
    def __init__(self, state: GameState) -> None:
        self.state = state


class IndividualState:
    def __init__(self, state: GameState, identity: str) -> None:
        self._state = state
        self._identity = identity

    @property
    def public_data(self) -> PublicIndividualData:
        raise NotImplementedError()

    @public_data.setter
    def public_data(self, v: PublicIndividualData) -> None:
        raise NotImplementedError()

    @property
    def wealth(self) -> float:
        raise NotImplementedError()

    @wealth.setter
    def wealth(self, v: float) -> None:
        raise NotImplementedError()

    @property
    def salary(self) -> float:
        raise NotImplementedError()

    @property
    def cost_of_living(self) -> float:
        raise NotImplementedError()

    @cost_of_living.setter
    def cost_of_living(self, v: float) -> None:
        raise NotImplementedError()


class OrgState(StateView):
    @property
    def wealth(self) -> float:
        return self.state.org_wealth

    @wealth.setter
    def wealth(self, v: float) -> None:
        self.state.org_wealth = v

    @property
    def individuals(self) -> set[str]:
        return set(self.state.individuals.keys())

    def get_salary_for(self, identity: str) -> float:
        return self.state.individuals[identity].salary
