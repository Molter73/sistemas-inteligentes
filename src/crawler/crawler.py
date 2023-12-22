import json
import os
import re
from argparse import Namespace
from queue import Queue
from typing import Set

import requests
from bs4 import BeautifulSoup


class Crawler:
    """Clase que representa un Crawler"""

    def __init__(self, args: Namespace):
        self.args = args
        self.url_regex = re.compile(f"^{re.escape(self.args.url)}")
        self.url_parameters_regex = re.compile(r"\?.*$")

    def crawl(self) -> None:
        """Método para crawlear la URL base. `crawl` debe crawlear, desde
        la URL base `args.url`, usando la librería `requests` de Python,
        el número máximo de webs especificado en `args.max_webs`.
        Puedes usar una cola para esto:

        https://docs.python.org/3/library/queue.html#queue.Queue

        Para cada nueva URL que se visite, debe almacenar en el directorio
        `args.output_folder` un fichero .json con, al menos, lo siguiente:

        - "url": URL de la web
        - "text": Contenido completo (en crudo, sin parsear) de la web
        """
        queue: Queue = Queue()
        queue.put(self.args.url)  # url base

        urls_visitadas: set = set()

        while not queue.empty() and len(urls_visitadas) < self.args.max_webs:
            url = queue.get()  # se extrae una url no visitada
            urls_visitadas.add(url)
            response = requests.get(url)  # se extraen todas las urls
            urls_list = self.find_urls(response.text)

            for url_crawleada in urls_list:
                if url_crawleada not in urls_visitadas:
                    queue.put(url_crawleada)

            info_web = {"url": url, "text": response.text}

            url_sin_prefijo = url.removeprefix("https://")
            directorio_limpio = re.sub(
                self.url_parameters_regex, "", url_sin_prefijo
            )

            directorios = os.path.join(
                self.args.output_folder, directorio_limpio
            )
            os.makedirs(directorios, exist_ok=True)
            web_content = os.path.join(directorios, "content.json")

            with open(web_content, "w") as f:
                json.dump(info_web, f, indent=4)

    def find_urls(self, text: str) -> Set[str]:
        """Método para encontrar URLs de la Universidad Europea en el
        texto de una web. SOLO se deben extraer URLs que aparezcan en
        como valores "href" y que sean de la Universidad, esto es,
        deben empezar por "https://universidadeuropea.com".
        `find_urls` será útil para el proceso de crawling en el método `crawl`

        Args:
            text (str): text de una web
        Returns:
            Set[str]: conjunto de urls (únicas) extraídas de la web
        """
        soup = BeautifulSoup(text, "html.parser")
        # re.compile trata a todos los caracteres del href como literales y no especiales.
        urls_filtradas = [
            link["href"] for link in soup.find_all("a", href=self.url_regex)
        ]

        return set(urls_filtradas)
