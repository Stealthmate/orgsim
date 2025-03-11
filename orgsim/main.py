import datetime
import json
import pathlib
import random

import matplotlib
import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot as plt
import pandas as pd

from orgsim import common, framework, models


class Plotter:
    def __init__(self, metrics: models.MetricsDump) -> None:
        self._metrics = metrics

    def get_fiscal_metric(self, name: str) -> "pd.Series[float]":
        for id_, series in self._metrics.fiscal.items():
            name_ = json.loads(id_)["__name"]
            if name_ == name:
                return pd.Series(series)
        raise Exception(f"Not found: {name}")

    def _build_individual_wealth(self, ax: matplotlib.axes.Axes) -> None:
        min_ = self.get_fiscal_metric("min_wealth")
        avg = self.get_fiscal_metric("avg_wealth")
        max_ = self.get_fiscal_metric("max_wealth")

        ax.plot(max_.index, max_, label="max")
        ax.plot(avg.index, avg, label="avg")
        ax.plot(min_.index, min_, label="min")
        ax.set_ylabel("Individual Wealth")
        ax.set_xlabel("Period")
        ax.legend()
        ax.set_ylim(0, 1000)

    def _build_selfishness(self, ax: matplotlib.axes.Axes) -> None:
        min_ = self.get_fiscal_metric("min_selfishness")
        avg = self.get_fiscal_metric("avg_selfishness")
        max_ = self.get_fiscal_metric("max_selfishness")

        ax.plot(max_.index, max_, label="max")
        ax.plot(avg.index, avg, label="avg")
        ax.plot(min_.index, min_, label="min")
        ax.set_ylabel("Selfishness")
        ax.set_xlabel("Period")
        ax.legend()
        ax.set_ylim(-0.1, 1.1)

    def build(self) -> matplotlib.figure.Figure:
        fig, axs = plt.subplots(3, 2, figsize=(18, 10))
        self._build_individual_wealth(axs[0][0])

        self._build_selfishness(axs[1][0])

        population = self.get_fiscal_metric("population")
        axs[0][1].plot(population.index, population)
        axs[0][1].set_ylim(0, 50)

        return fig


def record_run(seed: framework.WorldSeed, metrics: models.MetricsDump) -> None:
    ts = int(datetime.datetime.now().timestamp())
    root = pathlib.Path(".ignored", str(ts))
    root.mkdir(parents=True)

    with open(f"{root}/seed.json", mode="w") as f:
        f.write(seed.model_dump_json())

    with open(f"{root}/metrics.json", mode="w") as f:
        f.write(metrics.model_dump_json())

    fig = Plotter(metrics).build()
    fig.savefig(f"{root}/summary-fiscal.png")


def main() -> None:
    id_gen = common.SequentialIdentityGenerator()
    strategy = models.DefaultWorldStrategy(
        reward_distribution_strategy=models.EqualContribution(),
        identity_generator=id_gen,
    )
    world_seed = framework.WorldSeed(
        initial_people={
            framework.PersonSeed(
                identity=id_gen.generate(), selfishness=random.random()
            )
            for _ in range(10)
        },
        fiscal_length=3,
        productivity=2,
        initial_personal_gain=30,
        selfish_gain=6,
        selfless_gain=5,
        living_cost=10,
        periodic_recruit_count=1,
        max_age=100,
    )
    w = framework.create_world(
        seed=world_seed,
        strategy=strategy,
    )

    for i in range(int(1e3)):
        w.run_period()
        if i % 100 == 0:
            print("Period", i)
        if w.is_empty():
            break

    record_run(world_seed, strategy.metrics.dump())
    # plt.show()


if __name__ == "__main__":
    main()
