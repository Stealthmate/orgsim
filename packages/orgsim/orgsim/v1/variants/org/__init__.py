from orgsim.v1.game import base, state


class Shithole(base.Org):
    def compute_bonuses(self, state: state.OrgState) -> dict[str, float]:
        return {k: 0 for k in state.individuals}

    def compute_shareholder_value(self, state: state.OrgState) -> float:
        return state.wealth

    def re_evaluate_salaries(self, state: state.OrgState) -> dict[str, float]:
        return {k: state.get_salary_for(k) for k in state.individuals}
