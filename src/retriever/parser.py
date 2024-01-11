from .ast import AndNode, NotNode, OrNode, WordNode
from .lexer import (
    WORD,
    AndToken,
    DoneToken,
    Lexer,
    LParenToken,
    NotToken,
    OrToken,
    RParenToken,
)


class InvalidQueryException(Exception):
    def __init__(self, message):
        super().__init__(f"Invalid query: {message}")


class Parser:
    def __init__(self, query):
        self.lexer = Lexer(query)
        self.depth = 0
        self.cur_token = self.lexer.cur_token

    def _next_token(self):
        self.lexer.next_token()
        self.cur_token = self.lexer.cur_token

    def _parse_word_node(self):
        if self.cur_token.type != WORD:
            raise InvalidQueryException(
                f"Expected WORD, got {self.cur_token.value}"
            )

        node = WordNode(self.cur_token.value)
        self._next_token()

        return node

    def _parse_not_node(self):
        self._next_token()

        return NotNode(self._parse_word_node())

    def _parse_nested_query(self):
        # Quitamos el parentesis izquierdo
        self._next_token()

        initial_depth = self.depth
        self.depth += 1
        tree = None
        while initial_depth != self.depth and self.cur_token != DoneToken:
            tree = self._parse(tree)

        if initial_depth != self.depth:
            raise InvalidQueryException("Unbalanced parenthesis")

        return tree

    def _parse_infix_operation(self, left):
        operator = self.cur_token
        self._next_token()
        right = self.cur_token

        if right == NotToken:
            right = self._parse_not_node()
        elif right.type == WORD:
            right = self._parse_word_node()
        elif right == LParenToken:
            right = self._parse_nested_query()
        else:
            raise InvalidQueryException(
                f"Expected WORD or NOT, got {right.value}"
            )

        if operator == AndToken:
            return AndNode(left, right)
        elif operator == OrToken:
            return OrNode(left, right)
        raise InvalidQueryException(f"Expected AND or OR, got {operator.value}")

    def _parse(self, left):
        if left is None:
            if self.cur_token == NotToken:
                return self._parse_not_node()
            elif self.cur_token.type == WORD:
                return self._parse_word_node()
            elif self.cur_token == LParenToken:
                return self._parse_nested_query()
            else:
                raise InvalidQueryException(
                    f"Expected NOT or WORD, got {self.cur_token.value}"
                )

        if self.cur_token == RParenToken:
            if self.depth == 0:
                raise InvalidQueryException("Unbalanced parenthesis")

            self.depth -= 1
            self._next_token()
            return left

        return self._parse_infix_operation(left)

    def parse(self):
        tree = None
        while self.cur_token != DoneToken:
            tree = self._parse(tree)

        return tree
