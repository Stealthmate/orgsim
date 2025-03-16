import enum
import random

import pydantic
import pandas as pd

from orgsim import v1

random.seed(0)

N_PERIODS = 200
N_DAYS_IN_PERIOD = 30
INITIAL_ORG_WEALTH = 1_000_000
ORG_PRODUCTIVITY = 1.0
PRODUCTION_TO_VALUE_COEF = 0.1
MAX_INVEST_COEF = 1.0


class IndividualType(enum.Enum):
    SLAVE = 0


class IndividualSeed(pydantic.BaseModel):
    type_: IndividualType


class OrgType(enum.Enum):
    SHITHOLE = 0


class OrgSeed(pydantic.BaseModel):
    type_: OrgType


class Factory(v1.game.seed.Factory[IndividualSeed, OrgSeed]):
    def __init__(self) -> None:
        self._identity_counter = 0

    def create_individual(
        self, seed: IndividualSeed
    ) -> tuple[str, v1.game.base.Individual, v1.game.state.IndividualData]:
        self._identity_counter += 1
        return (
            str(self._identity_counter),
            v1.variants.individual.Slave(),
            v1.game.state.IndividualData(
                accumulated_value=0,
                wealth=1_000_000,
                base_production=10_000,
                salary=300_000,
                cost_of_living=300_000,
                contribution=0,
            ),
        )

    def create_org(self, seed: OrgSeed) -> v1.game.base.Org:
        return v1.variants.org.Shithole()


def generate_seed(org_type: OrgType) -> v1.game.seed.Seed:
    return v1.game.seed.Seed(
        periods=N_PERIODS,
        days_in_period=N_DAYS_IN_PERIOD,
        initial_individuals=[
            IndividualSeed(type_=IndividualType.SLAVE) for _ in range(10)
        ],
        initial_org_wealth=INITIAL_ORG_WEALTH,
        org_productivity=ORG_PRODUCTIVITY,
        org_seed=OrgSeed(type_=org_type),
        production_to_value_coef=PRODUCTION_TO_VALUE_COEF,
        max_invest_coef=MAX_INVEST_COEF,
    )


seed = generate_seed(OrgType.SHITHOLE)
game = v1.game.Game.from_seed(seed, Factory())
score = game.play()
for k, v in score.model_dump().items():
    print(k.rjust(30), f"{v: 10.0f}")

metrics = game._game.metrics
pop = metrics.get_fiscal_series("population")

wealth_series = list(metrics.get_series_in_class("individual_wealth"))
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
# print(df.head())
# sns.lineplot(df, x='period', y='value', hue='identity')
# plt.show()
