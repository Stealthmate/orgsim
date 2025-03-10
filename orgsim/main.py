import random

import matplotlib.pyplot as plt
import seaborn as sns

from orgsim import common, framework, models


def main() -> None:
    id_gen = common.SequentialIdentityGenerator()
    strategy = models.DefaultWorldStrategy(
        reward_distribution_strategy=models.EqualContribution(),
        identity_generator=id_gen,
    )
    w = framework.create_world(
        seed=framework.WorldSeed(
            initial_people={
                framework.PersonSeed(
                    identity=id_gen.generate(), selfishness=random.random()
                )
                for _ in range(10)
            },
            fiscal_length=3,
            productivity=3,
            initial_personal_gain=20,
            selfish_gain=6,
            selfless_gain=5,
            living_cost=10,
            periodic_recruit_count=1,
            max_age=100,
        ),
        strategy=strategy,
    )

    for i in range(int(1e3)):
        w.run_period()
        if i % 100 == 0:
            print("Period", i)
        if w.is_empty():
            break

    df = strategy.metrics.period_metrics()
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

    # sns.lineplot(df, x="period", y="total_reward", ax=axs[2][0])
    # sns.lineplot(df, x="period", y="recruit_average_selfishness", ax=axs[2][1])
    axs[2][1].set_ylim(-0.1, 1.1)

    fig.savefig("output.png")
    plt.show()


if __name__ == "__main__":
    main()
