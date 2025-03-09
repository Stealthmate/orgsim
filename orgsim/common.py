import random

import pydantic

IDENTITY_NUMBER = 0


def generate_identity() -> int:
    global IDENTITY_NUMBER
    IDENTITY_NUMBER += 1
    return str(IDENTITY_NUMBER)


class Person(pydantic.BaseModel):
    identity: str = pydantic.Field(default_factory=generate_identity)
    selfishness: float = pydantic.Field(default_factory=lambda: random.uniform(0, 1))

    def __hash__(self) -> int:
        return hash(self.identity)


class PersonalState(pydantic.BaseModel):
    person: Person
    age: int = 0
    gain: float
    contributions: int = 0
