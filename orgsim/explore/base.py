import abc
import typing

import pandas as pd

from orgsim import world


class MetricsStore(abc.ABC):
    @abc.abstractmethod
    def get_fiscal_series(
        self, name: str, labels: typing.Optional[world.Labels] = None
    ) -> "pd.Series[float]":
        raise NotImplementedError()
