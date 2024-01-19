import math
import pickle as pkl
from argparse import Namespace
from dataclasses import dataclass
from time import time
from typing import Dict, List

from ..indexer.indexer import Document, Index  # type: ignore
from .ast import AstNode
from .parser import Parser


@dataclass
class Result:
    """Clase que contendrá un resultado de búsqueda"""

    url: str
    snippet: str
    score: float

    def __str__(self) -> str:
        return f"({self.score}) {self.url} -> {self.snippet}"


class Retriever:
    """Clase que representa un recuperador"""

    def __init__(self, args: Namespace):
        self.args = args
        self.index = self.load_index()

    def search_query(self, query: AstNode) -> List[Result]:
        """Método para resolver una query.
        Este método debe ser capaz, al menos, de resolver consultas como:
        "grado AND NOT master OR docencia", con un procesado de izquierda
        a derecha. Por simplicidad, podéis asumir que los operadores AND,
        NOT y OR siempre estarán en mayúsculas.

        Ejemplo para "grado AND NOT master OR docencia":

        posting["grado"] = [1,2,3] (doc ids que tienen "grado")
        NOT posting["master"] = [3, 4, 5] (doc ids que no tienen "master")
        posting["docencia"] = [6] (doc ids que tienen docencia)

        [1, 2, 3] AND [3, 4, 5] OR [6] = [3] OR [6] = [3, 6]

        Args:
            query (str): consulta a resolver
        Returns:
            List[Result]: lista de resultados que cumplen la consulta
        """
        terms = query.get_words()

        res = [
            self.int_to_result(index, terms) for index in query.eval(self.index)
        ]
        res.sort(key=lambda x: x.score, reverse=True)

        return self.args.max_resultados

    def int_to_result(self, index: int, terms: List[str]) -> Result:
        res = self.index.documents[index]
        score = self.score(terms, res)
        return Result(url=res.url, snippet=res.snippet, score=score)

    def search_from_file(self, fname: str) -> Dict[str, List[Result]]:
        """Método para hacer consultas desde fichero.
        Debe ser un fichero de texto con una consulta por línea.

        Args:
            fname (str): ruta del fichero con consultas
        Return:
            Dict[str, List[Result]]: diccionario con resultados de cada consulta
        """
        resultados = {}

        with open(fname, "r") as fr:
            ts = time()

            # Las siguientes dos líneas son para dejar feliz a los linters,
            # eliminarlas al implementar la versión final del código.
            n_queries = 0

            for query in fr.readlines():
                parser = Parser(query)
                ast = parser.parse()
                resultados[f"{ast}"] = self.search_query(ast)

            te = time()
            print(f"Time to solve {n_queries}: {te - ts}")
        return resultados

    def load_index(self) -> Index:
        """Método para cargar un índice invertido desde disco."""
        with open(self.args.index_file, "rb") as fr:
            return pkl.load(fr)

    def score(self, terms: List[str], document: Document) -> float:
        tf = 0
        for term in terms:
            tf += document.text.count(term.lower())

        acc = 0.0
        for word in set(terms):
            if word in document.text:
                acc += math.pow(terms.count(word), 2)

        # El término no está en el documento
        if acc == 0.0:
            return 0.0

        score = tf / (document.partial_score * math.sqrt(acc))
        return score
