from .ast import AndNode, AstNode, NotNode, OrNode, WordNode
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
    def __init__(self, query: str):
        self.lexer = Lexer(query)
        self.depth = 0
        self.cur_token = self.lexer.cur_token

    def _next_token(self):
        """Mueve el lexer al siguiente token"""
        self.lexer.next_token()
        self.cur_token = self.lexer.cur_token

    def _parse_word_node(self) -> AstNode:
        """Transforma un token WORD a un WordNode del AST

        Returns:
            WordNode: Un nodo del AST que representa una palabra a buscar
        """
        if self.cur_token.type != WORD:
            raise InvalidQueryException(
                f"Expected WORD, got {self.cur_token.value}"
            )

        node = WordNode(self.cur_token.value)
        self._next_token()

        return node

    def _parse_not_node(self) -> AstNode:
        """Transforma un Token NOT a un NotNode del AST

        Returns:
            NotNode: Un nodo del AST que representa una operación NOT
        """
        self._next_token()
        if self.cur_token == LParenToken:
            return NotNode(self._parse_nested_query())
        if self.cur_token.type == WORD:
            return NotNode(self._parse_word_node())

        raise InvalidQueryException(
            f"Expected WORD or (, got {self.cur_token.value}"
        )

    def _parse_nested_query(self) -> AstNode:
        """Realiza el parse de una query anidada.

        Una query anidada se representa como un par de paréntesis en la query
        global.

        Returns:
            AstNode: Un nodo de AST que representa la query anidada
        """
        # Quitamos el parentesis izquierdo
        self._next_token()

        initial_depth = self.depth
        self.depth += 1
        tree = None
        while initial_depth != self.depth and self.cur_token != DoneToken:
            tree = self._parse(tree)

        if initial_depth != self.depth:
            raise InvalidQueryException("Unbalanced parenthesis")

        if tree is None:
            raise InvalidQueryException("Empty parenthesis")

        return tree

    def _parse_infix_operation(self, left: AstNode) -> AstNode:
        """Transforma una token que representa una operación binaria en un
        nodo del AST equivalente.

        Las operaciones binarias que se soportan actualmente son AND y OR.

        Args:
            left (AstNode): nodo del AST que representa el operando izquierdo.
        Returns:
            AstNode: Un nodo del AST que representa la operación binaria.
        """
        operator = self.cur_token
        self._next_token()

        if self.cur_token == NotToken:
            right = self._parse_not_node()
        elif self.cur_token.type == WORD:
            right = self._parse_word_node()
        elif self.cur_token == LParenToken:
            right = self._parse_nested_query()
        else:
            raise InvalidQueryException(
                f"Expected WORD or NOT, got {self.cur_token.value}"
            )

        if operator == AndToken:
            return AndNode(left, right)
        elif operator == OrToken:
            return OrNode(left, right)
        raise InvalidQueryException(f"Expected AND or OR, got {operator.value}")

    def _parse(self, left: AstNode | None) -> AstNode:
        """Transforma la siguiente cadena de tokens leídos por el lexer en
        nodos del AST.

        Args:
            left (AstNode): En operaciones binarias, el lado izquierdo que ya se
                ha parseado, None en otro caso.
        Returns:
            AstNode: Un nodo del AST que representa los tokens parseados.
        """
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

    def parse(self) -> AstNode:
        """Transformar el string query en un AST que lo representa.

        Representar la query como un AST simplifica el trabajo de evaluarla.

        Returns:
            AstNode: El AST equivalente a la query.
        """
        tree = None
        while self.cur_token != DoneToken:
            tree = self._parse(tree)

        if tree is None:
            raise InvalidQueryException("Empty query")

        return tree
