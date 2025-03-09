import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import pydantic

from orgsim import common, world, reward_distribution


class Tally(pydantic.BaseModel):
    day: int
    population: int
    average_wealth: float
    median_wealth: float
    average_selfishness: float
    median_selfishness: float
    org_gain: float


def main():
    w = world.World(
        world_params=world.WorldParams(
            initial_people={common.Person() for _ in range(10)},
            profit_period=3,
            profit_coef=3,
            initial_personal_gain=20,
            selfish_gain=6,
            selfless_gain=5,
            daily_loss=10,
            periodic_recruit_count=1,
            max_age=100,
            # reward_distribution_strategy=reward_distribution.AllEqual(),
            reward_distribution_strategy=reward_distribution.EqualContribution(),
        )
    )

    for i in range(int(1e3)):
        w.run_period()
        if i % 100 == 0:
            print("Period", i)
        if len(w.people_state) == 0:
            break

    df = pd.DataFrame.from_dict(w.period_metrics, orient="index")
    print(df.head())

    fig, axs = plt.subplots(3, 2, figsize=(20, 10))
    sns.lineplot(df, x="period", y="average_wealth", ax=axs[0][0])
    # sns.lineplot(df, x="period", y="median_wealth", ax=axs[0][0])

    sns.scatterplot(df, x="average_selfishness", y="average_wealth", ax=axs[0][1])
    axs[0][1].set_xlim(-0.1, 1.1)

    sns.lineplot(df, x="period", y="average_selfishness", ax=axs[1][0])
    # sns.lineplot(df, x="period", y="median_selfishness", ax=axs[1][0])
    axs[1][0].set_ylim(-0.1, 1.1)

    sns.lineplot(df, x="period", y="population", ax=axs[1][1])

    sns.lineplot(df, x="period", y="total_reward", ax=axs[2][0])
    sns.lineplot(df, x="period", y="recruit_average_selfishness", ax=axs[2][1])
    axs[2][1].set_ylim(-0.1, 1.1)

    fig.savefig("output.png")
    plt.show()


if __name__ == "__main__":
    main()
