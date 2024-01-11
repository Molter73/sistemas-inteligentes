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
        super.__init__(f"Invalid query: {message}")


class Parser:
    def __init__(self, query):
        self.lexer = Lexer(query)
        self.depth = 0

    def _parse_not_node(self):
        token = self.lexer.cur_token
        if token.type != WORD:
            raise InvalidQueryException(f"Expected WORD, got {token.value}")

        return NotNode(WordNode(token.value))

    def _parse_nested_query(self):
        initial_depth = self.depth
        self.depth += 1
        tree = None
        while initial_depth != self.depth and self.lexer.cur_token != DoneToken:
            tree = self._parse(tree)
            self.lexer.next_token()

        if initial_depth != self.depth:
            raise InvalidQueryException("Unbalanced parenthesis")

        return tree

    def _parse_infix_operation(self, operator, left):
        right = self.lexer.cur_token

        if right == NotToken:
            right = self._parse_not_node()
        elif right.type == WORD:
            right = WordNode(right.value)
        elif right == LParenToken:
            self.lexer.next_token()
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
        token = self.lexer.cur_token

        if left is None:
            if token == NotToken:
                self.lexer.next_token()
                return self._parse_not_node()
            elif token.type == WORD:
                return WordNode(token.value)
            elif token == LParenToken:
                self.lexer.next_token()
                return self._parse_nested_query()
            else:
                raise InvalidQueryException(
                    f"Expected NOT or WORD, got {token.value}"
                )

        if token == RParenToken:
            if self.depth == 0:
                raise InvalidQueryException("Unbalanced parenthesis")

            self.depth -= 1
            return left

        self.lexer.next_token()
        return self._parse_infix_operation(token, left)

    def parse(self):
        tree = None
        while self.lexer.cur_token != DoneToken:
            tree = self._parse(tree)
            self.lexer.next_token()

        return tree
