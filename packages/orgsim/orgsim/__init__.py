import pathlib
import typing

import pydantic

from . import common, framework, metrics, models

T = typing.TypeVar("T", bound=pydantic.BaseModel)


def run_world(
    *,
    seed: framework.WorldSeed[T],
    strategy: framework.WorldStrategy[T],
    periods: int = 200,
) -> None:
    w = framework.create_world(
        seed=seed,
        strategy=strategy,
    )

    for i in range(periods):
        w.run_period()
        if i % 10 == 0:
            print("Period", i)
        if w.is_empty():
            break


def do_experiment(
    *,
    title: str,
    seed: framework.WorldSeed[models.person.PersonSeed],
    strategy: models.DefaultWorldStrategy,
    periods: int = 200,
) -> metrics.Metrics:
    run_world(seed=seed, strategy=strategy, periods=periods)
    root = pathlib.Path(".", title)
    root.mkdir(parents=True, exist_ok=True)

    with open(f"{root}/seed.json", mode="w") as f:
        f.write(seed.model_dump_json())

    with open(f"{root}/metrics.json", mode="w") as f:
        f.write(strategy.metrics.data.model_dump_json())

    return strategy.metrics


__all__ = ["common", "framework", "models", "run_world"]
