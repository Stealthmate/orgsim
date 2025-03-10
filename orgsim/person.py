import pydantic


class PersonParams(pydantic.BaseModel):
    identity: str
    selfishness: float

    def __hash__(self) -> int:
        return hash(self.identity)
