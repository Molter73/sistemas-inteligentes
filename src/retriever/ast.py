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

    @abstractmethod
    def get_words(self) -> List[str]:
        """Busca y retorna el texto de todos los WordNode del árbol

        Returns:
            List[str]: Los términos de la query.
        """
        ...


class AndNode(AstNode):
    def __init__(self, left: AstNode, right: AstNode):
        self.left = left
        self.right = right

    def eval(self, index: Index) -> List[int]:
        return list(set(self.left.eval(index)) & set(self.right.eval(index)))

    def get_words(self) -> List[str]:
        res = self.left.get_words()
        res.extend(self.right.get_words())
        return res

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

    def get_words(self) -> List[str]:
        res = self.left.get_words()
        res.extend(self.right.get_words())
        return res

    def __str__(self):
        return f"({self.left} OR {self.right})"


class NotNode(AstNode):
    def __init__(self, data):
        self.data = data

    def eval(self, index: Index) -> List[int]:
        all_docs: set = set(doc.id for doc in index.documents)
        return list(all_docs - set(self.data.eval(index)))

    def get_words(self) -> List[str]:
        return self.data.get_words()

    def __str__(self):
        return f"NOT {self.data}"


class WordNode(AstNode):
    def __init__(self, data):
        self.data = data

    def eval(self, index: Index) -> List[int]:
        return index.postings.get(self.data, [])

    def get_words(self) -> List[str]:
        return [self.data]

    def __str__(self):
        return self.data
