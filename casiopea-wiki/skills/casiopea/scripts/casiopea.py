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
#   search <termino>           busqueda full-text (pagina hasta --limit)
#   page <titulo>              wikitexto de una pagina
#   category <nombre>          paginas dentro de una categoria (paginado)
#   backlinks <titulo>         paginas que enlazan a una pagina (paginado)
#   transclusions <plantilla>  paginas que transcluyen una plantilla {{X}}
#   fileusage <archivo>        paginas que usan un archivo File:X
#   history <titulo>           historial de revisiones de una pagina
#   recentchanges              cambios recientes de la wiki
#   ask <query SMW>            query semantica, --format json|csv|table
#   browse <titulo>            propiedades semanticas de una pagina
#
# Subcomandos de escritura (requieren --confirm explicito; dry-run con diff):
#   edit <titulo>              reemplaza el contenido de una pagina
#   append <titulo>            anade texto al final de una pagina
#   create <titulo>            crea una pagina nueva (falla si existe)
#   move <origen>              renombra/mueve una pagina (con redirect)
#   upload <archivo>           sube un archivo (chunked si es grande)
#   delete <titulo>            borra una pagina (requiere grant Delete pages)
#
# Las credenciales se buscan en este orden:
#   1. Variables de entorno CASIOPEA_BOT_USER y CASIOPEA_BOT_PASS
#   2. Path indicado en CASIOPEA_CREDENTIALS
#   3. Carpeta cuyo nombre contenga "casiopea" montada en el sandbox
#      (/sessions/*/mnt/*casiopea*/credentials, /mnt/*casiopea*/credentials)
#   4. ~/.config/casiopea/credentials  (estandar XDG en host local)
#   5. ~/casiopea-bot/credentials      (convencion de carpeta dedicada)
#   6. ~/Sites/casiopea-skill/credentials
# Si no se encuentra nada se aborta con un mensaje claro.
#
# Cortesia de bot: todas las llamadas mandan maxlag=5 y assert=user (salvo el
# bootstrap de login). Ante maxlag/ratelimited/HTTP 429/503 se reintenta con
# backoff. Ante badtoken en una escritura se refresca el CSRF token y se
# reintenta una vez.

import argparse
import csv
import difflib
import glob
import io
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.cookiejar import CookieJar
from typing import Any

# URL del endpoint MediaWiki API de Casiopea. Sobreescribible con la variable
# de entorno CASIOPEA_API_URL para apuntar a un mirror o a una instancia de test.
DEFAULT_API_URL = "https://wiki.ead.pucv.cl/api.php"

# Cortesia de bot. maxlag detiene al bot si la replica de BD esta retrasada.
MAXLAG_SECONDS = 5
MAX_RETRIES = 4
RETRY_BASE_DELAY = 2.0  # segundos; backoff exponencial RETRY_BASE_DELAY * 2**n

# Tamano de chunk para subidas grandes (4 MiB). Sobre este umbral de archivo
# total se usa el protocolo de upload chunked de MediaWiki.
CHUNK_SIZE = 4 * 1024 * 1024
CHUNKED_UPLOAD_THRESHOLD = 8 * 1024 * 1024


# -----------------------------------------------------------------------------
# Carga de credenciales
# -----------------------------------------------------------------------------

def load_credentials() -> tuple[str, str, str]:
    """
    Devuelve (api_url, bot_user, bot_pass).

    Se llama desde main() antes de cualquier operacion. El orden de busqueda
    permite usar el mismo plugin desde el sandbox (donde solo se ven las
    carpetas montadas) o desde una shell local del Mac/Linux.
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
            "  (o monta una carpeta cuyo nombre contenga 'casiopea' en el sandbox)\n\n"
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
    CASIOPEA_CREDENTIALS, los mounts tipicos del sandbox y los paths estandar
    de host local.
    """
    paths: list[str] = []
    explicit = os.environ.get("CASIOPEA_CREDENTIALS")
    if explicit:
        paths.append(explicit)

    # En el sandbox, cualquier carpeta que el usuario haya montado con un
    # nombre que contenga "casiopea" se considera candidata. Asi funciona
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
# Cliente HTTP minimal con cookies, tokens, maxlag y reintentos
# -----------------------------------------------------------------------------

class CasiopeaClient:
    """
    Cliente para la API de Casiopea con manejo de sesion via cookies.

    Se usa desde cada subcomando: primero login(), luego query(action=...).
    Mantiene un CookieJar para reutilizar la sesion entre llamadas, cachea el
    CSRF token, y aplica cortesia de bot (maxlag/assert) con reintentos ante
    lag de replica o rate limiting.
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
            ("User-Agent", "casiopea-wiki-plugin/0.3 (Claude Code plugin; +contact ead.pucv.cl)")
        ]
        self._csrf_token: str | None = None

    def _request(self, params: dict[str, str], method: str = "GET",
                 multipart: dict | None = None, authed: bool = True) -> dict[str, Any]:
        """
        Llama a api.php y devuelve el JSON parseado.

        Se usa en login() y en cada subcomando. Inyecta format=json,
        formatversion=2 y maxlag automaticamente; con authed=True agrega
        assert=user para que una sesion caida falle ruidosamente en vez de
        escribir como anonimo. Reintenta con backoff ante maxlag/ratelimited
        y HTTP 429/503. authed=False solo en el bootstrap de login (donde
        todavia no hay sesion que afirmar).
        """
        base = dict(params)
        base.setdefault("format", "json")
        base.setdefault("formatversion", "2")
        base["maxlag"] = str(MAXLAG_SECONDS)
        if authed:
            base.setdefault("assert", "user")

        attempt = 0
        while True:
            attempt += 1
            try:
                data = self._do_request(base, method, multipart)
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 503) and attempt <= MAX_RETRIES:
                    self._sleep_retry(exc.headers.get("Retry-After"), attempt,
                                      f"HTTP {exc.code}")
                    continue
                sys.stderr.write(f"ERROR HTTP {exc.code} desde la API: {exc.reason}\n")
                raise SystemExit(3) from exc
            except urllib.error.URLError as exc:
                if attempt <= MAX_RETRIES:
                    self._sleep_retry(None, attempt, f"red ({exc.reason})")
                    continue
                sys.stderr.write(f"ERROR de red contra la API: {exc.reason}\n")
                raise SystemExit(3) from exc

            err = data.get("error", {})
            code = err.get("code")
            if code in ("maxlag", "ratelimited", "readonly") and attempt <= MAX_RETRIES:
                self._sleep_retry(data.get("retry-after") or err.get("info"),
                                  attempt, code)
                continue
            return data

    def _do_request(self, params: dict[str, str], method: str,
                     multipart: dict | None) -> dict[str, Any]:
        """Una sola llamada HTTP. Construye el request segun GET/POST/multipart."""
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
            raw = resp.read().decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"Respuesta no JSON: {raw[:300]}\n")
            raise SystemExit(3) from exc

    def _sleep_retry(self, hint: Any, attempt: int, why: str) -> None:
        """Backoff exponencial entre reintentos. Avisa por stderr (no stdout)."""
        delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
        try:
            if hint is not None:
                delay = max(delay, float(str(hint).split()[0]))
        except (ValueError, IndexError):
            pass
        sys.stderr.write(
            f"[reintento {attempt}/{MAX_RETRIES}] {why}; esperando {delay:.0f}s...\n"
        )
        time.sleep(delay)

    def login(self) -> None:
        """
        Login en dos pasos como exige la action API de MediaWiki.

        1. action=query&meta=tokens&type=login -> logintoken
        2. action=login con ese token, lgname y lgpassword

        Ambas llamadas van con authed=False: todavia no hay sesion que
        afirmar. Las cookies de sesion luego viajan automaticamente.
        """
        token_resp = self._request({
            "action": "query",
            "meta": "tokens",
            "type": "login",
        }, authed=False)
        token = token_resp["query"]["tokens"]["logintoken"]

        login_resp = self._request({
            "action": "login",
            "lgname": self.user,
            "lgpassword": self.password,
            "lgtoken": token,
        }, method="POST", authed=False)

        result = login_resp.get("login", {}).get("result")
        if result != "Success":
            reason = login_resp.get("login", {}).get("reason", "(sin detalle)")
            sys.stderr.write(
                f"ERROR de login en Casiopea: {result}. {reason}\n"
                "Verifica el formato Usuario@NombreBot y la contrasena de bot.\n"
                "Las credenciales se generan en https://wiki.ead.pucv.cl/Special:BotPasswords\n"
            )
            sys.exit(4)

    def csrf_token(self, force_refresh: bool = False) -> str:
        """Obtiene y cachea el CSRF token necesario para escribir."""
        if self._csrf_token is None or force_refresh:
            resp = self._request({"action": "query", "meta": "tokens", "type": "csrf"})
            self._csrf_token = resp["query"]["tokens"]["csrftoken"]
        return self._csrf_token

    # -------------------------------------------------------------------------
    # Paginacion generica
    # -------------------------------------------------------------------------

    def _paginate(self, params: dict[str, str], result_key: str,
                   limit: int) -> list[dict[str, Any]]:
        """
        Itera la continuacion estandar de MediaWiki hasta juntar `limit`
        resultados o agotar la lista.

        Se usa desde search/category/backlinks/transclusions/recentchanges/
        fileusage. El truco robusto es reenviar tal cual el objeto `continue`
        que devuelve la API (sus claves cambian por modulo: sroffset,
        cmcontinue, blcontinue, eicontinue, rccontinue, iucontinue...).
        """
        out: list[dict[str, Any]] = []
        params = dict(params)
        while len(out) < limit:
            resp = self._request(params)
            items = resp.get("query", {}).get(result_key, []) or []
            out.extend(items)
            cont = resp.get("continue")
            if not cont:
                break
            params.update(cont)
        return out[:limit]

    # -------------------------------------------------------------------------
    # Operaciones de lectura
    # -------------------------------------------------------------------------

    def search(self, term: str, limit: int = 20) -> list[dict[str, Any]]:
        """Busqueda full-text (list=search), paginada hasta `limit`."""
        page = min(limit, 50)
        return self._paginate({
            "action": "query",
            "list": "search",
            "srsearch": term,
            "srlimit": str(page),
        }, "search", limit)

    def page(self, title: str) -> str:
        """Devuelve el wikitexto crudo de la pagina (prop=revisions)."""
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
        """Lista paginas de una categoria (list=categorymembers), paginada."""
        prefix = name.split(":", 1)[0].lower()
        if prefix in ("category", "categoria"):
            cmtitle = name
        else:
            cmtitle = "Category:" + name
        items = self._paginate({
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cmtitle,
            "cmlimit": str(min(limit, 500)),
        }, "categorymembers", limit)
        return [m["title"] for m in items]

    def backlinks(self, title: str, limit: int = 100) -> list[str]:
        """Lista paginas que enlazan a la pagina dada (list=backlinks)."""
        items = self._paginate({
            "action": "query",
            "list": "backlinks",
            "bltitle": title,
            "bllimit": str(min(limit, 500)),
        }, "backlinks", limit)
        return [b["title"] for b in items]

    def transclusions(self, template_title: str, limit: int = 500) -> list[str]:
        """
        Lista paginas que transcluyen una plantilla (list=embeddedin).

        Distinto de backlinks: encuentra usos de {{Plantilla:X}}, no enlaces
        [[X]]. Imprescindible antes de borrar o renombrar una plantilla, para
        detectar impacto. Si devuelve 0 resultados, la plantilla es segura.
        """
        items = self._paginate({
            "action": "query",
            "list": "embeddedin",
            "eititle": template_title,
            "eilimit": str(min(limit, 500)),
        }, "embeddedin", limit)
        return [p["title"] for p in items]

    def fileusage(self, filename: str, limit: int = 500) -> list[str]:
        """
        Lista paginas que usan un archivo (list=imageusage).

        Acepta el nombre con o sin prefijo File:/Archivo:. Imprescindible
        antes de borrar o renombrar un archivo: dice que paginas se romperian.
        """
        prefix = filename.split(":", 1)[0].lower()
        if prefix in ("file", "archivo", "imagen"):
            iutitle = filename
        else:
            iutitle = "File:" + filename
        items = self._paginate({
            "action": "query",
            "list": "imageusage",
            "iutitle": iutitle,
            "iulimit": str(min(limit, 500)),
        }, "imageusage", limit)
        return [p["title"] for p in items]

    def history(self, title: str, limit: int = 20) -> list[dict[str, Any]]:
        """
        Historial de revisiones de una pagina (prop=revisions).

        Devuelve revid, timestamp, user, size y comment de cada revision,
        de la mas nueva a la mas vieja. Util para auditar quien edito que.
        """
        resp = self._request({
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvprop": "ids|timestamp|user|comment|size|flags",
            "rvlimit": str(min(limit, 500)),
        })
        pages = resp.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            return []
        return pages[0].get("revisions", [])

    def recentchanges(self, limit: int = 30, namespace: str | None = None,
                       user: str | None = None, rctype: str | None = None,
                       bots: bool = True) -> list[dict[str, Any]]:
        """
        Cambios recientes de la wiki (list=recentchanges).

        Util para que el admin monitoree actividad: ediciones, creaciones,
        borrados. Filtros opcionales por namespace, usuario o tipo.
        """
        params = {
            "action": "query",
            "list": "recentchanges",
            "rcprop": "title|timestamp|user|comment|sizes|flags|ids",
            "rclimit": str(min(limit, 500)),
        }
        if namespace is not None:
            params["rcnamespace"] = namespace
        if user:
            params["rcuser"] = user
        if rctype:
            params["rctype"] = rctype
        if not bots:
            params["rcshow"] = "!bot"
        return self._paginate(params, "recentchanges", limit)

    def ask(self, query: str, max_results: int = 500) -> dict[str, Any]:
        """
        Ejecuta una query Semantic MediaWiki (action=ask), paginando por
        offset hasta `max_results` o hasta agotar resultados.

        Sintaxis SMW estandar, por ejemplo:
            [[Category:Travesía]][[Año::2018]]|?Autor|?Colección

        SMW devuelve por defecto ~50 filas; sin paginacion las queries de
        categorias grandes truncaban en silencio. Aca se itera offset=N
        fusionando `results`, conservando `printrequests` de la 1a pagina.
        """
        page_size = 50
        merged: dict[str, Any] = {}
        printrequests: list[Any] = []
        offset = 0
        # Si el usuario ya puso su propio offset/limit, respetamos su intencion
        # y no paginamos automaticamente (evita resultados inesperados).
        user_paged = "offset=" in query or "limit=" in query
        while True:
            q = query if user_paged else f"{query}|offset={offset}|limit={page_size}"
            resp = self._request({"action": "ask", "query": q}).get("query", {})
            results = resp.get("results", {}) or {}
            if not printrequests:
                printrequests = resp.get("printrequests", []) or []
            merged.update(results)
            if user_paged or len(results) < page_size or len(merged) >= max_results:
                break
            offset += page_size
        return {"results": merged, "printrequests": printrequests}

    def browse(self, title: str) -> dict[str, Any]:
        """
        Devuelve las propiedades SMW de una pagina (action=browsebysubject).

        Util para descubrir que datos estructurados existen en una pagina
        antes de armar una query con #ask.
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

        Modos mutuamente excluyentes: text (reemplaza), appendtext (al final),
        prependtext (al principio); section limita a una seccion; createonly
        falla si la pagina ya existe. bot=1 marca la edicion como de bot en
        RecentChanges. Ante badtoken refresca el CSRF y reintenta una vez.
        """
        base: dict[str, str] = {
            "action": "edit",
            "title": title,
            "summary": summary,
            "bot": "1",
        }
        if text is not None:
            base["text"] = text
        elif appendtext is not None:
            base["appendtext"] = appendtext
        elif prependtext is not None:
            base["prependtext"] = prependtext
        else:
            raise ValueError("edit requiere text, appendtext o prependtext")
        if section is not None:
            base["section"] = section
        if createonly:
            base["createonly"] = "1"
        return self._write("edit", base)

    def move(self, from_title: str, to_title: str, reason: str = "",
             noredirect: bool = False, movetalk: bool = True) -> dict[str, Any]:
        """
        Renombra/mueve una pagina (action=move).

        Por defecto deja un redirect en el titulo viejo (no rompe enlaces) y
        mueve tambien la pagina de discusion asociada.
        """
        base = {
            "action": "move",
            "from": from_title,
            "to": to_title,
            "reason": reason or "Move via casiopea-wiki bot",
        }
        if movetalk:
            base["movetalk"] = "1"
        if noredirect:
            base["noredirect"] = "1"
        return self._write("move", base)

    def delete(self, title: str, reason: str = "") -> dict[str, Any]:
        """
        Borra una pagina (action=delete).

        Requiere que el bot tenga el grant `Delete pages` en su Bot Password.
        Reversible solo por un sysop via Special:Undelete. Usar con cuidado.
        """
        base = {
            "action": "delete",
            "title": title,
            "reason": reason or "Borrado via casiopea-wiki bot",
        }
        return self._write("delete", base)

    def _write(self, action: str, base: dict[str, str]) -> dict[str, Any]:
        """
        Adjunta el CSRF token y postea una accion de escritura.

        Se usa desde edit/move/delete. Ante `badtoken` (token expirado)
        refresca el token una vez y reintenta; cualquier otro error se
        reporta y aborta.
        """
        for attempt in (1, 2):
            params = dict(base)
            params["token"] = self.csrf_token(force_refresh=(attempt == 2))
            resp = self._request(params, method="POST")
            err = resp.get("error", {})
            if err.get("code") == "badtoken" and attempt == 1:
                continue
            if "error" in resp:
                sys.stderr.write(f"ERROR en {action}: {resp['error']}\n")
                sys.exit(5)
            return resp.get(action, {})
        return {}

    def upload(self, filepath: str, filename: str | None = None,
               comment: str = "", text: str | None = None,
               ignorewarnings: bool = False) -> dict[str, Any]:
        """
        Sube un archivo (action=upload).

        Para archivos chicos hace un solo POST multipart. Sobre
        CHUNKED_UPLOAD_THRESHOLD usa el protocolo chunked de MediaWiki
        (stash + chunks + publish), necesario para PDFs/imagenes grandes
        que un solo POST rechazaria.
        """
        if not os.path.isfile(filepath):
            sys.stderr.write(f"Archivo no existe: {filepath}\n")
            sys.exit(1)
        target = filename or os.path.basename(filepath)
        size = os.path.getsize(filepath)
        if size > CHUNKED_UPLOAD_THRESHOLD:
            return self._upload_chunked(filepath, target, size, comment,
                                        text, ignorewarnings)

        with open(filepath, "rb") as fh:
            content = fh.read()
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
        mime = mimetypes.guess_type(target)[0] or "application/octet-stream"
        resp = self._request(params, method="POST",
                             multipart={"file": (target, content, mime)})
        if "error" in resp:
            sys.stderr.write(f"ERROR en upload: {resp['error']}\n")
            sys.exit(5)
        return resp.get("upload", {})

    def _upload_chunked(self, filepath: str, target: str, size: int,
                        comment: str, text: str | None,
                        ignorewarnings: bool) -> dict[str, Any]:
        """
        Sube un archivo grande en chunks de CHUNK_SIZE.

        Protocolo MediaWiki: 1) primer chunk con stash=1 y filesize -> filekey;
        2) chunks siguientes con offset+filekey hasta result=Success;
        3) publicar desde el stash con filekey, comment y text.
        """
        token = self.csrf_token()
        filekey = None
        offset = 0
        with open(filepath, "rb") as fh:
            while offset < size:
                chunk = fh.read(CHUNK_SIZE)
                params = {
                    "action": "upload",
                    "filename": target,
                    "stash": "1",
                    "filesize": str(size),
                    "offset": str(offset),
                    "token": token,
                }
                if filekey:
                    params["filekey"] = filekey
                resp = self._request(
                    params, method="POST",
                    multipart={"chunk": ("chunk", chunk, "application/octet-stream")},
                )
                if "error" in resp:
                    sys.stderr.write(f"ERROR en upload (chunk @{offset}): {resp['error']}\n")
                    sys.exit(5)
                up = resp.get("upload", {})
                filekey = up.get("filekey", filekey)
                offset += len(chunk)
                sys.stderr.write(f"[upload] {offset}/{size} bytes\n")

        params = {
            "action": "upload",
            "filename": target,
            "filekey": filekey,
            "comment": comment,
            "token": token,
        }
        if text is not None:
            params["text"] = text
        if ignorewarnings:
            params["ignorewarnings"] = "1"
        resp = self._request(params, method="POST")
        if "error" in resp:
            sys.stderr.write(f"ERROR en upload (publicacion): {resp['error']}\n")
            sys.exit(5)
        return resp.get("upload", {})


# -----------------------------------------------------------------------------
# Multipart helper para upload
# -----------------------------------------------------------------------------

def _build_multipart(fields: dict[str, str], files: dict, boundary: str) -> bytes:
    """
    Construye un cuerpo multipart/form-data manualmente.

    Se usa para upload de archivos y chunks. No depende de requests para
    mantener el plugin sin dependencias externas. `files` es
    {field: (filename, bytes, mime)}.
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

    Se llama desde el subcomando `ask`. CSV y table aplanan los printouts en
    columnas; json emite tal cual lo devuelve SMW para usuarios avanzados.
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
# Salvaguarda para escrituras: dry-run con diff real
# -----------------------------------------------------------------------------

def _unified_diff(current: str, proposed: str, title: str) -> str:
    """
    Diff unificado entre el contenido actual y el propuesto.

    Se usa en el dry-run de edit/append/create para que el operador vea
    exactamente que lineas cambian, no solo cuantos chars.
    """
    diff = difflib.unified_diff(
        current.splitlines(),
        proposed.splitlines(),
        fromfile=f"a/{title} (actual)",
        tofile=f"b/{title} (propuesto)",
        lineterm="",
    )
    body = "\n".join(diff)
    return body or "(sin cambios textuales)"


def require_confirmation(title: str, action_desc: str, confirm: bool,
                         diff: str | None = None) -> None:
    """
    Imprime un dry-run y aborta si --confirm no se paso.

    Se llama al inicio de cada operacion de escritura. Asi una invocacion
    casual del CLI nunca modifica la wiki sin que el operador haya visto
    exactamente que se va a hacer, incluido el diff cuando aplica.
    """
    if confirm:
        return
    sys.stderr.write(
        "[DRY RUN] No se ejecuto ningun cambio.\n"
        f"  Pagina: {title}\n"
        f"  Operacion: {action_desc}\n"
    )
    if diff is not None:
        sys.stderr.write("  --- Diff propuesto ---\n")
        sys.stderr.write(diff + "\n")
        sys.stderr.write("  --- Fin del diff ---\n")
    sys.stderr.write(
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
    p_search.add_argument("--limit", type=int, default=20,
                          help="Total de resultados (pagina automaticamente)")

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

    p_fu = sub.add_parser("fileusage", help="Paginas que usan un archivo File:X")
    p_fu.add_argument("filename", help="Con o sin prefijo File:/Archivo:")
    p_fu.add_argument("--limit", type=int, default=500)

    p_hist = sub.add_parser("history", help="Historial de revisiones de una pagina")
    p_hist.add_argument("title")
    p_hist.add_argument("--limit", type=int, default=20)

    p_rc = sub.add_parser("recentchanges", help="Cambios recientes de la wiki")
    p_rc.add_argument("--limit", type=int, default=30)
    p_rc.add_argument("--namespace", help="Filtra por id de namespace (ej: 0)")
    p_rc.add_argument("--user", help="Filtra por usuario")
    p_rc.add_argument("--type", dest="rctype",
                      help="edit|new|log|categorize (coma-separado)")
    p_rc.add_argument("--no-bots", action="store_true",
                      help="Excluye ediciones marcadas como de bot")

    p_ask = sub.add_parser("ask", help="Query Semantic MediaWiki")
    p_ask.add_argument("query", help="Sintaxis SMW: [[Category:X]][[Prop::Val]]|?Prop1|?Prop2")
    p_ask.add_argument("--format", choices=["json", "csv", "table"], default="table")
    p_ask.add_argument("--max", type=int, default=500, dest="max_results",
                       help="Tope total de filas al paginar (default 500)")

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

    p_move = sub.add_parser("move", help="Renombra/mueve una pagina (con redirect)")
    p_move.add_argument("from_title", metavar="origen")
    p_move.add_argument("to_title", metavar="destino")
    p_move.add_argument("--reason", default="Move via casiopea-wiki bot")
    p_move.add_argument("--noredirect", action="store_true",
                        help="No dejar redirect en el titulo viejo (requiere permiso)")
    p_move.add_argument("--confirm", action="store_true")

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
    """Punto de entrada del CLI. Carga credenciales, hace login y despacha."""
    args = build_parser().parse_args()
    api_url, user, password = load_credentials()
    client = CasiopeaClient(api_url, user, password)
    client.login()

    # ---- Lectura ----
    if args.cmd == "search":
        for r in client.search(args.term, limit=args.limit):
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

    elif args.cmd == "fileusage":
        for title in client.fileusage(args.filename, limit=args.limit):
            print(title)

    elif args.cmd == "history":
        for rev in client.history(args.title, limit=args.limit):
            ts = rev.get("timestamp", "")
            usr = rev.get("user", "")
            size = rev.get("size", "")
            rid = rev.get("revid", "")
            comment = (rev.get("comment", "") or "").strip()
            print(f"{ts}  r{rid}  {usr}  ({size}b)  — {comment}")

    elif args.cmd == "recentchanges":
        changes = client.recentchanges(
            limit=args.limit, namespace=args.namespace,
            user=args.user, rctype=args.rctype, bots=not args.no_bots,
        )
        for c in changes:
            ts = c.get("timestamp", "")
            usr = c.get("user", "")
            delta = c.get("newlen", 0) - c.get("oldlen", 0)
            sign = f"+{delta}" if delta >= 0 else str(delta)
            kind = c.get("type", "")
            title = c.get("title", "")
            comment = (c.get("comment", "") or "").strip()
            print(f"{ts}  {kind:<5}  {usr}  ({sign})  {title}  — {comment}")

    elif args.cmd == "ask":
        data = client.ask(args.query, max_results=args.max_results)
        sys.stdout.write(format_ask_results(data, args.format))
        if args.format != "json":
            sys.stdout.write("\n")

    elif args.cmd == "browse":
        data = client.browse(args.title)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    # ---- Escritura: dry-run con diff, luego --confirm ----
    elif args.cmd == "edit":
        body = _read_text_input(args)
        current = client.page(args.title)
        diff = None if args.section else _unified_diff(current, body, args.title)
        require_confirmation(
            args.title, f"reemplazar contenido ({len(body)} chars)",
            args.confirm, diff,
        )
        result = client.edit(args.title, text=body, section=args.section,
                              summary=args.summary)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "append":
        body = _read_text_input(args)
        current = client.page(args.title)
        proposed = current + body
        diff = _unified_diff(current, proposed, args.title)
        require_confirmation(
            args.title, f"anadir {len(body)} chars al final",
            args.confirm, diff,
        )
        result = client.edit(args.title, appendtext=body, summary=args.summary)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "create":
        body = _read_text_input(args)
        existing = client.page(args.title)
        if existing:
            sys.stderr.write(
                f"AVISO: la pagina '{args.title}' ya existe ({len(existing)} chars). "
                "create fallara con articleexists; usa edit o append.\n"
            )
        diff = _unified_diff("", body, args.title)
        require_confirmation(
            args.title, f"crear pagina nueva ({len(body)} chars)",
            args.confirm, diff,
        )
        result = client.edit(args.title, text=body, summary=args.summary,
                              createonly=True)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "move":
        require_confirmation(
            args.from_title,
            f"mover a '{args.to_title}'"
            + (" sin redirect" if args.noredirect else " (deja redirect)"),
            args.confirm,
        )
        result = client.move(args.from_title, args.to_title,
                              reason=args.reason, noredirect=args.noredirect)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "delete":
        require_confirmation(
            args.title, f"borrar pagina (motivo: {args.reason})", args.confirm,
        )
        result = client.delete(args.title, reason=args.reason)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "upload":
        target = args.as_name or os.path.basename(args.filepath)
        require_confirmation(
            target, f"subir archivo {args.filepath}", args.confirm,
        )
        result = client.upload(args.filepath, filename=args.as_name,
                               comment=args.comment, text=args.text,
                               ignorewarnings=args.ignorewarnings)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
