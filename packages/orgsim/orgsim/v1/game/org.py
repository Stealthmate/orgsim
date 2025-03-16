import abc

from . import metrics


class OrgState(abc.ABC):
    @property
    @abc.abstractmethod
    def population(self) -> int:
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

        return dead

    def pay_employees(self) -> set[str]:
        raise NotImplementedError()
        # org = self._config.org
        # ostate = state.OrgState(self._config.state)

        # total_salaries = sum(v.salary for v in self._config.state.individuals.values())
        # insufficiency_coef = min(self._config.state.org_wealth / total_salaries, 1.0)

        # bonuses = org.compute_bonuses(ostate)

        # for identity in self._mutator.individuals:
        #     self._mutator.pay_salary(identity, insufficiency_coef)
        #     self._mutator.pay_bonus(identity, bonuses[identity])
        #     self._mutator.deduct_cost_of_living(identity)

        # self._mutator.pay_shareholder_value(org.compute_shareholder_value(ostate))

        # new_salaries = org.re_evaluate_salaries(ostate)
        # for identity in self._config.individuals.keys():
        #     self._mutator.update_salary(identity, new_salaries[identity])

    def pay_shareholders(self) -> None:
        raise NotImplementedError()
