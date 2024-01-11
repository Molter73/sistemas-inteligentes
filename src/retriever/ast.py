from abc import ABC, abstractmethod
from typing import List

from ..indexer.indexer import Index  # type: ignore


class AstNode(ABC):
    """Representación de un nodo del AST"""

    @abstractmethod
    def eval(self, index: Index) -> List[int]:
        """Evalúa el nodo utilizando el índice provisto

        Args:
            index (Index): Índice utilizado en la evaluación del AST
        Returns:
            List[Result]: lista de resultados que cumplen la consulta
        """
        ...


class AndNode(AstNode):
    def __init__(self, left: AstNode, right: AstNode):
        self.left = left
        self.right = right

    def eval(self, index: Index) -> List[int]:
        return list(set(self.left.eval(index)) & set(self.right.eval(index)))

    def __str__(self):
        return f"({self.left} AND {self.right})"


class OrNode(AstNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def eval(self, index: Index) -> List[int]:
        return list(
            sorted(set(self.left.eval(index)) | set(self.right.eval(index)))
        )

    def __str__(self):
        return f"({self.left} OR {self.right})"


class NotNode(AstNode):
    def __init__(self, data):
        self.data = data

    def eval(self, index: Index) -> List[int]:
        all_docs: set = set(doc.id for doc in index.documents)
        return list(all_docs - set(self.data.eval(index)))

    def __str__(self):
        return f"NOT {self.data}"


class WordNode(AstNode):
    def __init__(self, data):
        self.data = data

    def eval(self, index: Index) -> List[int]:
        return index.postings[self.data]

    def __str__(self):
        return self.data
