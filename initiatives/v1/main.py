import random

import pydantic
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from orgsim.v1.game import Game, Factory, IndividualStats, IndividualStrategy, Seed
from orgsim.v1.variants import individual

random.seed(0)

N_PERIODS = 200
N_DAYS_IN_PERIOD = 30
INITIAL_ORG_WEALTH = 1_000_000
ORG_PRODUCTIVITY = 2.0
PRODUCTION_TO_VALUE_COEF = 0.1
MAX_INVEST_COEF = 1.0


class IndividualSeed(pydantic.BaseModel):
    pass


class FactoryImpl(Factory[IndividualSeed]):
    def __init__(self) -> None:
        self._identity_counter = 0

    def create_individual(
        self, seed: IndividualSeed
    ) -> tuple[str, IndividualStats, IndividualStrategy]:
        self._identity_counter += 1
        return (
            str(self._identity_counter),
            IndividualStats(
                score=0,
                wealth=0,
                unit_production=10_000,
                salary=300_000,
                cost_of_living=200_000,
            ),
            individual.Slave(),
        )


def generate_seed() -> Seed:
    return Seed(
        periods=N_PERIODS,
        days_in_period=N_DAYS_IN_PERIOD,
        initial_individuals=[IndividualSeed() for _ in range(10)],
        initial_org_wealth=INITIAL_ORG_WEALTH,
        org_productivity=ORG_PRODUCTIVITY,
        production_to_value_coef=PRODUCTION_TO_VALUE_COEF,
        max_invest_coef=MAX_INVEST_COEF,
    )


seed = generate_seed()
game = Game.from_seed(seed, FactoryImpl())
score = game.play()
for k, v in score.model_dump().items():
    print(k.rjust(30), f"{v: 10.0f}")

metrics = game._game._state.metrics._metrics
pop = metrics.get_fiscal_series("population")

wealth_series = list(metrics.get_series_in_class("individual_unit_production"))
df = pd.concat(
    [x[0] for x in wealth_series], keys=[x[1]["identity"] for x in wealth_series]
)
df = (
    df.reset_index(level=0)
    .rename(columns={"level_0": "identity"})
    .groupby(["period", "identity"])["value"]
    .max()
    .reset_index()
)
print(df.head())
sns.lineplot(df, x="period", y="value", hue="identity")
plt.show()
