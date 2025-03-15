import abc
import typing

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pandas as pd

from . import base


class MetricsStore(abc.ABC):
    @abc.abstractmethod
    def get_fiscal_series(
        self, name: str, labels: typing.Optional[base.Labels] = None
    ) -> "pd.Series[float]":
        raise NotImplementedError()


def plot_world_summary(*, metrics: MetricsStore, filepath: str) -> Figure:
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    population = metrics.get_fiscal_series(base.Metrics.POPULATION)
    ax.plot(population.index, population, label="Population")
    ax.set_xlabel("Period")
    ax.set_ylabel("Individuals")
    ax.set_ylim(0, population.max() * 1.2)
    ax.legend(loc="upper left")

    ax2 = ax.twinx()
    ax2._get_lines = ax._get_lines  # type: ignore
    recruited = metrics.get_fiscal_series(base.Metrics.RECRUITED)
    suicides = metrics.get_fiscal_series(base.Metrics.SUICIDES)
    killed = metrics.get_fiscal_series(base.Metrics.KILLED)
    ax2.plot(recruited.index, recruited, label="Recruited", linestyle="dashed")
    ax2.plot(suicides.index, suicides, label="Suicides", linestyle="dashed")
    ax2.plot(killed.index, killed, label="Killed", linestyle="dashed")
    ax2.set_ylim(0, max(recruited.max(), suicides.max(), killed.max()) * 1.2)
    ax2.legend(loc="upper right")

    fig.savefig(filepath)

    return fig
