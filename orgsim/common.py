import abc


class IdentityGenerator(abc.ABC):
    @abc.abstractmethod
    def generate(self) -> str:
        raise NotImplementedError()


class SequentialIdentityGenerator(IdentityGenerator):
    def __init__(self, initial: int = 0) -> None:
        self._state: int = initial

    def generate(self) -> str:
        self._state += 1
        return str(self._state)
