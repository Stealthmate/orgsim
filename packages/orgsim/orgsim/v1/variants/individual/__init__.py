# import numpy as np
from orgsim.v1.game import IndividualStrategy, IndividualStrategyStateView


class Human(IndividualStrategy):
    def compute_work_coefficient(self, state: IndividualStrategyStateView) -> float:
        v = -1.0
        while not (0 < v < 1):
            v = float(input("Enter a contirbution value: "))
        return v


class Slave(IndividualStrategy):
    def compute_work_coefficient(self, state: IndividualStrategyStateView) -> float:
        return 0.9


# class Slave(game.IndividualStrategy):
#     def get_public_data(self) -> game.PublicIndividualData:
#         return game.PublicIndividualData()

#     def compute_work_coefficient(self, state: game.IndividualStateView) -> float:
#         return float(np.clip(np.random.normal(loc=0.5, scale=0.1, size=1), 0, 1))
