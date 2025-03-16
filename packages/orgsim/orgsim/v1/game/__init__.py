import typing

import pydantic

from . import base, individual, metrics, org, state, seed


class Config(pydantic.BaseModel, typing.Generic[seed.IndividualSeed, seed.OrgSeed]):
    seed: seed.Seed[seed.IndividualSeed, seed.OrgSeed]
    state: state.State
    org: base.Org
    individuals: dict[str, base.Individual]
    metrics: metrics.Metrics

    class Config:
        arbitrary_types_allowed = True


class Results(pydantic.BaseModel):
    shareholder_value: float
    total_individual_value: float
    min_individual_value: float
    med_individual_value: float
    max_individual_value: float


class _Game(typing.Generic[seed.IndividualSeed, seed.OrgSeed]):
    @classmethod
    def from_seed(
        cls,
        seed: seed.Seed[seed.IndividualSeed, seed.OrgSeed],
        factory: seed.Factory[seed.IndividualSeed, seed.OrgSeed],
    ) -> typing.Self:
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

    def __init__(self, config: Config[seed.IndividualSeed, seed.OrgSeed]) -> None:
        self._config = config
        self._individual_tally: list[float] = []
        self._results = Results(
            shareholder_value=0,
            total_individual_value=0,
            min_individual_value=0,
            med_individual_value=0,
            max_individual_value=0,
        )

    def play(self) -> Results:
        """Play the game for however many periods were provided in the seed."""

        for _ in range(self._config.seed.periods):
            self.play_period()

        self._results.shareholder_value = self._config.state.shareholder_value
        for k in self._config.individuals.keys():
            self._individual_tally.append(
                self._config.state.individuals[k].accumulated_value
            )
        self._results.total_individual_value = sum(self._individual_tally)
        self._results.min_individual_value = min(self._individual_tally)
        self._results.med_individual_value = sorted(self._individual_tally)[
            len(self._individual_tally) // 2
        ]
        self._results.max_individual_value = max(self._individual_tally)

        return self._results

    def play_period(self) -> None:
        """Play a single period.

        A period consists of a fixed number of days (as configured in the seed). All days are played
        in order. At the end of the period the Org plays its turn.
        """

        self.initialize_period_state()

        for _ in range(self._config.seed.days_in_period):
            self.play_day()

        population = len(self._config.individuals)
        self._log(name="population", value=population)

        if population > 0:
            self.play_org()

        self._config.state.period += 1

    def initialize_period_state(self) -> None:
        """Set the initial state before each period run.

        During every period, some information is recorded in order to be used by the Org at the end.
        This method is called at the beginning of every period in order to reset that information.
        """

        for k in self._config.individuals.keys():
            self._config.state.individuals[k].contribution = 0

    def play_day(self) -> None:
        """Play a single day.

        During the day, all Individuals execute their turns sequentially, albeit in no particular order.
        """

        for identity in self._config.individuals.keys():
            self.play_individual(identity)

        self._config.state.date += 1

    def play_individual(self, identity: str) -> None:
        """Play the turn for a specific individual.

        Each turn, the Individual must make a decision expressed by a real value `k` between 0 and 1,
        which can be loosely thought of as the proportion of time spent by the Individual on organizational work.
        The rest of the time is used for self-improvement.
        """

        individual = self._config.individuals[identity]
        istate = state.IndividualState(self._config.state, identity)

        k = individual.compute_work_coefficient(istate)

        self.individual_do_work(identity, k)
        self.individual_do_self_improvement(identity, 1 - k)

        idata = self._config.state.individuals[identity]
        labels = {"identity": identity}
        self._log("individual_wealth", idata.wealth, labels=labels)
        self._log("individual_contribution", idata.contribution, labels=labels)
        self._log(
            "individual_accumulated_value", idata.accumulated_value, labels=labels
        )

    def individual_do_work(self, identity: str, k: float) -> None:
        """Assume that the individual spent `k` of his time working and update the game state.

        Doing work results in two state changes:

        1. The total wealth of the Org is increased.
        2. The individual's contribution value for this period is increased.
        """

        seed = self._config.seed
        idata = self._config.state.individuals[identity]

        production = idata.base_production + (
            idata.accumulated_value * seed.production_to_value_coef
        )
        work = k * production
        self._config.state.org_wealth += work * self._config.seed.org_productivity
        idata.contribution += work

    def individual_do_self_improvement(self, identity: str, k: float) -> None:
        seed = self._config.seed
        idata = self._config.state.individuals[identity]

        max_investment = (k**2) * seed.max_invest_coef * idata.wealth
        investment = min(max_investment, idata.wealth)
        idata.wealth -= investment
        idata.accumulated_value += investment

    def play_org(self) -> None:
        org = self._config.org
        ostate = state.OrgState(self._config.state)

        total_salaries = sum(v.salary for v in self._config.state.individuals.values())
        insufficiency_coef = min(self._config.state.org_wealth / total_salaries, 1.0)

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
        idata = state.individuals[identity]
        idata.wealth -= idata.cost_of_living
        if state.individuals[identity].wealth < 0:
            self.die(identity)

    def die(self, identity: str) -> None:
        self._individual_tally.append(
            self._config.state.individuals[identity].accumulated_value
        )
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


class Game(typing.Generic[seed.IndividualSeed, seed.OrgSeed]):
    @classmethod
    def from_seed(
        cls,
        seed: seed.Seed[seed.IndividualSeed, seed.OrgSeed],
        factory: seed.Factory[seed.IndividualSeed, seed.OrgSeed],
    ) -> typing.Self:
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

    def __init__(self, game: _Game[seed.IndividualSeed, seed.OrgSeed]) -> None:
        self._game = game

    def play(self) -> Results:
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
