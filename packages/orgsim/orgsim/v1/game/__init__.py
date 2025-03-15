import typing

import pydantic

from . import base, individual, org, state, seed


class GameConfig(pydantic.BaseModel):
    seed: seed.GameSeed
    state: state.GameState
    org: base.Org
    individuals: dict[str, base.Individual]

    class Config:
        arbitrary_types_allowed = True


class Game:
    @classmethod
    def from_seed(cls, seed: seed.GameSeed, factory: seed.Factory) -> typing.Self:
        individuals = [factory.create_individual(s) for s in seed.initial_individuals]
        config = GameConfig(
            seed=seed,
            state=state.GameState(
                period=0,
                individuals={k: v for (k, _, v) in individuals},
                org_wealth=seed.initial_org_wealth,
                shareholder_value=0,
            ),
            org=factory.create_org(seed.org_seed),
            individuals={k: v for (k, v, _) in individuals},
        )
        return cls(config)

    def __init__(self, config: GameConfig) -> None:
        self._config = config

    def play(self) -> None:
        for _ in range(self._config.seed.periods):
            self._play_period()

    def _play_period(self) -> None:
        for _ in range(self._config.seed.days_in_period):
            self._play_day()

        self._play_org()
        self._config.state.period += 1

    def _play_day(self) -> None:
        for identity, ind in self._config.individuals.items():
            self._play_individual(identity, ind)

    def _play_individual(self, identity: str, individual: base.Individual) -> None:
        istate = state.IndividualState(self._config.state, identity)
        k = individual.compute_work_coefficient(istate)

        idata = self._config.state.individuals[identity]
        c = k * idata.qol * idata.base_production
        self._config.state.org_wealth += c * self._config.seed.org_productivity
        idata.contribution += c

    def _play_org(self) -> None:
        org = self._config.org
        ostate = state.OrgState(self._config.state)

        bonuses = org.compute_bonuses(ostate)

        for identity in self._config.individuals.keys():
            self._pay_salary(identity)
            self._pay_bonus(identity, bonuses[identity])

        self._pay_shareholder_value(org.compute_shareholder_value(ostate))

        new_salaries = org.re_evaluate_salaries(ostate)
        for identity in self._config.individuals.keys():
            self._update_salary(identity, new_salaries[identity])

    def _pay_salary(self, identity: str) -> None:
        state = self._config.state
        salary = state.individuals[identity].salary
        state.individuals[identity].wealth += salary
        state.org_wealth -= salary

    def _pay_bonus(self, identity: str, bonus: float) -> None:
        state = self._config.state
        state.individuals[identity].wealth += bonus
        state.org_wealth -= bonus

    def _pay_shareholder_value(self, sv: float) -> None:
        state = self._config.state
        state.shareholder_value += sv
        state.org_wealth -= sv

    def _update_salary(self, identity: str, salary: float) -> None:
        self._config.state.individuals[identity].salary = salary


__all__ = ["base", "individual", "org", "seed", "state", "GameConfig", "Game"]
