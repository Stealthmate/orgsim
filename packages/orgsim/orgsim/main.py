import numpy as np

from orgsim.world import v1

metrics = v1.models.v1.Metrics()

seed = v1.models.v1.Seed(
    base=v1.base.BaseWorldSeed(fiscal_length=365),
    org=v1.models.v1.OrgSeed(recruit_count_per_period=1),
    nature=v1.models.v1.NatureSeed(
        initial_candidates=[
            v1.models.v1.CandidatePrivateData(selfishness=x)
            for x in np.random.uniform(0, 1, size=10)
        ]
    ),
    common=v1.models.v1.CommonSeed(
        daily_salary=300_000 / 365,
        daily_living_cost=400_000 / 365,
        productivity=2,
        max_age=100,
        initial_individual_reward=400_000,
    ),
)

model = v1.models.v1.create_model(seed=seed, metrics=metrics)
model.init()
model.run(20)

v1.explore.plot_world_summary(metrics=metrics, filepath="example.png")
