#!/usr/bin/env python3
# casiopea.py
#
# Cliente de linea de comandos para la wiki Casiopea de la e[ad] PUCV
# (https://wiki.ead.pucv.cl), implementada en Semantic MediaWiki.
#
# Se usa desde el skill `casiopea` del plugin casiopea-wiki, pero tambien
# puede invocarse a mano desde una terminal. Solo requiere Python 3 estandar;
# no usa dependencias externas para que el plugin sea portable.
#
# Subcomandos de lectura:
#   search <termino>           busqueda full-text
#   page <titulo>              wikitexto de una pagina
#   category <nombre>          paginas dentro de una categoria
#   backlinks <titulo>         paginas que enlazan a una pagina
#   transclusions <plantilla>  paginas que transcluyen una plantilla {{X}}
#   ask <query SMW>            query semantica, --format json|csv|table
#   browse <titulo>            propiedades semanticas de una pagina
#
# Subcomandos de escritura (requieren --confirm explicito):
#   edit <titulo>              reemplaza el contenido de una pagina
#   append <titulo>            anade texto al final de una pagina
#   create <titulo>            crea una pagina nueva (falla si existe)
#   upload <archivo>           sube un archivo (imagen, PDF, etc.)
#   delete <titulo>            borra una pagina (requiere grant Delete pages)
#
# Las credenciales se buscan en este orden:
#   1. Variables de entorno CASIOPEA_BOT_USER y CASIOPEA_BOT_PASS
#   2. Path indicado en CASIOPEA_CREDENTIALS
#   3. Carpeta `casiopea-bot` montada en el sandbox de Cowork
#      (/sessions/*/mnt/casiopea-bot/credentials, /mnt/casiopea-bot/credentials)
#   4. ~/.config/casiopea/credentials  (estandar XDG en host local)
#   5. ~/casiopea-bot/credentials      (convencion de carpeta dedicada)
# Si no se encuentra nada se aborta con un mensaje claro.

import argparse
import csv
import glob
import io
import json
import mimetypes
import os
import sys
import urllib.parse
import urllib.request
import uuid
from http.cookiejar import CookieJar
from typing import Any

# URL del endpoint MediaWiki API de Casiopea. Sobreescribible con la variable
# de entorno CASIOPEA_API_URL para apuntar a un mirror o a una instancia de test.
DEFAULT_API_URL = "https://wiki.ead.pucv.cl/api.php"


# -----------------------------------------------------------------------------
# Carga de credenciales
# -----------------------------------------------------------------------------

def load_credentials() -> tuple[str, str, str]:
    """
    Devuelve (api_url, bot_user, bot_pass).

    Se llama desde main() antes de cualquier operacion. El orden de busqueda
    permite usar el mismo plugin desde el sandbox de Cowork (donde solo se ven
    las carpetas montadas) o desde una shell local del Mac/Linux.
    """
    api_url = os.environ.get("CASIOPEA_API_URL", DEFAULT_API_URL)
    user = os.environ.get("CASIOPEA_BOT_USER")
    password = os.environ.get("CASIOPEA_BOT_PASS")

    if not (user and password):
        for cred_path in _candidate_credential_paths():
            if cred_path and os.path.isfile(cred_path):
                file_user, file_pass, file_api = _read_credentials_file(cred_path)
                user = user or file_user
                password = password or file_pass
                if file_api and api_url == DEFAULT_API_URL:
                    api_url = file_api
                if user and password:
                    break

    if not (user and password):
        sys.stderr.write(
            "ERROR: faltan credenciales de Casiopea.\n\n"
            "Define CASIOPEA_BOT_USER y CASIOPEA_BOT_PASS como variables de\n"
            "entorno, o crea un archivo en una de estas rutas:\n"
            "  ~/Sites/casiopea-skill/credentials\n"
            "  ~/.config/casiopea/credentials\n"
            "  ~/casiopea-bot/credentials\n"
            "  (o monta una carpeta cuyo nombre contenga 'casiopea' en el sandbox de Cowork)\n\n"
            "Con este contenido y permisos 600:\n\n"
            "  CASIOPEA_BOT_USER=Usuario@NombreBot\n"
            "  CASIOPEA_BOT_PASS=la-contrasena-larga-de-bot-password\n\n"
            "Las credenciales se generan en https://wiki.ead.pucv.cl/Special:BotPasswords\n"
        )
        sys.exit(2)

    return api_url, user, password


def _candidate_credential_paths() -> list[str]:
    """
    Lista ordenada de paths donde buscar el archivo de credenciales.

    Se llama desde load_credentials(). Incluye la opcion explicita
    CASIOPEA_CREDENTIALS, los mounts tipicos de Cowork y los paths estandar
    de host local.
    """
    paths: list[str] = []
    explicit = os.environ.get("CASIOPEA_CREDENTIALS")
    if explicit:
        paths.append(explicit)

    # En el sandbox de Cowork, cualquier carpeta que el usuario haya montado
    # con un nombre que contenga "casiopea" se considera candidata. Asi funciona
    # tanto si la carpeta dedicada se llama casiopea-skill, casiopea-bot o
    # casiopea-creds, sin tener que actualizar el script por cada convencion.
    for mnt in glob.glob("/sessions/*/mnt/*casiopea*/credentials"):
        paths.append(mnt)
    for mnt in glob.glob("/mnt/*casiopea*/credentials"):
        paths.append(mnt)

    # Paths estandar de host local (cuando el script corre fuera del sandbox).
    paths.append(os.path.expanduser("~/.config/casiopea/credentials"))
    paths.append(os.path.expanduser("~/casiopea-bot/credentials"))
    paths.append(os.path.expanduser("~/Sites/casiopea-skill/credentials"))
    return paths


def _read_credentials_file(path: str) -> tuple[str | None, str | None, str | None]:
    """
    Parsea un archivo formato KEY=VALUE y devuelve (user, pass, api_url).

    Se llama desde load_credentials() por cada path candidato. Las claves
    permitidas son CASIOPEA_BOT_USER, CASIOPEA_BOT_PASS y CASIOPEA_API_URL.
    Lineas vacias y comentarios (#) se ignoran.
    """
    user = pwd = api = None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key == "CASIOPEA_BOT_USER":
                    user = value
                elif key == "CASIOPEA_BOT_PASS":
                    pwd = value
                elif key == "CASIOPEA_API_URL":
                    api = value
    except OSError:
        return None, None, None
    return user, pwd, api


# -----------------------------------------------------------------------------
# Cliente HTTP minimal con cookies y tokens
# -----------------------------------------------------------------------------

class CasiopeaClient:
    """
    Cliente para la API de Casiopea con manejo de sesion via cookies.

    Se usa desde cada subcomando: primero login(), luego query(action=...).
    Mantiene un CookieJar para reutilizar la sesion entre llamadas, y cachea
    el CSRF token para evitar pedirlo en cada operacion de escritura.
    """

    def __init__(self, api_url: str, user: str, password: str):
        self.api_url = api_url
        self.user = user
        self.password = password
        self.cookies = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies)
        )
        self.opener.addheaders = [
            ("User-Agent", "casiopea-wiki-plugin/0.1 (Cowork plugin; +contact ead.pucv.cl)")
        ]
        self._csrf_token: str | None = None

    def _request(self, params: dict[str, str], method: str = "GET",
                 multipart: dict | None = None) -> dict[str, Any]:
        """
        Llama a api.php y devuelve el JSON parseado.

        Se usa en login() y en cada subcomando. El parametro `format=json`
        se inyecta automaticamente. Si se pasa `multipart`, se construye un
        cuerpo multipart/form-data (necesario para upload de archivos).
        """
        params = dict(params)
        params.setdefault("format", "json")
        params.setdefault("formatversion", "2")

        if multipart:
            boundary = uuid.uuid4().hex
            body = _build_multipart(params, multipart, boundary)
            req = urllib.request.Request(self.api_url, data=body, method="POST")
            req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        elif method == "GET":
            url = self.api_url + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url)
        else:
            data = urllib.parse.urlencode(params).encode("utf-8")
            req = urllib.request.Request(self.api_url, data=data, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")

        with self.opener.open(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"Respuesta no JSON: {body[:300]}\n")
            raise SystemExit(3) from exc

    def login(self) -> None:
        """
        Login en dos pasos como exige la action API de MediaWiki.

        1. action=query&meta=tokens&type=login -> logintoken
        2. action=login con ese token, lgname y lgpassword

        Se usa una sola vez al inicio de cada invocacion del CLI; las cookies
        de sesion luego viajan automaticamente en cada request.
        """
        token_resp = self._request({
            "action": "query",
            "meta": "tokens",
            "type": "login",
        })
        token = token_resp["query"]["tokens"]["logintoken"]

        login_resp = self._request({
            "action": "login",
            "lgname": self.user,
            "lgpassword": self.password,
            "lgtoken": token,
        }, method="POST")

        result = login_resp.get("login", {}).get("result")
        if result != "Success":
            reason = login_resp.get("login", {}).get("reason", "(sin detalle)")
            sys.stderr.write(
                f"ERROR de login en Casiopea: {result}. {reason}\n"
                "Verifica el formato Usuario@NombreBot y la contrasena de bot.\n"
            )
            sys.exit(4)

    def csrf_token(self) -> str:
        """Obtiene y cachea el CSRF token necesario para escribir."""
        if self._csrf_token is None:
            resp = self._request({"action": "query", "meta": "tokens", "type": "csrf"})
            self._csrf_token = resp["query"]["tokens"]["csrftoken"]
        return self._csrf_token

    # -------------------------------------------------------------------------
    # Operaciones de lectura
    # -------------------------------------------------------------------------

    def search(self, term: str, limit: int = 20) -> list[dict[str, Any]]:
        """Busqueda full-text estandar de MediaWiki (action=query&list=search)."""
        resp = self._request({
            "action": "query",
            "list": "search",
            "srsearch": term,
            "srlimit": str(limit),
        })
        return resp.get("query", {}).get("search", [])

    def page(self, title: str) -> str:
        """Devuelve el wikitexto crudo de la pagina (action=query&prop=revisions)."""
        resp = self._request({
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvprop": "content",
            "rvslots": "main",
        })
        pages = resp.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            return ""
        revs = pages[0].get("revisions", [])
        if not revs:
            return ""
        return revs[0].get("slots", {}).get("main", {}).get("content", "")

    def category(self, name: str, limit: int = 100) -> list[str]:
        """Lista paginas de una categoria (action=query&list=categorymembers)."""
        prefix = name.split(":", 1)[0].lower()
        if prefix in ("category", "categoria"):
            cmtitle = name
        else:
            cmtitle = "Category:" + name
        resp = self._request({
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cmtitle,
            "cmlimit": str(limit),
        })
        return [m["title"] for m in resp.get("query", {}).get("categorymembers", [])]

    def backlinks(self, title: str, limit: int = 100) -> list[str]:
        """Lista paginas que enlazan a la pagina dada (action=query&list=backlinks)."""
        resp = self._request({
            "action": "query",
            "list": "backlinks",
            "bltitle": title,
            "bllimit": str(limit),
        })
        return [b["title"] for b in resp.get("query", {}).get("backlinks", [])]

    def transclusions(self, template_title: str, limit: int = 500) -> list[str]:
        """
        Lista paginas que transcluyen una plantilla (action=query&list=embeddedin).

        Distinto de backlinks: encuentra usos de {{Plantilla:X}}, no enlaces [[X]].
        Imprescindible antes de borrar o renombrar una plantilla, para detectar
        impacto. Pagina automaticamente sobre todos los resultados.
        """
        out = []
        cont = None
        while True:
            params = {
                "action": "query",
                "list": "embeddedin",
                "eititle": template_title,
                "eilimit": str(limit),
            }
            if cont: params["eicontinue"] = cont
            resp = self._request(params)
            out.extend(p["title"] for p in resp.get("query", {}).get("embeddedin", []))
            if "continue" in resp: cont = resp["continue"]["eicontinue"]
            else: break
        return out

    def ask(self, query: str) -> dict[str, Any]:
        """
        Ejecuta una query Semantic MediaWiki (action=ask).

        Sintaxis SMW estandar, por ejemplo:
            [[Category:Travesia]][[Tiene destino::Patagonia]]|?Tiene ano|?Tiene destino

        Se devuelve el dict completo con `results` y `printrequests` para que el
        formateador (json/csv/table) emita lo que corresponda.
        """
        resp = self._request({
            "action": "ask",
            "query": query,
        })
        return resp.get("query", {})

    def browse(self, title: str) -> dict[str, Any]:
        """
        Devuelve las propiedades SMW de una pagina (action=browsebysubject).

        Util para descubrir que datos estructurados existen en una pagina antes
        de armar una query con #ask.
        """
        resp = self._request({
            "action": "browsebysubject",
            "subject": title,
        })
        return resp.get("query", {})

    # -------------------------------------------------------------------------
    # Operaciones de escritura (requieren CSRF token)
    # -------------------------------------------------------------------------

    def edit(self, title: str, text: str | None = None,
             appendtext: str | None = None, prependtext: str | None = None,
             section: str | None = None, summary: str = "",
             createonly: bool = False) -> dict[str, Any]:
        """
        Crea o modifica una pagina (action=edit).

        Modos mutuamente excluyentes:
          - text: reemplaza el contenido completo
          - appendtext: anade al final
          - prependtext: anade al principio
          - section: si se da, limita la operacion a una seccion
          - createonly: falla si la pagina ya existe (modo create)

        El bot flag se manda en True para que el log de cambios marque la
        edicion como hecha por bot, distinguible en RecentChanges.
        """
        params: dict[str, str] = {
            "action": "edit",
            "title": title,
            "summary": summary,
            "token": self.csrf_token(),
            "bot": "1",
        }
        if text is not None:
            params["text"] = text
        elif appendtext is not None:
            params["appendtext"] = appendtext
        elif prependtext is not None:
            params["prependtext"] = prependtext
        else:
            raise ValueError("edit requiere text, appendtext o prependtext")
        if section is not None:
            params["section"] = section
        if createonly:
            params["createonly"] = "1"
        resp = self._request(params, method="POST")
        if "error" in resp:
            sys.stderr.write(f"ERROR en edit: {resp['error']}\n")
            sys.exit(5)
        return resp.get("edit", {})

    def delete(self, title: str, reason: str = "") -> dict[str, Any]:
        """
        Borra una pagina (action=delete).

        Requiere que el bot tenga el grant `Delete pages` en su Bot Password.
        El borrado en MediaWiki es reversible por un sysop via Special:Undelete,
        pero para el bot no lo es. Usar con cuidado.
        """
        params = {
            "action": "delete",
            "title": title,
            "reason": reason or "Borrado via casiopea-wiki bot",
            "token": self.csrf_token(),
        }
        resp = self._request(params, method="POST")
        if "error" in resp:
            sys.stderr.write(f"ERROR en delete: {resp['error']}\n")
            sys.exit(5)
        return resp.get("delete", {})

    def upload(self, filepath: str, filename: str | None = None,
               comment: str = "", text: str | None = None,
               ignorewarnings: bool = False) -> dict[str, Any]:
        """
        Sube un archivo (action=upload) usando multipart/form-data.

        Se usa para imagenes, PDFs, etc. Si `filename` no se da, se usa el
        basename del path. `text` es el wikitexto inicial de la pagina File:.
        """
        if not os.path.isfile(filepath):
            sys.stderr.write(f"Archivo no existe: {filepath}\n")
            sys.exit(1)
        target = filename or os.path.basename(filepath)
        params = {
            "action": "upload",
            "filename": target,
            "comment": comment,
            "token": self.csrf_token(),
        }
        if text is not None:
            params["text"] = text
        if ignorewarnings:
            params["ignorewarnings"] = "1"

        with open(filepath, "rb") as fh:
            content = fh.read()
        mime = mimetypes.guess_type(target)[0] or "application/octet-stream"
        multipart = {"file": (target, content, mime)}
        resp = self._request(params, method="POST", multipart=multipart)
        if "error" in resp:
            sys.stderr.write(f"ERROR en upload: {resp['error']}\n")
            sys.exit(5)
        return resp.get("upload", {})


# -----------------------------------------------------------------------------
# Multipart helper para upload
# -----------------------------------------------------------------------------

def _build_multipart(fields: dict[str, str], files: dict, boundary: str) -> bytes:
    """
    Construye un cuerpo multipart/form-data manualmente.

    Se usa solo para upload de archivos. No depende de requests para mantener
    el plugin sin dependencias externas. `files` es {field: (filename, bytes, mime)}.
    """
    lines: list[bytes] = []
    b = boundary.encode("ascii")
    for key, value in fields.items():
        lines.append(b"--" + b)
        lines.append(f'Content-Disposition: form-data; name="{key}"'.encode("utf-8"))
        lines.append(b"")
        lines.append(str(value).encode("utf-8"))
    for field_name, (filename, content, mime) in files.items():
        lines.append(b"--" + b)
        lines.append(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"'.encode("utf-8")
        )
        lines.append(f"Content-Type: {mime}".encode("utf-8"))
        lines.append(b"")
        lines.append(content)
    lines.append(b"--" + b + b"--")
    lines.append(b"")
    return b"\r\n".join(lines)


# -----------------------------------------------------------------------------
# Formateadores de salida
# -----------------------------------------------------------------------------

def format_ask_results(ask_data: dict[str, Any], fmt: str) -> str:
    """
    Convierte el resultado de action=ask al formato pedido.

    Se llama desde el subcomando `ask` cuando se especifica --format. CSV y
    table aplanan los printouts en columnas; json emite tal cual lo devuelve
    SMW para usuarios avanzados.
    """
    results = ask_data.get("results", {}) or {}
    printouts_meta = ask_data.get("printrequests", []) or []
    columns = [pr.get("label") for pr in printouts_meta if pr.get("label")]

    if fmt == "json":
        return json.dumps(ask_data, indent=2, ensure_ascii=False)

    rows = []
    for page_title, page_data in results.items():
        row = {"Pagina": page_title}
        printouts = page_data.get("printouts", {}) or {}
        for col in columns:
            values = printouts.get(col, [])
            row[col] = "; ".join(_smw_value(v) for v in values)
        rows.append(row)

    fieldnames = ["Pagina"] + columns

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()

    if fmt == "table":
        widths = {f: max(len(f), max((len(str(r.get(f, ""))) for r in rows), default=0)) for f in fieldnames}
        lines = ["  ".join(f.ljust(widths[f]) for f in fieldnames),
                 "  ".join("-" * widths[f] for f in fieldnames)]
        for r in rows:
            lines.append("  ".join(str(r.get(f, "")).ljust(widths[f]) for f in fieldnames))
        return "\n".join(lines)

    raise ValueError(f"Formato desconocido: {fmt}")


def _smw_value(value: Any) -> str:
    """Aplana un valor SMW (string, dict con fulltext, numero, etc.) a string."""
    if isinstance(value, dict):
        return value.get("fulltext") or value.get("displaytitle") or json.dumps(value, ensure_ascii=False)
    return str(value)


# -----------------------------------------------------------------------------
# Salvaguarda para escrituras
# -----------------------------------------------------------------------------

def require_confirmation(title: str, action_desc: str, confirm: bool) -> None:
    """
    Imprime un dry-run y aborta si --confirm no se paso.

    Se llama al inicio de cada subcomando de escritura. Asi se garantiza que
    una invocacion casual del CLI nunca modifique la wiki sin que el operador
    haya visto exactamente que se va a hacer.
    """
    if confirm:
        return
    sys.stderr.write(
        "[DRY RUN] No se ejecuto ningun cambio.\n"
        f"  Pagina: {title}\n"
        f"  Operacion: {action_desc}\n"
        "Para ejecutar realmente esta operacion, vuelve a invocar el comando con --confirm.\n"
    )
    sys.exit(0)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Define los subcomandos del CLI. Cada uno mapea 1:1 a un metodo del cliente."""
    parser = argparse.ArgumentParser(
        prog="casiopea",
        description="Cliente para la wiki Casiopea de la e[ad] PUCV (Semantic MediaWiki).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ---- Lectura ----
    p_search = sub.add_parser("search", help="Busqueda full-text")
    p_search.add_argument("term")
    p_search.add_argument("--limit", type=int, default=20)

    p_page = sub.add_parser("page", help="Wikitexto de una pagina")
    p_page.add_argument("title")

    p_cat = sub.add_parser("category", help="Paginas de una categoria")
    p_cat.add_argument("name")
    p_cat.add_argument("--limit", type=int, default=100)

    p_back = sub.add_parser("backlinks", help="Paginas que enlazan a una pagina")
    p_back.add_argument("title")
    p_back.add_argument("--limit", type=int, default=100)

    p_trans = sub.add_parser("transclusions", help="Paginas que transcluyen una plantilla")
    p_trans.add_argument("template", help="Titulo completo, ej: Plantilla:Mis Cursos2")
    p_trans.add_argument("--limit", type=int, default=500)

    p_ask = sub.add_parser("ask", help="Query Semantic MediaWiki")
    p_ask.add_argument("query", help="Sintaxis SMW: [[Category:X]][[Prop::Val]]|?Prop1|?Prop2")
    p_ask.add_argument("--format", choices=["json", "csv", "table"], default="table")

    p_browse = sub.add_parser("browse", help="Propiedades semanticas de una pagina")
    p_browse.add_argument("title")

    # ---- Escritura ----
    def add_write_args(p):
        p.add_argument("--summary", default="Edit via casiopea-wiki bot")
        p.add_argument("--confirm", action="store_true",
                       help="Sin esta flag, el comando solo imprime un dry-run.")
        p.add_argument("--from-file", help="Leer el contenido desde un archivo en vez de stdin.")

    p_edit = sub.add_parser("edit", help="Reemplaza el contenido de una pagina")
    p_edit.add_argument("title")
    p_edit.add_argument("--section", help="Limitar la operacion a una seccion")
    add_write_args(p_edit)

    p_append = sub.add_parser("append", help="Anade texto al final de una pagina")
    p_append.add_argument("title")
    add_write_args(p_append)

    p_create = sub.add_parser("create", help="Crea una pagina nueva (falla si existe)")
    p_create.add_argument("title")
    add_write_args(p_create)

    p_del = sub.add_parser("delete", help="Borra una pagina (requiere grant Delete pages)")
    p_del.add_argument("title")
    p_del.add_argument("--reason", default="Borrado via casiopea-wiki bot")
    p_del.add_argument("--confirm", action="store_true")

    p_up = sub.add_parser("upload", help="Sube un archivo (imagen, PDF, etc.)")
    p_up.add_argument("filepath")
    p_up.add_argument("--as", dest="as_name", help="Nombre de archivo en la wiki")
    p_up.add_argument("--comment", default="Upload via casiopea-wiki bot")
    p_up.add_argument("--text", help="Wikitexto inicial de la pagina File:")
    p_up.add_argument("--ignorewarnings", action="store_true")
    p_up.add_argument("--confirm", action="store_true")

    return parser


def _read_text_input(args) -> str:
    """Lee el contenido a escribir desde --from-file o desde stdin."""
    if args.from_file:
        with open(args.from_file, "r", encoding="utf-8") as fh:
            return fh.read()
    return sys.stdin.read()


def main() -> None:
    """Punto de entrada del CLI. Carga credenciales, hace login y despacha al subcomando."""
    args = build_parser().parse_args()
    api_url, user, password = load_credentials()
    client = CasiopeaClient(api_url, user, password)
    client.login()

    # ---- Lectura ----
    if args.cmd == "search":
        results = client.search(args.term, limit=args.limit)
        for r in results:
            print(f"{r['title']}\n  {r.get('snippet', '').strip()}\n")

    elif args.cmd == "page":
        text = client.page(args.title)
        if not text:
            sys.stderr.write(f"Pagina no encontrada o vacia: {args.title}\n")
            sys.exit(1)
        sys.stdout.write(text)

    elif args.cmd == "category":
        for title in client.category(args.name, limit=args.limit):
            print(title)

    elif args.cmd == "backlinks":
        for title in client.backlinks(args.title, limit=args.limit):
            print(title)

    elif args.cmd == "transclusions":
        for title in client.transclusions(args.template, limit=args.limit):
            print(title)

    elif args.cmd == "ask":
        data = client.ask(args.query)
        sys.stdout.write(format_ask_results(data, args.format))
        if args.format != "json":
            sys.stdout.write("\n")

    elif args.cmd == "browse":
        data = client.browse(args.title)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    # ---- Escritura ----
    elif args.cmd == "edit":
        body = _read_text_input(args)
        require_confirmation(args.title, f"reemplazar contenido ({len(body)} chars)", args.confirm)
        result = client.edit(args.title, text=body, section=args.section, summary=args.summary)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "append":
        body = _read_text_input(args)
        require_confirmation(args.title, f"anadir {len(body)} chars al final", args.confirm)
        result = client.edit(args.title, appendtext=body, summary=args.summary)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "create":
        body = _read_text_input(args)
        require_confirmation(args.title, f"crear pagina nueva ({len(body)} chars)", args.confirm)
        result = client.edit(args.title, text=body, summary=args.summary, createonly=True)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "delete":
        require_confirmation(args.title, f"borrar pagina (motivo: {args.reason})", args.confirm)
        result = client.delete(args.title, reason=args.reason)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "upload":
        target = args.as_name or os.path.basename(args.filepath)
        require_confirmation(target, f"subir archivo {args.filepath}", args.confirm)
        result = client.upload(args.filepath, filename=args.as_name,
                               comment=args.comment, text=args.text,
                               ignorewarnings=args.ignorewarnings)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
