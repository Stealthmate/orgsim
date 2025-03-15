import abc

from . import state


class Org(abc.ABC):
    @abc.abstractmethod
    def compute_bonuses(self, state: state.OrgState) -> dict[str, float]:
        raise NotImplementedError()

    @abc.abstractmethod
    def compute_shareholder_value(self, state: state.OrgState) -> float:
        raise NotImplementedError()

    @abc.abstractmethod
    def re_evaluate_salaries(self, state: state.OrgState) -> dict[str, float]:
        raise NotImplementedError()


class Individual(abc.ABC):
    @abc.abstractmethod
    def get_public_data(self) -> state.PublicIndividualData:
        raise NotImplementedError()

    @abc.abstractmethod
    def compute_work_coefficient(self, state: state.IndividualState) -> float:
        raise NotImplementedError()
