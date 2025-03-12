import abc
import typing


from orgsim import framework, common


class RecruitmentStrategy(abc.ABC):
    @abc.abstractmethod
    def pick_role_models(
        self, *, state: framework.ImmutableWorldState
    ) -> typing.Iterable[str]:
        raise NotImplementedError()


class AverageOfEveryone(RecruitmentStrategy):
    def __init__(self, *, identity_generator: common.IdentityGenerator) -> None:
        self._identity_generator = identity_generator

    def pick_role_models(
        self, *, state: framework.ImmutableWorldState
    ) -> typing.Iterable[str]:
        for s in state.people_states.values():
            yield s.seed.identity


class AverageOfTopContributors(RecruitmentStrategy):
    def __init__(
        self, *, identity_generator: common.IdentityGenerator, percentile: float
    ) -> None:
        self._identity_generator = identity_generator
        self._percentile = percentile

    def pick_role_models(
        self, *, state: framework.ImmutableWorldState
    ) -> typing.Iterable[str]:
        contributors = sorted(
            list(state.people_states.values()),
            key=lambda x: x.contributions,
            reverse=True,
        )
        if not contributors:
            raise Exception("No people to compare to!")

        N = len(contributors)
        p = int(self._percentile * N) + 1
        sample = contributors[:p]

        for s in sample:
            yield s.seed.identity
