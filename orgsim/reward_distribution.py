import abc

from orgsim.common import PersonalState


class RewardDistributionStrategy(abc.ABC):
    @abc.abstractmethod
    def compute_rewards(
        self, *, total: float, people: list[PersonalState]
    ) -> dict[str, float]:
        raise NotImplementedError()


class AllEqual(RewardDistributionStrategy):
    def compute_rewards(
        self, *, total: float, people: list[PersonalState]
    ) -> dict[str, float]:
        N = len(people)
        return {p.person.identity: total / N for p in people}
