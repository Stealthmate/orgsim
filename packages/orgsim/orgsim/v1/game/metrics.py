import abc
import typing

import pandas as pd
import pydantic

Labels: typing.TypeAlias = dict[str, str]

TimeSeriesEntry: typing.TypeAlias = tuple[int, int, float]


class TimeSeriesClass(pydantic.BaseModel):
    label_mapping: dict[int, Labels]
    series: dict[int, list[TimeSeriesEntry]]


class MetricsData(pydantic.BaseModel):
    series_classes: dict[str, TimeSeriesClass]


def generate_labels_identity(labels: Labels) -> int:
    return hash(frozenset(list(labels.items())))


class Metrics:
    def __init__(self, data: MetricsData) -> None:
        self._data = data

    def log(
        self,
        *,
        date: int,
        period: int,
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
        ts.append((date, period, value))

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

    def get_series_in_class(
        self, name: str, filter_labels: typing.Optional[Labels] = None
    ) -> typing.Iterable[tuple[pd.DataFrame, Labels]]:
        if name not in self._data.series_classes:
            raise Exception(f"No such series class: {name}")
        sc = self._data.series_classes[name]

        the_filter_labels = filter_labels if filter_labels else {}
        for lid, labels in sc.label_mapping.items():
            if not all(
                (fk in labels) and (labels[fk] == fv)
                for fk, fv in the_filter_labels.items()
            ):
                continue
            yield (
                pd.DataFrame(sc.series[lid], columns=["date", "period", "value"]),
                labels,
            )

    @property
    def data(self) -> MetricsData:
        return self._data


class MetricsState(abc.ABC):
    @property
    @abc.abstractmethod
    def date(self) -> int:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def period(self) -> int:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def population(self) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    def wealth_of(self, identity: str) -> float:
        raise NotImplementedError()

    @abc.abstractmethod
    def contribution_of(self, identity: str) -> float:
        raise NotImplementedError()

    @abc.abstractmethod
    def score_of(self, identity: str) -> float:
        raise NotImplementedError()


class MetricsLogger:
    def __init__(self, state: MetricsState, metrics: Metrics) -> None:
        self._state = state
        self._metrics = metrics

    def log_end_of_period(self) -> None:
        self._log(name="population", value=self._state.population)

    def log_individual(self, identity: str) -> None:
        labels = {"identity": identity}
        self._log("individual_wealth", self._state.wealth_of(identity), labels=labels)
        self._log(
            "individual_contribution",
            self._state.contribution_of(identity),
            labels=labels,
        )
        self._log("individual_score", self._state.score_of(identity), labels=labels)

    def _log(
        self, name: str, value: float, labels: typing.Optional[Labels] = None
    ) -> None:
        self._metrics.log(
            date=self._state.date,
            period=self._state.period,
            name=name,
            value=value,
            labels=labels,
        )
