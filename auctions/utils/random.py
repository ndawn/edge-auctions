from pypika.terms import Function


class Random(Function):
    def __init__(self, alias=None) -> None:
        super().__init__("RANDOM", alias=alias)