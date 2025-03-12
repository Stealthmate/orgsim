import matplotlib
import matplotlib.axes
import matplotlib.figure
import pandas as pd

from orgsim.models.metrics import Metrics


def plot_individual_wealth(metrics: Metrics, ax: matplotlib.axes.Axes) -> None:
    min_ = metrics.get_fiscal_series("min_wealth")
    avg = metrics.get_fiscal_series("avg_wealth")
    max_ = metrics.get_fiscal_series("max_wealth")

    ax.plot(max_.index, max_, label="max")
    ax.plot(avg.index, avg, label="avg")
    ax.plot(min_.index, min_, label="min")
    ax.set_ylabel("Individual Wealth")
    ax.set_xlabel("Period")
    ax.legend()
    ax.set_yscale("log")
    ax.set_ylim(1e0, 1e8)


def plot_selfishness(metrics: Metrics, ax: matplotlib.axes.Axes) -> None:
    min_ = metrics.get_fiscal_series("min_selfishness")
    avg = metrics.get_fiscal_series("avg_selfishness")
    max_ = metrics.get_fiscal_series("max_selfishness")

    ax.plot(max_.index, max_, label="max")
    ax.plot(avg.index, avg, label="avg")
    ax.plot(min_.index, min_, label="min")
    ax.set_ylabel("Selfishness")
    ax.set_xlabel("Period")
    ax.legend()
    ax.set_ylim(-0.1, 1.1)


def plot_age(metrics: Metrics, ax: matplotlib.axes.Axes) -> None:
    min_ = metrics.get_fiscal_series("min_age") / 365
    avg = metrics.get_fiscal_series("avg_age") / 365
    max_ = metrics.get_fiscal_series("max_age") / 365

    ax.plot(max_.index, max_, label="max")
    ax.plot(avg.index, avg, label="avg")
    ax.plot(min_.index, min_, label="min")
    ax.set_ylabel("Age")
    ax.set_xlabel("Period")
    ax.legend()
    ax.set_ylim(0, 21)


def plot_age_distribution(metrics: Metrics, ax: matplotlib.axes.Axes) -> None:
    series = list(metrics.get_series_in_class("person_age"))
    for v, labels_ in series:
        v["identity"] = int(labels_["identity"])
    df = pd.concat([s[0] for s in series]).groupby("identity")["value"].max() / 365
    ax.hist(df, bins=list(range(0, 21, 2)))
    ax.set_xlim(0, 20)


def plot_contribution(metrics: Metrics, ax: matplotlib.axes.Axes) -> None:
    min_ = metrics.get_fiscal_series("min_contribution")
    avg = metrics.get_fiscal_series("avg_contribution")
    max_ = metrics.get_fiscal_series("max_contribution")

    ax.plot(max_.index, max_, label="max")
    ax.plot(avg.index, avg, label="avg")
    ax.plot(min_.index, min_, label="min")
    ax.set_ylabel("Contribution")
    ax.set_xlabel("Period")
    ax.legend()
    ax.set_ylim(0, 400)


def plot_population(metrics: Metrics, ax: matplotlib.axes.Axes) -> None:
    population = metrics.get_fiscal_series("population")
    ax.plot(population.index, population)
    ax.set_ylim(0, 50)
    ax.set_xlabel("Period")
    ax.set_ylabel("Population")
