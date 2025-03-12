import datetime
import pathlib
import random

import matplotlib
import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot as plt
import pandas as pd

from orgsim import common, framework, models


class Plotter:
    def __init__(self, metrics: models.metrics.Metrics) -> None:
        self._metrics = metrics

    def _build_individual_wealth(self, ax: matplotlib.axes.Axes) -> None:
        min_ = self._metrics.get_fiscal_series("min_wealth")
        avg = self._metrics.get_fiscal_series("avg_wealth")
        max_ = self._metrics.get_fiscal_series("max_wealth")

        ax.plot(max_.index, max_, label="max")
        ax.plot(avg.index, avg, label="avg")
        ax.plot(min_.index, min_, label="min")
        ax.set_ylabel("Individual Wealth")
        ax.set_xlabel("Period")
        ax.legend()
        ax.set_ylim(0, max_.max() * 1.1)

    def _build_selfishness(self, ax: matplotlib.axes.Axes) -> None:
        min_ = self._metrics.get_fiscal_series("min_selfishness")
        avg = self._metrics.get_fiscal_series("avg_selfishness")
        max_ = self._metrics.get_fiscal_series("max_selfishness")

        ax.plot(max_.index, max_, label="max")
        ax.plot(avg.index, avg, label="avg")
        ax.plot(min_.index, min_, label="min")
        ax.set_ylabel("Selfishness")
        ax.set_xlabel("Period")
        ax.legend()
        ax.set_ylim(-0.1, 1.1)

    def _build_age(self, ax: matplotlib.axes.Axes) -> None:
        min_ = self._metrics.get_fiscal_series("min_age") / 365
        avg = self._metrics.get_fiscal_series("avg_age") / 365
        max_ = self._metrics.get_fiscal_series("max_age") / 365

        ax.plot(max_.index, max_, label="max")
        ax.plot(avg.index, avg, label="avg")
        ax.plot(min_.index, min_, label="min")
        ax.set_ylabel("Age")
        ax.set_xlabel("Period")
        ax.legend()
        ax.set_ylim(0, 21)

    def _build_age_distribution(self, ax: matplotlib.axes.Axes) -> None:
        series = list(self._metrics.get_series_in_class("person_age"))
        for v, labels_ in series:
            v["identity"] = int(labels_["identity"])
        df = pd.concat([s[0] for s in series]).groupby("identity")["value"].max() / 365
        ax.hist(df)

    def build(self) -> matplotlib.figure.Figure:
        fig, axs = plt.subplots(3, 2, figsize=(18, 10))
        self._build_individual_wealth(axs[0][0])

        self._build_selfishness(axs[1][0])
        self._build_age(axs[1][1])

        population = self._metrics.get_fiscal_series("population")
        axs[0][1].plot(population.index, population)
        axs[0][1].set_ylim(0, 50)

        bonus = self._metrics.get_fiscal_series("avg_bonus")
        axs[2][0].plot(bonus.index, bonus)
        axs[2][0].set_ylim(0, max(bonus) * 1.1)

        self._build_age_distribution(axs[2][1])

        return fig


def record_run(seed: framework.WorldSeed, metrics: models.metrics.Metrics) -> None:
    ts = int(datetime.datetime.now().timestamp())
    root = pathlib.Path(".ignored", str(ts))
    root.mkdir(parents=True)

    with open(f"{root}/seed.json", mode="w") as f:
        f.write(seed.model_dump_json())

    with open(f"{root}/metrics.json", mode="w") as f:
        f.write(metrics.data.model_dump_json())

    fig = Plotter(metrics).build()
    fig.savefig(f"{root}/summary-fiscal.png")


def main() -> None:
    id_gen = common.SequentialIdentityGenerator()
    strategy = models.DefaultWorldStrategy(
        reward_distribution_strategy=models.EqualContribution(),
        identity_generator=id_gen,
    )

    fiscal_length = 365

    world_seed = framework.WorldSeed(
        initial_people={
            framework.PersonSeed(
                identity=id_gen.generate(), selfishness=random.random()
            )
            for _ in range(10)
        },
        fiscal_length=fiscal_length,
        productivity=2,
        initial_individual_wealth=600_000,
        daily_salary=300_000 / 365,
        daily_living_cost=600_000 / 365,
        periodic_recruit_count=1,
        max_age=fiscal_length * 20,
    )
    w = framework.create_world(
        seed=world_seed,
        strategy=strategy,
    )

    for i in range(int(2e2)):
        w.run_period()
        if i % 10 == 0:
            print("Period", i)
        if w.is_empty():
            break

    record_run(world_seed, strategy.metrics)
    # plt.show()


if __name__ == "__main__":
    main()
