import pathlib

from . import common, explore, framework, models


def run_world(
    *, seed: framework.WorldSeed, strategy: framework.WorldStrategy, periods: int = 200
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
    seed: framework.WorldSeed,
    strategy: models.DefaultWorldStrategy,
    periods: int = 200,
) -> models.metrics.Metrics:
    run_world(seed=seed, strategy=strategy, periods=periods)
    root = pathlib.Path(".", title)
    root.mkdir(parents=True, exist_ok=True)

    with open(f"{root}/seed.json", mode="w") as f:
        f.write(seed.model_dump_json())

    with open(f"{root}/metrics.json", mode="w") as f:
        f.write(strategy.metrics.data.model_dump_json())

    return strategy.metrics


__all__ = ["common", "explore", "framework", "models", "run_world"]
