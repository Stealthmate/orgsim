import abc

from orgsim import framework


class PersonActionStrategy(abc.ABC):
    @abc.abstractmethod
    def act(self, *, state: framework.ImmutableWorldState, identity: str) -> float:
        raise NotImplementedError()


class ConstantSelfishness(PersonActionStrategy):
    def act(self, *, state: framework.ImmutableWorldState, identity: str) -> float:
        return 1 - state.people_states[identity].seed.selfishness
