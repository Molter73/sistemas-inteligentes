from dataclasses import dataclass

WORD = 0
AND = 1
OR = 2
NOT = 3
LPAREN = 4
RPAREN = 5
DONE = 6

_ignorable_whitespace = " \t\n"
_delimiters = _ignorable_whitespace + "()"


@dataclass
class Token:
    """Clase que representa un token leído por el lexer"""

    type: int
    value: str


AndToken = Token(AND, "AND")
OrToken = Token(OR, "OR")
NotToken = Token(NOT, "NOT")
DoneToken = Token(DONE, "")
LParenToken = Token(LPAREN, "(")
RParenToken = Token(RPAREN, ")")


class Lexer:
    """Lexer encargado de leer queries y traducirlas a tokens"""

    def __init__(self, query: str):
        self.query = query
        self.index = 0
        # Asignado a DoneToken para que el linter sea feliz
        self.cur_token = DoneToken
        self.next_token()

    def _eat_whitespace(self):
        """Método que elimina espacios en blanco de la query procesada."""
        while (
            self.index < len(self.query)
            and self.query[self.index] in _ignorable_whitespace
        ):
            self.index += 1

    def next_token(self):
        """Mueve el lexer al próximo token."""
        self._eat_whitespace()

        if self.index >= len(self.query):
            self.cur_token = DoneToken
            return

        if self.query[self.index] == "(":
            self.index += 1
            self.cur_token = LParenToken
            return

        if self.query[self.index] == ")":
            self.index += 1
            self.cur_token = RParenToken
            return

        offset = 0
        while (
            self.index + offset < len(self.query)
            and self.query[self.index + offset] not in _delimiters
        ):
            offset += 1

        token = self.query[self.index : self.index + offset]
        self.index += offset
        if token == "AND":
            self.cur_token = AndToken
        elif token == "OR":
            self.cur_token = OrToken
        elif token == "NOT":
            self.cur_token = NotToken
        else:
            self.cur_token = Token(WORD, token)
