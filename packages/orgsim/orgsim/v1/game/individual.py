from . import base, state


class SimpleIndividual(base.Individual):
    def get_public_data(self) -> state.PublicIndividualData:
        raise NotImplementedError()

    def compute_work_coefficient(self, state: state.IndividualState) -> float:
        return 1.0
