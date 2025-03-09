import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import pydantic

from orgsim import common


class Tally(pydantic.BaseModel):
    day: int
    population: int
    average_wealth: float
    median_wealth: float
    average_selfishness: float
    median_selfishness: float
    org_gain: float


def main():
    world = common.World(
        world_params=common.WorldParams(
            initial_people={common.Person() for _ in range(10)},
            profit_period=3,
            profit_coef=3,
            initial_personal_gain=20,
            selfish_gain=6,
            selfless_gain=5,
            daily_loss=10,
            periodic_recruit_count=1,
            max_age=100,
        )
    )

    tally: list[Tally] = []

    for i in range(int(1e4)):
        world.run()
        if i % 100 == 0:
            print("Day", i)
        if len(world.people_state) == 0:
            break
        tally.append(
            Tally(
                day=i,
                population=len(world.people_state),
                average_wealth=np.average(
                    [s.gain for s in world.people_state.values()]
                ),
                median_wealth=np.median([s.gain for s in world.people_state.values()]),
                average_selfishness=np.average(
                    [s.person.selfishness for s in world.people_state.values()]
                ),
                median_selfishness=np.median(
                    [s.person.selfishness for s in world.people_state.values()]
                ),
                org_gain=world._org_gain,
            )
        )

    df = pd.DataFrame([t.model_dump() for t in tally])
    print(df.head())

    fig, axs = plt.subplots(3, 2, figsize=(20, 10))
    sns.lineplot(df, x="day", y="average_wealth", ax=axs[0][0])
    sns.lineplot(df, x="day", y="median_wealth", ax=axs[0][0])

    sns.scatterplot(df, x="average_selfishness", y="average_wealth", ax=axs[0][1])
    axs[0][1].set_xlim(-0.1, 1.1)

    sns.lineplot(df, x="day", y="average_selfishness", ax=axs[1][0])
    sns.lineplot(df, x="day", y="median_selfishness", ax=axs[1][0])
    axs[1][0].set_ylim(-0.1, 1.1)

    sns.lineplot(df, x="day", y="population", ax=axs[1][1])

    sns.lineplot(df, x="day", y="org_gain", ax=axs[2][0])

    fig.savefig("output.png")
    plt.show()


if __name__ == "__main__":
    main()
