import abc
import typing

import numpy as np

from orgsim import framework, common


class RecruitmentStrategy(abc.ABC):
    @abc.abstractmethod
    def generate_recruit_candidates(
        self, *, state: framework.ImmutableWorldState
    ) -> typing.Iterable[framework.PersonSeed]:
        raise NotImplementedError()


class AverageOfEveryone(RecruitmentStrategy):
    def __init__(self, *, identity_generator: common.IdentityGenerator) -> None:
        self._identity_generator = identity_generator

    def generate_recruit_candidates(
        self, *, state: framework.ImmutableWorldState
    ) -> typing.Iterable[framework.PersonSeed]:
        m = np.average([s.seed.selfishness for s in state.people_states.values()])

        identities = [
            self._identity_generator.generate()
            for _ in range(state.seed.periodic_recruit_count)
        ]
        selfishness_values = np.clip(
            np.random.normal(
                loc=m,
                scale=0.05,
                size=state.seed.periodic_recruit_count,
            ),
            0,
            1,
        )
        for i, s in zip(identities, list(selfishness_values)):
            yield framework.PersonSeed(identity=i, selfishness=s)


class AverageOfTopContributors(RecruitmentStrategy):
    def __init__(
        self, *, identity_generator: common.IdentityGenerator, percentile: float
    ) -> None:
        self._identity_generator = identity_generator
        self._percentile = percentile

    def generate_recruit_candidates(
        self, *, state: framework.ImmutableWorldState
    ) -> typing.Iterable[framework.PersonSeed]:
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

        m = np.average([p.seed.selfishness for p in sample])

        identities = [self._identity_generator.generate() for _ in range(len(sample))]
        selfishness_values = np.clip(
            np.random.normal(
                loc=m,
                scale=0.05,
                size=state.seed.periodic_recruit_count,
            ),
            0,
            1,
        )

        for i, s in zip(identities, list(selfishness_values)):
            yield framework.PersonSeed(identity=i, selfishness=s)
