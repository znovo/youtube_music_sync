import json
import re
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# ============================================================
# CONFIGURAÇÃO
# ============================================================

APP_DIR = Path(__file__).resolve().parent
LIBRARY_FILE = APP_DIR / "library.json"

DEFAULT_DOWNLOAD_DIR = Path(r"F:\play")
DEFAULT_BROWSER = "firefox"

AUDIO_EXTENSIONS = {
    ".mp3",
    ".m4a",
    ".aac",
    ".flac",
    ".wav",
    ".ogg",
    ".opus",
    ".webm"
}


# ============================================================
# FLAGS DO YT-DLP
# ============================================================

def yt_dlp_base_args(browser):
    return [
        "--js-runtimes",
        "node",

        "--remote-components",
        "ejs:github",

        "--cookies-from-browser",
        browser,

        "--extractor-args",
        "youtube:player_client=android_vr,web_embedded",

        "--no-warnings"
    ]


# ============================================================
# BIBLIOTECA
# ============================================================

def load_library():
    if not LIBRARY_FILE.exists():
        return {}

    try:
        with open(
            LIBRARY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return {}

        return data

    except Exception:
        return {}


def save_library(library):
    temp_file = LIBRARY_FILE.with_suffix(".tmp")

    with open(
        temp_file,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            library,
            f,
            ensure_ascii=False,
            indent=2
        )

    temp_file.replace(LIBRARY_FILE)


def sanitize_filename(name):
    name = re.sub(
        r'[<>:"/\\|?*]',
        "",
        name
    )

    name = name.strip()

    if not name:
        name = "Unknown"

    return name


def normalize_name(name):
    """
    Normaliza nomes para facilitar a comparação
    entre playlist e arquivos existentes.
    """

    name = Path(name).stem

    # Remove ID [abcdef]
    name = re.sub(
        r"\s*\[[A-Za-z0-9_-]{6,}\]\s*$",
        "",
        name
    )

    name = name.lower()

    # Remove caracteres especiais
    name = re.sub(
        r"[^a-z0-9áéíóúãõâêôç ]+",
        " ",
        name
    )

    # Normaliza espaços
    name = re.sub(
        r"\s+",
        " ",
        name
    )

    return name.strip()


# ============================================================
# INDEXAÇÃO DA PASTA
# ============================================================

def scan_existing_files(folder):
    """
    Encontra todas as músicas existentes na pasta.

    Retorna:
        nome_normalizado -> caminho
    """

    existing = {}

    if not folder.exists():
        folder.mkdir(
            parents=True,
            exist_ok=True
        )

    for file in folder.rglob("*"):

        if not file.is_file():
            continue

        if file.suffix.lower() not in AUDIO_EXTENSIONS:
            continue

        normalized = normalize_name(
            file.name
        )

        if normalized:
            existing[normalized] = file

    return existing


# ============================================================
# YT-DLP
# ============================================================

def check_yt_dlp():
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--version"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return result.stdout.strip()

    except FileNotFoundError:
        pass

    return None


def get_playlist(url, browser):
    """
    Obtém os vídeos da playlist sem baixar nada.
    """

    command = [
        "yt-dlp",

        *yt_dlp_base_args(browser),

        "--flat-playlist",

        "--dump-single-json",

        "--no-playlist",

        url
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

    except FileNotFoundError:
        raise RuntimeError(
            "yt-dlp não foi encontrado.\n\n"
            "Instale com:\n"
            "pip install -U yt-dlp"
        )

    if result.returncode != 0:
        error = result.stderr.strip()

        raise RuntimeError(
            error or
            "Não foi possível acessar a playlist."
        )

    try:
        data = json.loads(
            result.stdout
        )

    except json.JSONDecodeError:
        raise RuntimeError(
            "O yt-dlp retornou dados inválidos."
        )

    entries = data.get(
        "entries",
        []
    )

    tracks = []

    for entry in entries:

        if not entry:
            continue

        video_id = entry.get("id")

        if not video_id:
            continue

        title = (
            entry.get("title")
            or
            "Unknown"
        )

        tracks.append({
            "id": video_id,
            "title": title,
            "url":
                f"https://www.youtube.com/watch?v={video_id}"
        })

    return tracks


def download_track(
    track,
    output_dir,
    browser,
    log_callback
):
    title = sanitize_filename(
        track["title"]
    )

    output_template = str(
        output_dir /
        f"{title} [%(id)s].%(ext)s"
    )

    command = [
        "yt-dlp",

        *yt_dlp_base_args(browser),

        # Garante que somente o vídeo individual seja baixado
        "--no-playlist",

        # Pega o melhor áudio disponível.
        # Se não houver áudio separado, tenta o melhor formato geral.
        "-f",
        "bestaudio/best",

        # Extrair/converter para MP3
        "--extract-audio",

        "--audio-format",
        "mp3",

        "--audio-quality",
        "0",

        "--newline",

        "-o",
        output_template,

        track["url"]
    ]

    log_callback(
        "Executando yt-dlp..."
    )

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )

    if process.stdout is not None:
        for line in process.stdout:
            line = line.rstrip()

            if line:
                log_callback(line)

    return process.wait() == 0


# ============================================================
# APLICAÇÃO
# ============================================================

class App:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "YouTube Music Sync"
        )

        self.root.geometry(
            "760x620"
        )

        self.root.minsize(
            680,
            540
        )

        self.library = load_library()

        self.build_ui()

        self.append_log(
            f"library.json: "
            f"{len(self.library)} músicas registradas."
        )

    # ========================================================
    # GUI
    # ========================================================

    def build_ui(self):

        main = ttk.Frame(
            self.root,
            padding=15
        )

        main.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            main,
            text="YouTube Music Sync",
            font=(
                "Segoe UI",
                20,
                "bold"
            )
        ).pack(
            anchor="w"
        )

        ttk.Label(
            main,
            text=(
                "Sincroniza somente músicas novas "
                "da playlist."
            )
        ).pack(
            anchor="w",
            pady=(0, 20)
        )

        # ----------------------------------------------------
        # PLAYLIST
        # ----------------------------------------------------

        ttk.Label(
            main,
            text="URL da playlist:"
        ).pack(
            anchor="w"
        )

        self.playlist_var = tk.StringVar()

        ttk.Entry(
            main,
            textvariable=self.playlist_var
        ).pack(
            fill="x",
            pady=(5, 15)
        )

        # ----------------------------------------------------
        # PASTA
        # ----------------------------------------------------

        ttk.Label(
            main,
            text="Biblioteca:"
        ).pack(
            anchor="w"
        )

        folder_frame = ttk.Frame(
            main
        )

        folder_frame.pack(
            fill="x",
            pady=(5, 15)
        )

        self.folder_var = tk.StringVar(
            value=str(
                DEFAULT_DOWNLOAD_DIR
            )
        )

        ttk.Entry(
            folder_frame,
            textvariable=self.folder_var
        ).pack(
            side="left",
            fill="x",
            expand=True
        )

        ttk.Button(
            folder_frame,
            text="Escolher",
            command=self.choose_folder
        ).pack(
            side="right",
            padx=(8, 0)
        )

        # ----------------------------------------------------
        # BROWSER
        # ----------------------------------------------------

        browser_frame = ttk.Frame(
            main
        )

        browser_frame.pack(
            fill="x",
            pady=(0, 15)
        )

        ttk.Label(
            browser_frame,
            text="Navegador:"
        ).pack(
            side="left"
        )

        self.browser_var = tk.StringVar(
            value=DEFAULT_BROWSER
        )

        ttk.Combobox(
            browser_frame,
            textvariable=self.browser_var,
            values=[
                "firefox",
                "chrome",
                "edge",
                "brave"
            ],
            state="readonly",
            width=12
        ).pack(
            side="left",
            padx=(8, 0)
        )

        # ----------------------------------------------------
        # BOTÃO
        # ----------------------------------------------------

        self.sync_button = ttk.Button(
            main,
            text="🔄 Sincronizar",
            command=self.start_sync
        )

        self.sync_button.pack(
            fill="x",
            pady=(0, 15)
        )

        # ----------------------------------------------------
        # STATS
        # ----------------------------------------------------

        stats = ttk.Frame(
            main
        )

        stats.pack(
            fill="x"
        )

        self.total_label = ttk.Label(
            stats,
            text="Playlist: 0"
        )

        self.total_label.pack(
            side="left",
            padx=(0, 20)
        )

        self.local_label = ttk.Label(
            stats,
            text="Já existentes: 0"
        )

        self.local_label.pack(
            side="left",
            padx=(0, 20)
        )

        self.new_label = ttk.Label(
            stats,
            text="Novas: 0"
        )

        self.new_label.pack(
            side="left"
        )

        # ----------------------------------------------------
        # PROGRESSO
        # ----------------------------------------------------

        self.progress = ttk.Progressbar(
            main,
            orient="horizontal",
            mode="determinate"
        )

        self.progress.pack(
            fill="x",
            pady=(15, 10)
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.status_var = tk.StringVar(
            value="Pronto."
        )

        ttk.Label(
            main,
            textvariable=self.status_var
        ).pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

        ttk.Label(
            main,
            text="Log:"
        ).pack(
            anchor="w",
            pady=(15, 5)
        )

        self.log_text = tk.Text(
            main,
            height=12,
            state="disabled",
            wrap="word"
        )

        self.log_text.pack(
            fill="both",
            expand=True
        )

    # ========================================================
    # GUI HELPERS
    # ========================================================

    def append_log(self, text):

        self.root.after(
            0,
            self._append_log,
            text
        )

    def _append_log(self, text):

        self.log_text.configure(
            state="normal"
        )

        self.log_text.insert(
            "end",
            text + "\n"
        )

        self.log_text.see(
            "end"
        )

        self.log_text.configure(
            state="disabled"
        )

    def set_status(self, text):

        self.root.after(
            0,
            self.status_var.set,
            text
        )

    def update_stats(
        self,
        total,
        existing,
        new
    ):

        def update():

            self.total_label.config(
                text=f"Playlist: {total}"
            )

            self.local_label.config(
                text=f"Já existentes: {existing}"
            )

            self.new_label.config(
                text=f"Novas: {new}"
            )

        self.root.after(
            0,
            update
        )

    def choose_folder(self):

        folder = filedialog.askdirectory()

        if folder:
            self.folder_var.set(
                folder
            )

    # ========================================================
    # INICIAR
    # ========================================================

    def start_sync(self):

        playlist_url = (
            self.playlist_var
            .get()
            .strip()
        )

        if not playlist_url:

            messagebox.showerror(
                "Erro",
                "Digite a URL da playlist."
            )

            return

        browser = (
            self.browser_var
            .get()
        )

        output_dir = Path(
            self.folder_var.get().strip()
        )

        if not str(output_dir).strip():

            messagebox.showerror(
                "Erro",
                "Escolha uma pasta para a biblioteca."
            )

            return

        self.sync_button.config(
            state="disabled"
        )

        threading.Thread(
            target=self.sync,
            args=(
                playlist_url,
                browser,
                output_dir
            ),
            daemon=True
        ).start()

    # ========================================================
    # SINCRONIZAÇÃO
    # ========================================================

    def sync(
        self,
        playlist_url,
        browser,
        output_dir
    ):

        try:

            # ------------------------------------------------
            # YT-DLP
            # ------------------------------------------------

            version = check_yt_dlp()

            if not version:

                raise RuntimeError(
                    "yt-dlp não encontrado.\n\n"
                    "Execute:\n"
                    "pip install -U yt-dlp"
                )

            self.append_log(
                f"yt-dlp {version}"
            )

            # ------------------------------------------------
            # PASTA
            # ------------------------------------------------

            output_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            self.append_log(
                f"Biblioteca: {output_dir}"
            )

            # ------------------------------------------------
            # INDEXAR ARQUIVOS EXISTENTES
            # ------------------------------------------------

            self.set_status(
                "Indexando músicas existentes..."
            )

            self.append_log(
                "Procurando músicas já baixadas..."
            )

            existing_files = scan_existing_files(
                output_dir
            )

            self.append_log(
                f"Encontrados "
                f"{len(existing_files)} arquivos de áudio."
            )

            # ------------------------------------------------
            # PLAYLIST
            # ------------------------------------------------

            self.set_status(
                "Lendo playlist..."
            )

            self.append_log(
                "Consultando playlist..."
            )

            tracks = get_playlist(
                playlist_url,
                browser
            )

            if not tracks:

                raise RuntimeError(
                    "Nenhuma música encontrada."
                )

            self.append_log(
                f"{len(tracks)} músicas na playlist."
            )

            # ------------------------------------------------
            # DETECTAR NOVAS
            # ------------------------------------------------

            new_tracks = []

            already_exists = 0

            for track in tracks:

                video_id = track["id"]

                title_key = normalize_name(
                    track["title"]
                )

                # --------------------------------------------
                # 1. Já está registrada pelo ID?
                # --------------------------------------------

                if video_id in self.library:

                    already_exists += 1

                    continue

                # --------------------------------------------
                # 2. Já existe pelo nome?
                # --------------------------------------------

                if title_key in existing_files:

                    self.library[video_id] = {
                        "id": video_id,
                        "title": track["title"],
                        "url": track["url"],
                        "source": "existing_file",
                        "file": str(
                            existing_files[title_key]
                        )
                    }

                    already_exists += 1

                    self.append_log(
                        f"✓ Já existe: "
                        f"{track['title']}"
                    )

                    continue

                # --------------------------------------------
                # 3. É nova
                # --------------------------------------------

                new_tracks.append(
                    track
                )

            # Salvar biblioteca
            save_library(
                self.library
            )

            self.update_stats(
                len(tracks),
                already_exists,
                len(new_tracks)
            )

            # ------------------------------------------------
            # NENHUMA NOVA
            # ------------------------------------------------

            if not new_tracks:

                self.set_status(
                    "Tudo sincronizado."
                )

                self.append_log(
                    "Nenhuma música nova encontrada."
                )

                return

            # ------------------------------------------------
            # DOWNLOAD
            # ------------------------------------------------

            total_new = len(
                new_tracks
            )

            self.root.after(
                0,
                lambda: self.progress.config(
                    maximum=total_new,
                    value=0
                )
            )

            downloaded_count = 0
            failed_count = 0

            for index, track in enumerate(
                new_tracks,
                start=1
            ):

                self.set_status(
                    f"Baixando "
                    f"{index}/{total_new}: "
                    f"{track['title']}"
                )

                self.append_log(
                    "----------------------------------"
                )

                self.append_log(
                    f"[{index}/{total_new}] "
                    f"{track['title']}"
                )

                success = download_track(
                    track,
                    output_dir,
                    browser,
                    self.append_log
                )

                if success:

                    downloaded_count += 1

                    # Localiza o arquivo criado
                    downloaded_file = None

                    safe_title = sanitize_filename(
                        track["title"]
                    )

                    expected_prefix = (
                        safe_title +
                        f" [{track['id']}]"
                    )

                    for file in output_dir.iterdir():

                        if not file.is_file():
                            continue

                        if file.suffix.lower() != ".mp3":
                            continue

                        if file.stem == expected_prefix:

                            downloaded_file = file
                            break

                    entry = {
                        "id": track["id"],
                        "title": track["title"],
                        "url": track["url"],
                        "source": "downloaded"
                    }

                    if downloaded_file:
                        entry["file"] = str(
                            downloaded_file
                        )

                    self.library[
                        track["id"]
                    ] = entry

                    save_library(
                        self.library
                    )

                    self.append_log(
                        "✓ Download concluído."
                    )

                else:

                    failed_count += 1

                    self.append_log(
                        "✗ Falha no download."
                    )

                self.root.after(
                    0,
                    lambda value=index:
                    self.progress.config(
                        value=value
                    )
                )

            # ------------------------------------------------
            # FIM
            # ------------------------------------------------

            self.set_status(
                "Sincronização concluída."
            )

            self.append_log(
                "=================================="
            )

            self.append_log(
                f"Baixadas: {downloaded_count}"
            )

            self.append_log(
                f"Falhas: {failed_count}"
            )

            self.append_log(
                f"Total processado: {total_new}"
            )

        except Exception as e:

            self.set_status(
                "Erro."
            )

            self.append_log(
                f"ERRO: {e}"
            )

            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Erro",
                    str(e)
                )
            )

        finally:

            self.root.after(
                0,
                lambda: self.sync_button.config(
                    state="normal"
                )
            )


# ============================================================
# MAIN
# ============================================================

def main():

    root = tk.Tk()

    try:

        style = ttk.Style()

        if "vista" in style.theme_names():

            style.theme_use(
                "vista"
            )

    except Exception:
        pass

    App(root)

    root.mainloop()


if __name__ == "__main__":
    main()