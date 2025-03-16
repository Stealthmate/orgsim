# from orgsim.v1.game import base, state


# class Shithole(base.Org):
#     def compute_bonuses(self, state: state.OrgState) -> dict[str, float]:
#         return {k: 0 for k in state.individuals}

#     def compute_shareholder_value(self, state: state.OrgState) -> float:
#         return state.wealth

#     def re_evaluate_salaries(self, state: state.OrgState) -> dict[str, float]:
#         return {k: state.get_salary_for(k) for k in state.individuals}


# class V1(base.Org):
#     def compute_bonuses(self, state: state.OrgState) -> dict[str, float]:
#         bonuses = {}

#         bonus_funds = state.wealth * 0.5
#         skill_bonus_funds = bonus_funds * 0.5
#         contribution_bonus_funds = bonus_funds * 0.5

#         skill_bonuses = self.compute_skill_bonuses(state, skill_bonus_funds)
#         contribution_bonuses = self.compute_contribution_bonuses(
#             state, contribution_bonus_funds
#         )

#         for identity in state.individuals:
#             bonuses[identity] = skill_bonuses[identity] + contribution_bonuses[identity]
#         return bonuses

#     def compute_contribution_bonuses(
#         self, state: state.OrgState, funds: float
#     ) -> dict[str, float]:
#         contributions = {i: state.get_contribution_for(i) for i in state.individuals}
#         total_contribution = sum(contributions.values())
#         unit = funds / total_contribution
#         bonuses = {}
#         for i, c in contributions.items():
#             bonuses[i] = unit * c
#         return bonuses

#     def compute_skill_bonuses(
#         self, state: state.OrgState, funds: float
#     ) -> dict[str, float]:
#         skill_gains = {
#             i: (
#                 state.get_starting_unit_production_for(i),
#                 state.get_unit_production_for(i),
#             )
#             for i in state.individuals
#         }
#         total_skill_gains = sum(x[1] - x[0] for x in skill_gains.values())
#         unit = funds / total_skill_gains

#         bonuses = {}
#         for i, (start_u, end_u) in skill_gains.items():
#             bonuses[i] = unit * (end_u - start_u)
#         return bonuses

#     def compute_shareholder_value(self, state: state.OrgState) -> float:
#         return state.wealth

#     def re_evaluate_salaries(self, state: state.OrgState) -> dict[str, float]:
#         return {k: state.get_salary_for(k) for k in state.individuals}
