from argparse import ArgumentParser

from .parser import Parser
from .retriever import Retriever


def parse_args():
    parser = ArgumentParser(
        prog="Retriever",
        description="Script para ejecutar el retriever. El retriever recibe"
        " , como mínimo, el fichero donde se guarda el índice invertido.",
    )

    parser.add_argument(
        "-i",
        "--index-file",
        type=str,
        help="Ruta del fichero con el índice invertido",
        required=True,
    )

    parser.add_argument(
        "-q", "--query", type=str, help="Query a resolver", required=False
    )

    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="Ruta al fichero de texto con una query por línea",
        required=False,
    )
    parser.add_argument(
        "-n",
        "--max_resultados",
        type=int,
        default=10,
        help="Número de resultados",
    )

    # Añade aquí cualquier otro argumento que condicione
    # el funcionamiento del retriever

    args = parser.parse_args()
    if not args.query and not args.file:
        parser.error(
            "Debes introducir una query (-q) o un fichero (-f) con queries."
        )
    if args.query and args.file:
        parser.error(
            "Introduce solo una query (-q) o un fichero (-f), no ambos."
        )
    return args


if __name__ == "__main__":
    args = parse_args()
    retriever = Retriever(args)
    if args.query:
        parser = Parser(args.query)
        ast = parser.parse()
        for res in retriever.search_query(ast):
            print(res)
    elif args.file:
        for query, results in retriever.search_from_file(args.file).items():
            print(f"#### {query} ####")
            for res in results:
                print(res)
