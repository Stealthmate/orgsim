from orgsim.v1.game import base, state


class Slave(base.Individual):
    def get_public_data(self) -> state.PublicIndividualData:
        return state.PublicIndividualData()

    def compute_work_coefficient(self, state: state.IndividualState) -> float:
        return 1.0
