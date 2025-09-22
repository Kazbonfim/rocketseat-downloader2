# POC: https://gist.github.com/felipeadeildo, obrigado 🤲
# Feito a partir de https://github.com/alefd2/script-download-lessons-rs 🚀
# Para executar tenha Python, FFmpeg, e Yt-dlp instalados, e definidos em seu PATH no Windows!
# Rod > pip install m3u8 requests beautifulsoup4
# Importações úteis
import json
import os
import pickle
import re
import time
import shutil
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE_API = "https://skylab-api.rocketseat.com.br"
BASE_URL = "https://app.rocketseat.com.br"
SESSION_PATH = Path(os.getenv("SESSION_DIR", ".")) / ".session.pkl"
SESSION_PATH.parent.mkdir(exist_ok=True)


def clear_screen():
    return


def sanitize_string(string: str):
    return re.sub(r'[@#$%&*/:^{}<>?"]', "", string).strip()


def check_dependencies():
    print("Verificando dependências do sistema...")
    required_commands = ["ffmpeg", "yt-dlp"]
    missing_commands = []

    for command in required_commands:
        if shutil.which(command) is None:
            missing_commands.append(command)

    if missing_commands:
        print(
            "\nERRO: Dependências não encontradas. Por favor, instale os seguintes programas:"
        )
        for command in missing_commands:
            print(f" - {command}")
        print("\nLinks para instalação:")
        print(" - FFmpeg: https://ffmpeg.org/download.html")
        print(" - yt-dlp: https://github.com/yt-dlp/yt-dlp")
        sys.exit(1)

    print("✓ Todas as dependências foram encontradas.")


class DownloadReport:
    def __init__(self):
        self.successful_downloads = []
        self.failed_downloads = []
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = datetime.now()
        print(f"Início do download: {self.start_time.strftime('%d/%m/%Y %H:%M:%S')}")

    def add_success(self, module_title, lesson_title):
        self.successful_downloads.append(
            {
                "module": module_title,
                "lesson": lesson_title,
                "timestamp": datetime.now(),
            }
        )
        print(f"✓ Aula baixada com sucesso: {module_title} - {lesson_title}")

    def add_failure(self, module_title, lesson_title, error):
        self.failed_downloads.append(
            {
                "module": module_title,
                "lesson": lesson_title,
                "error": str(error),
                "timestamp": datetime.now(),
            }
        )
        print(f"✗ Erro ao baixar aula: {module_title} - {lesson_title}")
        print(f"   Erro: {str(error)}")

    def finish(self):
        self.end_time = datetime.now()
        self.generate_report()

    def generate_report(self):
        if not self.start_time or not self.end_time:
            return "Relatório incompleto - download não finalizado"

        duration = self.end_time - self.start_time
        total_attempts = len(self.successful_downloads) + len(self.failed_downloads)

        report = [
            "=== RELATÓRIO DE DOWNLOAD ===",
            f"Data: {self.end_time.strftime('%d/%m/%Y %H:%M:%S')}",
            f"Duração total: {duration}",
            f"Total de aulas: {total_attempts}",
            f"Aulas baixadas com sucesso: {len(self.successful_downloads)}",
            f"Aulas com erro: {len(self.failed_downloads)}",
            "\n=== AULAS BAIXADAS COM SUCESSO ===",
        ]

        for download in self.successful_downloads:
            report.append(f"- Módulo: {download['module']}")
            report.append(f"  Aula: {download['lesson']}")
            report.append(f"  Horário: {download['timestamp'].strftime('%H:%M:%S')}")

        if self.failed_downloads:
            report.append("\n=== AULAS COM ERRO ===")
            for download in self.failed_downloads:
                report.append(f"- Módulo: {download['module']}")
                report.append(f"  Aula: {download['lesson']}")
                report.append(f"  Erro: {download['error']}")
                report.append(
                    f"  Horário: {download['timestamp'].strftime('%H:%M:%S')}"
                )

        report_text = "\n".join(report)
        report_path = (
            Path("relatorios")
            / f"relatorio_{self.end_time.strftime('%Y%m%d_%H%M%S')}.txt"
        )
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        print("\n" + "=" * 50)
        print(report_text)
        print("=" * 50)
        print(f"\nRelatório salvo em: {report_path}")


class CDNVideo:
    def __init__(self, video_id: str, save_path: str):
        self.video_id = video_id
        self.save_path = str(save_path)
        self.domain = "vz-dc851587-83d.b-cdn.net"
        self.referer = "https://iframe.mediadelivery.net/"
        self.origin = "https://iframe.mediadelivery.net"

    def download(self):
        if os.path.exists(self.save_path):
            print(f"\tArquivo já existe: {os.path.basename(self.save_path)}. Pulando.")
            return True

        print(f"Baixando com yt-dlp (CDN): {os.path.basename(self.save_path)}")
        playlist_url = f"https://{self.domain}/{self.video_id}/playlist.m3u8"

        ytdlp_cmd = (
            f'yt-dlp "{playlist_url}" '
            f"--merge-output-format mp4 "
            f"--concurrent-fragments 10 "
            f'--add-header "Referer: {self.referer}" '
            f'--add-header "Origin: {self.origin}" '
            f'-o "{self.save_path}"'
        )

        exit_code = os.system(ytdlp_cmd)
        if exit_code == 0:
            print("✓ Download (CDN) concluído com sucesso!")
            return True
        else:
            print(f"✗ Erro ao executar yt-dlp para CDN (código de saída: {exit_code}).")
            return False


class VideoDownloader:
    def __init__(self, video_id: str, save_path: str):
        self.video_id = video_id
        self.save_path = save_path
        print(video_id, "Dados dos vídeos em plaintext para Debug")
        self.cdn = CDNVideo(video_id, save_path)

    def download(self):
        print("--- Iniciando tentativa de download ---")
        print(
            "Realizando download das aulas via CDN, por favor, aguarde enquanto processamos os dados!"
        )
        if self.cdn.download():
            print("-----------------------------------------")
            return
        print("\n✗ Não foi possível baixar o vídeo de nenhuma das fontes disponíveis.")
        print("-----------------------------------------")


class Rocketseat:
    def __init__(self):
        self._session_exists = SESSION_PATH.exists()
        if self._session_exists:
            print("Carregando sessão salva...")
            self.session = pickle.load(SESSION_PATH.open("rb"))
        else:
            self.session = requests.session()
            self.session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    "Referer": BASE_URL,
                }
            )
        self.download_report = DownloadReport()

    def login(self, username: str, password: str):
        print("Realizando login...")
        payload = {"email": username, "password": password}
        res = self.session.post(f"{BASE_API}/sessions", json=payload)
        res.raise_for_status()
        data = res.json()

        self.session.headers["Authorization"] = (
            f"{data['type'].capitalize()} {data['token']}"
        )
        self.session.cookies.update(
            {
                "skylab_next_access_token_v3": data["token"],
                "skylab_next_refresh_token_v3": data["refreshToken"],
            }
        )

        account_infos = self.session.get(f"{BASE_API}/account").json()
        print(f"Bem-vindo, {account_infos['name']}!")
        pickle.dump(self.session, SESSION_PATH.open("wb"))

    def __load_modules(self, specialization_slug: str):
        print(f"Buscando módulos para a formação: {specialization_slug}")
        url = f"{BASE_API}/journeys/{specialization_slug}"
        print(f"[DEBUG] Buscando módulos com a URL: {url}")

        try:
            res = self.session.get(url)
            res.raise_for_status()
            journey_data = res.json()
            modules_data = journey_data.get("nodes", [])
            print(f"Encontrados {len(modules_data)} módulos.")
            return modules_data
        except Exception as e:
            print(f"✗ Erro ao buscar módulos: {e}")
            return []

    def __load_lessons_from_module(self, module_slug: str):
        print(f"Buscando lições para o módulo: {module_slug}")
        url = f"{BASE_API}/journey-nodes/{module_slug}"

        try:
            res = self.session.get(url)
            res.raise_for_status()
            module_data = res.json()

            groups = []
            if "group" in module_data and module_data.get("group"):
                main_group = module_data["group"]
                group_title = main_group.get("title", "Aulas do Módulo")
                lessons_raw = main_group.get("lessons", [])
                lessons_processed = []

                for lesson_item in lessons_raw:
                    if "last" in lesson_item and lesson_item.get("last"):
                        lesson_data = lesson_item["last"]
                        lesson_data["group_title"] = group_title
                        lessons_processed.append(lesson_data)

                if lessons_processed:
                    groups.append({"title": group_title, "lessons": lessons_processed})

            if not groups:
                print(f"[AVISO] Nenhuma aula encontrada para o módulo {module_slug}.")

            print(
                f"Encontrados {len(groups)} grupos com um total de {sum(len(g['lessons']) for g in groups)} lições."
            )
            return groups

        except Exception as e:
            print(f"✗ Erro ao processar lições do módulo {module_slug}: {e}")
            return []

    def _download_video(self, video_id: str, save_path: Path):
        VideoDownloader(video_id, str(save_path / "aulinha.mp4")).download()

    def _download_lesson(
        self, lesson: dict, save_path: Path, group_index: int, lesson_index: int
    ):
        if isinstance(lesson, dict) and "title" in lesson:
            title = lesson.get("title", "Sem título")
            group_title = lesson.get("group_title", "Sem Grupo")
            print(
                f"\tBaixando aula {group_index}.{lesson_index}: {title} (Grupo: {group_title})"
            )

            try:
                group_folder = (
                    save_path / f"{group_index:02d}. {sanitize_string(group_title)}"
                )
                group_folder.mkdir(exist_ok=True)
                base_name = f"{lesson_index:02d}. {sanitize_string(title)}"

                with open(
                    group_folder / f"{base_name}.txt", "w", encoding="utf-8"
                ) as f:
                    f.write(f"Grupo: {group_title}\n")
                    f.write(f"Aula: {title}\n\n")
                    if "description" in lesson and lesson["description"]:
                        f.write(f"Descrição:\n{lesson['description']}\n\n")
                    if "duration" in lesson:
                        minutes = lesson["duration"] // 60
                        seconds = lesson["duration"] % 60
                        f.write(f"Duração: {minutes}min {seconds}s\n")
                    if (
                        "author" in lesson
                        and lesson["author"]
                        and isinstance(lesson["author"], dict)
                    ):
                        author_name = lesson["author"].get("name", "")
                        if author_name:
                            f.write(f"Autor: {author_name}\n")

                if "resource" in lesson and lesson["resource"]:
                    resource = (
                        lesson["resource"].split("/")[-1]
                        if "/" in lesson["resource"]
                        else lesson["resource"]
                    )
                    VideoDownloader(
                        resource, str(group_folder / f"{base_name}.mp4")
                    ).download()
                    self.download_report.add_success(group_title, title)
                else:
                    print(f"\tAula '{title}' não tem recurso de vídeo")
                    self.download_report.add_success(group_title, title)

                if "downloads" in lesson and lesson["downloads"]:
                    downloads_dir = group_folder / f"{base_name}_arquivos"
                    downloads_dir.mkdir(exist_ok=True)
                    for download in lesson["downloads"]:
                        if "file_url" in download and download["file_url"]:
                            download_url = download["file_url"]
                            download_title = download.get("title", "arquivo")
                            file_ext = os.path.splitext(download_url)[1]
                            download_path = (
                                downloads_dir
                                / f"{sanitize_string(download_title)}{file_ext}"
                            )
                            print(f"\t\tBaixando material: {download_title}")
                            try:
                                response = requests.get(download_url)
                                response.raise_for_status()
                                with open(download_path, "wb") as f:
                                    f.write(response.content)
                                print(f"\t\tMaterial salvo em: {download_path}")
                            except Exception as e:
                                print(f"\t\tErro ao baixar material: {e}")
            except Exception as e:
                self.download_report.add_failure(group_title, title, e)
                print(f"\tErro ao baixar aula: {str(e)}")
        else:
            print(f"\tFormato de aula não reconhecido: {lesson}")

    def _download_courses(self, specialization_slug: str, specialization_name: str):
        print(f"Baixando cursos da especialização: {specialization_name}")
        self.download_report.start()

        try:
            modules = self.__load_modules(specialization_slug)
            if not modules:
                print("Nenhum módulo encontrado para esta especialização.")
                return

            print("\nEscolha os módulos que você quer baixar:")
            print("[0] - Baixar todos os módulos")
            for i, module in enumerate(modules, 1):
                module_type = module.get("type", "desconhecido")
                print(f"[{i}] - {module['title']} (Tipo: {module_type})")

            choices_str = input(
                "Digite 0 para baixar todos ou os números dos módulos separados por vírgula (ex: 1, 3, 5): "
            )

            if choices_str.strip() == "0":
                selected_modules = modules
                print("\nBaixando todos os módulos...")
            else:
                try:
                    selected_indices = [
                        int(choice.strip()) - 1 for choice in choices_str.split(",")
                    ]
                    selected_modules = [
                        modules[i] for i in selected_indices if 0 <= i < len(modules)
                    ]
                except (ValueError, IndexError):
                    print("Seleção inválida. Abortando.")
                    return

            for module in selected_modules:
                module_title = module["title"]
                module_slug = module.get("slug")
                module_type = module.get("type")

                print(f"\nProcessando módulo: '{module_title}' (Tipo: {module_type})")

                if module_type == "group" and module_slug:
                    course_name = module.get("course", {}).get("title", "Curso Padrão")
                    save_path = (
                        Path("Cursos")
                        / sanitize_string(specialization_name)
                        / sanitize_string(course_name)
                        / sanitize_string(module_title)
                    )
                    save_path.mkdir(parents=True, exist_ok=True)

                    print(f"Buscando aulas para o cluster slug: {module_slug}")
                    groups = self.__load_lessons_from_module(module_slug)

                    if not groups:
                        print(
                            f"Nenhum grupo ou aula encontrado para o módulo: {module_title}"
                        )
                        continue

                    for group_index, group in enumerate(groups, 1):
                        group_title = group["title"]
                        print(f"\nProcessando grupo {group_index}: {group_title}")

                        for lesson_index, lesson in enumerate(group["lessons"], 1):
                            self._download_lesson(
                                lesson, save_path, group_index, lesson_index
                            )

                        print(f"Grupo {group_index} ('{group_title}') concluído!")
                else:
                    print(
                        f"Módulo '{module_title}' não é um cluster de aulas ou não possui slug. Pulando."
                    )

        finally:
            self.download_report.finish()

    def select_specializations(self):
        print("Buscando especializações disponíveis...")
        params = {
            "types[0]": "SPECIALIZATION",
            "types[1]": "COURSE",
            "types[2]": "EXTRA",
            "limit": "60",
            "offset": "0",
            "page": "1",
            "sort_by": "relevance",
        }
        specializations = self.session.get(
            f"{BASE_API}/catalog/list", params=params
        ).json()["items"]
        clear_screen()
        print("Selecione uma formação ou 0 para selecionar todas:")
        for i, specialization in enumerate(specializations, 1):
            print(f"[{i}] - {specialization['title']}")

        choice = int(input(">> "))
        if choice == 0:
            for specialization in specializations:
                self._download_courses(specialization["slug"], specialization["title"])
        else:
            specialization = specializations[choice - 1]
            self._download_courses(specialization["slug"], specialization["title"])

    def run(self):
        if not self._session_exists:
            self.login(
                username=input("Seu email Rocketseat: "), password=input("Sua senha: ")
            )
        self.select_specializations()


if __name__ == "__main__":
    check_dependencies()
    print("\nIniciando o processo de download...")
    agent = Rocketseat()
    agent.run()
