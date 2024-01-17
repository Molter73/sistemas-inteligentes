import asyncio
import io
import json
import os
import re
import time
from argparse import Namespace
from queue import Queue
from typing import Set

import requests  # type: ignore
from bs4 import BeautifulSoup
from pypdf import PdfReader


class Crawler:
    """Clase que representa un Crawler"""

    def __init__(self, args: Namespace):
        self.args = args
        self.url_regex = re.compile(f"^{re.escape(self.args.url)}")
        self.pdf_regex = re.compile(r"^\/.*\.pdf$")
        self.url_parameters_regex = re.compile(r"\?.*$")
        self.urls_visitadas: set = set()

    async def _crawl(self, url: str) -> dict:
        print(f"Crawling {url}...")
        response = await asyncio.to_thread(
            requests.get, url
        )  # se extraen todas las urls

        if response.status_code != 200:
            return {
                "url": url,
                "status_code": response.status_code,
            }

        if not url.endswith(".pdf"):
            urls_list = self.find_urls(response.text)
            text = response.text
            type = "html"
        else:
            urls_list = set()
            text = self.read_pdf(response.content)
            type = "pdf"

        print(f"Done crawling {url}")
        return {
            "url": url,
            "text": text,
            "crawled_urls": urls_list,
            "status_code": response.status_code,
            "type": type,
        }

    async def crawl(self) -> None:
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

        throtle = False
        while not queue.empty() and len(urls_visitadas) < self.args.max_webs:
            tasks: list = []
            if throtle:
                print("Esperando un segundo...")
                time.sleep(1)
                throtle = False

            async with asyncio.TaskGroup() as tg:
                while (
                    not queue.empty()
                    and len(urls_visitadas) < self.args.max_webs
                    and len(tasks) < self.args.jobs
                ):
                    url = queue.get()
                    if url not in urls_visitadas:
                        urls_visitadas.add(url)
                        tasks.append(tg.create_task(self._crawl(url)))

            for task in tasks:
                res = task.result()
                status_code = res["status_code"]

                if status_code != 200:
                    urls_visitadas.remove(res["url"])
                    queue.put(res["url"])

                    # Fallo por demasiadas peticiones, esperamos antes de
                    # reintentar.
                    if status_code == 429:
                        throtle = True
                    continue

                for url in res["crawled_urls"]:
                    if url not in urls_visitadas:
                        queue.put(url)

                self.dump_data(res["url"], res["text"], res["type"])

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
        # Buscar enlaces a páginas web
        urls_filtradas = {
            link["href"] for link in soup.find_all("a", href=self.url_regex)
        }

        # Buscar enlaces a archivos PDF
        urls_filtradas.update(
            {
                f"{self.args.url}{link['href']}"
                for link in soup.find_all("a", href=self.pdf_regex)
            }
        )

        return urls_filtradas

    def read_pdf(self, content: bytes) -> str:
        content_stream = io.BytesIO(content)
        pdf = PdfReader(content_stream)
        text = ""
        for page in pdf.pages:
            text += page.extract_text(0)

        return text

    def dump_data(self, url: str, text: str, type: str):
        info_web = {"url": url, "text": text, "type": type}

        url_sin_prefijo = url.removeprefix("https://")
        directorio_limpio = re.sub(
            self.url_parameters_regex, "", url_sin_prefijo
        )

        directorios = os.path.join(self.args.output_folder, directorio_limpio)
        os.makedirs(directorios, exist_ok=True)
        web_content = os.path.join(directorios, "content.json")

        with open(web_content, "w") as f:
            json.dump(info_web, f, indent=4)
