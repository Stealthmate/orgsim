# seed = v1.game.seed.Seed(
#     periods=240,
#     days_in_period=30,
#     initial_individuals=[
#         v1.game.seed.IndividualSeed(initial_wealth=100_000) for _ in range(10)
#     ],
#     initial_org_wealth=1_000_000,
#     org_seed=v1.game.seed.OrgSeed(),
#     org_productivity=0.8,
#     max_invest_coef=0.2,
#     production_to_value_coef=0.001,
# )


# class Factory(v1.game.seed.Factory):
#     def __init__(self) -> None:
#         self._identity_counter: int = 0

#     def create_org(self, seed: v1.game.seed.OrgSeed) -> v1.game.base.Org:
#         return v1.game.org.SimpleOrg()

#     def create_individual(
#         self, seed: v1.game.seed.IndividualSeed
#     ) -> tuple[str, v1.game.base.Individual, v1.game.state.IndividualData]:
#         self._identity_counter += 1
#         identity = str(self._identity_counter)
#         return (
#             identity,
#             v1.game.individual.SimpleIndividual(),
#             v1.game.state.IndividualData(
#                 accumulated_value=0,
#                 base_production=10_000,
#                 salary=300_000,
#                 cost_of_living=300_000,
#                 contribution=0,
#                 wealth=seed.initial_wealth,
#             ),
#         )


# factory = Factory()
# game = v1.game.Game.from_seed(seed, factory)

# game.play()
