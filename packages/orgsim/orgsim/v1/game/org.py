import abc

from . import metrics


class OrgState(abc.ABC):
    @property
    @abc.abstractmethod
    def population(self) -> int:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def individuals(self) -> set[str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def salary_of(self, identity: str) -> float:
        raise NotImplementedError()

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
    def shareholder_value(self) -> float:
        raise NotImplementedError()

    @shareholder_value.setter
    @abc.abstractmethod
    def shareholder_value(self, v: float) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def pay_individual(self, identity: str, v: float) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def deduct_cost_of_living(self, identity: str) -> bool:
        raise NotImplementedError()


class Org:
    def __init__(
        self,
        *,
        state: OrgState,
        metrics: metrics.MetricsLogger,
    ) -> None:
        self._state = state
        self._metrics = metrics

    def play(self) -> set[str]:
        dead = set()
        if self._state.population > 0:
            dead = self.pay_employees()

        self.pay_shareholders()

        self.re_evaluate_salaries(dead)

        return dead

    def pay_employees(self) -> set[str]:
        total_salaries = sum(self._state.salary_of(i) for i in self._state.individuals)
        insufficiency_coef = min(self._state.wealth / total_salaries, 1.0)

        # bonuses = org.compute_bonuses(ostate)

        dead_individuals: set[str] = set()

        for identity in self._state.individuals:
            salary = insufficiency_coef * self._state.salary_of(identity)
            self._state.pay_individual(identity, salary)
            # self._mutator.pay_bonus(identity, bonuses[identity])
            dead = self._state.deduct_cost_of_living(identity)
            if dead:
                dead_individuals.add(identity)

        return dead_individuals

    def pay_shareholders(self) -> None:
        self._state.shareholder_value += self._state.wealth
        self._state.wealth = 0

    def re_evaluate_salaries(self, dead: set[str]) -> None:
        pass
        # new_salaries = org.re_evaluate_salaries(ostate)
        # for identity in self._config.individuals.keys():
        #     self._mutator.update_salary(identity, new_salaries[identity])
