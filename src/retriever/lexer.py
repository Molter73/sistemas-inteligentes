from dataclasses import dataclass

WORD = 0
AND = 1
OR = 2
NOT = 3
DONE = 4

_ignorable_whitespace = " \t"


@dataclass
class Token:
    """Clase que representa un token leído por el lexer"""

    type: int
    value: str


AndToken = Token(AND, "AND")
OrToken = Token(OR, "OR")
NotToken = Token(NOT, "NOT")
DoneToken = Token(DONE, "")


class Lexer:
    """Lexer encargado de leer queries y traducirlas a tokens"""

    def __init__(self, query):
        self.query = query
        self.index = 0

    def _eat_whitespace(self):
        while (
            self.index < len(self.query)
            and self.query[self.index] in _ignorable_whitespace
        ):
            self.index += 1

    def next_token(self):
        self._eat_whitespace()

        if self.index >= len(self.query):
            return DoneToken

        token = ""
        while (
            self.index < len(self.query)
            and self.query[self.index] not in _ignorable_whitespace
        ):
            token += self.query[self.index]
            self.index += 1

        if token == "AND":
            return AndToken
        if token == "OR":
            return OrToken
        if token == "NOT":
            return NotToken
        return Token(WORD, token)
