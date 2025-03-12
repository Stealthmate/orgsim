import typing

import pandas as pd
import pydantic

from orgsim.framework import WorldState

Labels: typing.TypeAlias = dict[str, str]

TimeSeriesEntry: typing.TypeAlias = tuple[int, int, float]


class TimeSeriesClass(pydantic.BaseModel):
    label_mapping: dict[int, Labels]
    series: dict[int, list[TimeSeriesEntry]]


class MetricsData(pydantic.BaseModel):
    series_classes: dict[str, TimeSeriesClass]


def generate_labels_identity(labels: Labels) -> int:
    return hash(frozenset(labels))


class Metrics:
    def __init__(self, data: MetricsData) -> None:
        self._data = data

    def log(
        self,
        *,
        world_state: WorldState,
        name: str,
        value: float,
        labels: typing.Optional[Labels] = None,
    ) -> None:
        if name not in self._data.series_classes:
            self._data.series_classes[name] = TimeSeriesClass(
                label_mapping={}, series={}
            )
        sc = self._data.series_classes[name]

        the_labels = labels if labels else {}
        lid = generate_labels_identity(the_labels)
        if lid not in sc.label_mapping:
            sc.label_mapping[lid] = the_labels
        if lid not in sc.series:
            sc.series[lid] = []

        ts = sc.series[lid]
        ts.append((world_state.date, world_state.fiscal_period, value))

    def get_fiscal_series(
        self, name: str, labels: typing.Optional[Labels] = None
    ) -> "pd.Series[float]":
        if name not in self._data.series_classes:
            raise Exception(f"No such series class: {name}")
        sc = self._data.series_classes[name]

        the_labels = labels if labels is not None else {}
        lid = generate_labels_identity(the_labels)
        if lid not in sc.label_mapping or lid not in sc.series:
            raise Exception(f"Series {name} does not have label set: {the_labels}")

        series = sc.series[lid]
        return pd.Series([s[2] for s in series], index=[s[1] for s in series])

    @property
    def data(self) -> MetricsData:
        return self._data
