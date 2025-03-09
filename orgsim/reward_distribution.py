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
        self,
        *,
        total: float,
        people: list[PersonalState],
    ) -> dict[str, float]:
        N = len(people)
        return {p.person.identity: total / N for p in people}


class EqualContribution(RewardDistributionStrategy):
    def compute_rewards(
        self,
        *,
        total: float,
        people: list[PersonalState],
    ) -> dict[str, float]:
        N = sum(x.contributions for x in people)
        if N == 0:
            return {}
        return {p.person.identity: p.contributions * total / N for p in people}
