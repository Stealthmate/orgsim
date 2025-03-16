import typing

import pydantic

from . import state, seed


class Results(pydantic.BaseModel):
    shareholder_value: float
    total_individual_value: float
    min_individual_value: float
    med_individual_value: float
    max_individual_value: float


class _Game(typing.Generic[seed.IndividualSeed]):
    def __init__(self, state: state.GameState[seed.IndividualSeed]) -> None:
        self._state = state
        self._metrics = state.metrics

    def play(self) -> Results:
        """Play the game for however many periods were provided in the seed."""

        for _ in range(self._state.periods):
            self.play_period()

        return self.calculate_results()

    def play_period(self) -> None:
        """Play a single period.

        A period consists of a fixed number of days (as configured in the seed). All days are played
        in order. At the end of the period the Org plays its turn.
        """

        for _ in range(self._state.days_in_period):
            self.play_day()

        dead_individuals = self._state.org.play()
        for i in dead_individuals:
            self._state.delete_individual(i)
        self._metrics.log_end_of_period()
        self._state.advance_period()

    def play_day(self) -> None:
        """Play a single day.

        During the day, all Individuals execute their turns sequentially, albeit in no particular order.
        """

        for identity in self._state.individuals:
            self._state.obj_of(identity).play()

        self._state.advance_date()

    def calculate_results(self) -> Results:
        individual_values = list(
            self._state.score_of(i) for i in self._state.individuals
        )
        results = Results(
            shareholder_value=self._state.shareholder_value,
            total_individual_value=sum(individual_values),
            min_individual_value=min(individual_values) if individual_values else 0,
            med_individual_value=sorted(individual_values)[len(individual_values) // 2]
            if individual_values
            else 0,
            max_individual_value=max(individual_values) if individual_values else 0,
        )
        return results


class Game(typing.Generic[seed.IndividualSeed]):
    @classmethod
    def from_seed(
        cls,
        seed: seed.Seed[seed.IndividualSeed],
        factory: seed.Factory[seed.IndividualSeed],
    ) -> typing.Self:
        return cls(_Game(state.GameState.from_seed(seed, factory)))

    def __init__(self, game: _Game[seed.IndividualSeed]) -> None:
        self._game = game

    def play(self) -> Results:
        return self._game.play()
