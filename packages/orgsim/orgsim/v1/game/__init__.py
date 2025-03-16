import typing

import pydantic

from . import base, individual, metrics, org, state, seed


class Config(pydantic.BaseModel):
    seed: seed.Seed
    state: state.State
    org: base.Org
    individuals: dict[str, base.Individual]
    metrics: metrics.Metrics

    class Config:
        arbitrary_types_allowed = True


class _Game:
    @classmethod
    def from_seed(cls, seed: seed.Seed, factory: seed.Factory) -> typing.Self:
        individuals = [factory.create_individual(s) for s in seed.initial_individuals]
        config = Config(
            seed=seed,
            state=state.State(
                date=0,
                period=0,
                individuals={k: v for (k, _, v) in individuals},
                org_wealth=seed.initial_org_wealth,
                shareholder_value=0,
            ),
            org=factory.create_org(seed.org_seed),
            individuals={k: v for (k, v, _) in individuals},
            metrics=metrics.Metrics(metrics.MetricsData(series_classes={})),
        )
        return cls(config)

    def __init__(self, config: Config) -> None:
        self._config = config

    def play(self) -> None:
        for _ in range(self._config.seed.periods):
            self.play_period()

    def play_period(self) -> None:
        self.reset_period()

        for _ in range(self._config.seed.days_in_period):
            self.play_day()

        self._log(name="population", value=len(self._config.individuals))
        self.play_org()
        self._config.state.period += 1

    def reset_period(self) -> None:
        for k in self._config.individuals.keys():
            self._config.state.individuals[k].contribution = 0

    def play_day(self) -> None:
        for identity, ind in self._config.individuals.items():
            self.play_individual(identity, ind)

        self._config.state.date += 1

    def play_individual(self, identity: str, individual: base.Individual) -> None:
        seed = self._config.seed

        istate = state.IndividualState(self._config.state, identity)
        k = individual.compute_work_coefficient(istate)

        idata = self._config.state.individuals[identity]
        production = idata.base_production + (
            idata.accumulated_value * seed.production_to_value_coef
        )
        work = k * production
        self._config.state.org_wealth += work * self._config.seed.org_productivity
        idata.contribution += work

        max_investment = ((1 - k) ** 2) * seed.max_invest_coef * idata.wealth
        if max_investment > 1e-7:
            investment = min(max_investment, idata.wealth)
            idata.wealth -= investment
            idata.accumulated_value += investment

    def play_org(self) -> None:
        org = self._config.org
        ostate = state.OrgState(self._config.state)

        total_salaries = sum(v.salary for v in self._config.state.individuals.values())
        insufficiency_coef = min(self._config.state.org_wealth / total_salaries, 1.0)
        # print(total_salaries, self._config.state.org_wealth, insufficiency_coef)

        bonuses = org.compute_bonuses(ostate)

        for identity in list(self._config.individuals.keys()):
            self.pay_salary(identity, insufficiency_coef)
            self.pay_bonus(identity, bonuses[identity])
            self._deduct_cost_of_living(identity)

        self.pay_shareholder_value(org.compute_shareholder_value(ostate))

        new_salaries = org.re_evaluate_salaries(ostate)
        for identity in self._config.individuals.keys():
            self.update_salary(identity, new_salaries[identity])

    def pay_salary(self, identity: str, insufficiency_coef: float) -> None:
        state = self._config.state
        salary = insufficiency_coef * state.individuals[identity].salary
        state.individuals[identity].wealth += salary
        state.org_wealth -= salary

    def pay_bonus(self, identity: str, bonus: float) -> None:
        state = self._config.state
        state.individuals[identity].wealth += bonus
        state.org_wealth -= bonus

    def _deduct_cost_of_living(self, identity: str) -> None:
        state = self._config.state
        state.individuals[identity].wealth -= state.individuals[identity].cost_of_living
        if state.individuals[identity].wealth < 0:
            self.die(identity)

    def die(self, identity: str) -> None:
        del self._config.individuals[identity]
        del self._config.state.individuals[identity]

    def pay_shareholder_value(self, sv: float) -> None:
        state = self._config.state
        state.shareholder_value += sv
        state.org_wealth -= sv

    def update_salary(self, identity: str, salary: float) -> None:
        self._config.state.individuals[identity].salary = salary

    def _log(
        self, name: str, value: float, labels: typing.Optional[metrics.Labels] = None
    ) -> None:
        self._config.metrics.log(
            date=self._config.state.date,
            period=self._config.state.period,
            name=name,
            value=value,
            labels=labels,
        )

    @property
    def metrics(self) -> metrics.Metrics:
        return self._config.metrics


class Game:
    @classmethod
    def from_seed(cls, seed: seed.Seed, factory: seed.Factory) -> typing.Self:
        individuals = [factory.create_individual(s) for s in seed.initial_individuals]
        config = Config(
            seed=seed,
            state=state.State(
                date=0,
                period=0,
                individuals={k: v for (k, _, v) in individuals},
                org_wealth=seed.initial_org_wealth,
                shareholder_value=0,
            ),
            org=factory.create_org(seed.org_seed),
            individuals={k: v for (k, v, _) in individuals},
            metrics=metrics.Metrics(metrics.MetricsData(series_classes={})),
        )
        return cls(_Game(config))

    def __init__(self, game: _Game) -> None:
        self._game = game

    def play(self) -> None:
        return self._game.play()


__all__ = [
    "base",
    "individual",
    "metrics",
    "org",
    "seed",
    "state",
    "Config",
    "Game",
]
