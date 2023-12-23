import math
import pickle as pkl
from argparse import Namespace
from dataclasses import dataclass
from time import time
from typing import Dict, List

from ..indexer.indexer import Index  # type: ignore


@dataclass
class Result:
    """Clase que contendrá un resultado de búsqueda"""

    url: str
    snippet: str

    def __str__(self) -> str:
        return f"{self.url} -> {self.snippet}"


class Retriever:
    """Clase que representa un recuperador"""

    def __init__(self, args: Namespace):
        self.args = args
        self.index = self.load_index()

    def _search_query(self, query: List[str], left: List[int]) -> List[int]:
        if len(query) == 0:
            return left

        right = []
        token = query.pop(0)
        if token == "AND":
            if query[0] == "NOT":
                query.pop(0)
                right = self._not_(self.index.postings[query.pop(0)])
            else:
                right = self.index.postings[query.pop(0)]
            left = self._and_(left, right)
        elif token == "OR":
            if query[0] == "NOT":
                query.pop(0)
                right = self._not_(self.index.postings[query.pop(0)])
            else:
                right = self.index.postings[query.pop(0)]
            left = self._or_(left, right)
        else:
            raise RuntimeError("Parametro desconocido")

        return self._search_query(query, left)

    def search_query(self, query: str) -> List[Result]:
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
        import pdb

        pdb.set_trace()
        tokens = query.split()

        left = []
        if tokens[0] == "NOT":
            tokens.pop(0)
            left = self._not_(self.index.postings[tokens.pop(0)])
        else:
            left = self.index.postings[tokens.pop(0)]

        self._search_query(tokens, left)

        return []

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
            fr.read()

            for line in fr:
                query = line.strip()
                resultados[query] = self.search_query(query)

            te = time()
            print(f"Time to solve {n_queries}: {te - ts}")
        return resultados

    def load_index(self) -> Index:
        """Método para cargar un índice invertido desde disco."""
        with open(self.args.index_file, "rb") as fr:
            return pkl.load(fr)

    def _and_(self, posting_a: List[int], posting_b: List[int]) -> List[int]:
        """Método para calcular la intersección de dos posting lists.
        Será necesario para resolver queries que incluyan "A AND B"
        en `search_query`.

        Args:
            posting_a (List[int]): una posting list
            posting_b (List[int]): otra posting list
        Returns:
            List[int]: posting list de la intersección
        """
        return list(set(posting_a) & set(posting_b))

    def _or_(self, posting_a: List[int], posting_b: List[int]) -> List[int]:
        """Método para calcular la unión de dos posting lists.
        Será necesario para resolver queries que incluyan "A OR B"
        en `search_query`.

        Args:
            posting_a (List[int]): una posting list
            posting_b (List[int]): otra posting list
        Returns:
            List[int]: posting list de la unión
        """
        return list(sorted(set(posting_a) | set(posting_b)))

    def _not_(self, posting_a: List[int]) -> List[int]:
        """Método para calcular el complementario de una posting list.
        Será necesario para resolver queries que incluyan "NOT A"
        en `search_query`

        Args:
            posting_a (List[int]): una posting list
        Returns:
            List[int]: complementario de la posting list
        """
        all_docs: set = set(self.index.ids_all_docs)
        return list(all_docs - set(posting_a))

    def score(
        self, query: str, resultados: List[Result], N: float = 10.0
    ) -> List[Result]:
        score_results = []
        for r in resultados:
            score = self._calcular_tfidf_score(query, r)
            score_results.append((r, score))

        score_results.sort(key=lambda x: x[1], reverse=True)

        return [r for r, _ in score_results[: int(N)]]

    def _calcular_tfidf_score(self, query: str, resultado: Result) -> float:
        score = 0.0
        term_query = query.split()

        """La variable ids_total_docs se sustituirá por la que contenga el 
        indice de los archivos extraidos"""
        total_files = len(self.index.ids_total_docs)
        for term in term_query:
            tf = resultado.snippet.lower().count(term.lower())
            documentos_con_termino = self._contar_documentos(term)

            if documentos_con_termino > 0:
                idf = math.log(total_files / documentos_con_termino)
                score += tf * idf

        return score

    def _contar_documentos(self, term: str) -> int:
        return len(self.index.postings.get(term, []))
