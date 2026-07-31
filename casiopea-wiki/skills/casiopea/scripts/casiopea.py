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
#   prefix <prefijo>           busqueda de titulos por prefijo (autocompletado)
#   page <titulo>              wikitexto de una pagina (--section, --max-bytes)
#   pages <t1> <t2> ...        wikitexto de hasta 50 paginas en una llamada
#   sections <titulo>          indice de secciones (numero, nivel, titulo)
#   revision <revid>           wikitexto de una revision historica concreta
#   category <nombre>          paginas dentro de una categoria (paginado)
#   backlinks <titulo>         paginas que enlazan a una pagina (paginado)
#   transclusions <plantilla>  paginas que transcluyen una plantilla {{X}}
#   fileusage <archivo>        paginas que usan un archivo File:X
#   history <titulo>           historial de revisiones de una pagina
#   compare <a> <b>            diff entre dos revisiones o dos titulos
#   recentchanges              cambios recientes de la wiki
#   ask <query SMW>            query semantica, --format json|csv|table
#   browse <titulo>            propiedades semanticas de una pagina
#   properties                 lista las propiedades SMW declaradas en la wiki
#   parse                      renderiza wikitexto SIN guardar (previsualizar)
#   siteinfo                   version de MW, extensiones, namespaces
#   whoami                     identidad, grupos y permisos de la sesion
#
# Subcomandos de escritura (requieren --confirm explicito; dry-run con diff):
#   edit <titulo>              reemplaza el contenido de una pagina
#   append <titulo>            anade texto al final de una pagina
#   create <titulo>            crea una pagina nueva (falla si existe)
#   move <origen>              renombra/mueve una pagina (con redirect)
#   upload <archivo>           sube un archivo (chunked si es grande)
#   upload-from-url <url>      sube un archivo descargandolo del lado del wiki
#   delete <titulo>            borra una pagina (requiere grant Delete pages)
#   undelete <titulo>          restaura una pagina borrada
#   purge <titulo>             purga la cache de parseo (tras tocar una plantilla)
#
# Subcomandos de mantenimiento:
#   doctor                     diagnostico de credenciales, red, grants y rutas
#   sn-sync                    regenera el inventario de tokens de Stella Nova
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

VERSION = "0.5.0"

# URL del endpoint MediaWiki API de Casiopea. Sobreescribible con la variable
# de entorno CASIOPEA_API_URL para apuntar a un mirror o a una instancia de test.
DEFAULT_API_URL = "https://wiki.ead.pucv.cl/api.php"

# Atajos para --wiki. Casiopea vive en dos instancias: la de produccion y el
# espejo local de desarrollo. El espejo solo es alcanzable desde la maquina que
# lo hospeda (no desde un sandbox en la nube).
WIKI_PRESETS = {
    "prod": "https://wiki.ead.pucv.cl/api.php",
    "produccion": "https://wiki.ead.pucv.cl/api.php",
    "local": "http://casiopea.local/api.php",
}

# Cortesia de bot. maxlag detiene al bot si la replica de BD esta retrasada.
MAXLAG_SECONDS = 5
MAX_RETRIES = 4
RETRY_BASE_DELAY = 2.0  # segundos; backoff exponencial RETRY_BASE_DELAY * 2**n

# Tamano de chunk para subidas grandes (4 MiB). Sobre este umbral de archivo
# total se usa el protocolo de upload chunked de MediaWiki.
CHUNK_SIZE = 4 * 1024 * 1024
CHUNKED_UPLOAD_THRESHOLD = 8 * 1024 * 1024

# Tope de bytes que `page` vuelca a stdout antes de truncar. Existe porque el
# consumidor habitual es un agente con ventana de contexto finita: una pagina
# de 300 KB de wikitexto se come la conversacion entera sin avisar. Al truncar
# se imprime un marcador con el indice de secciones para poder volver con
# --section N. Sobreescribible con CASIOPEA_MAX_BYTES o --max-bytes.
DEFAULT_CONTENT_MAX_BYTES = 50_000

# Tope de titulos por llamada en `pages`. Es el limite de la API de MediaWiki
# para usuarios sin el permiso apihighlimits.
MAX_TITLES_PER_CALL = 50

# ---------------------------------------------------------------------------
# Taxonomia de errores
#
# Siete categorias cubren todo lo que la API puede devolver. La categoria va
# como primer token del mensaje de stderr ("categoria: detalle") para que un
# agente pueda decidir que hacer sin parsear prosa: reintentar, corregir
# argumentos, re-autenticarse o rendirse. Tomada de las convenciones del
# MediaWiki MCP Server de Professional Wiki.
# ---------------------------------------------------------------------------

ERROR_CATEGORIES = {
    "not_found": 6,        # el titulo, revision o archivo no existe
    "permission_denied": 7,  # falta el grant, la pagina esta protegida
    "invalid_input": 8,    # argumentos incompatibles o mal formados
    "conflict": 9,         # edit conflict, createonly sobre pagina existente
    "authentication": 4,   # credenciales ausentes, invalidas o expiradas
    "rate_limited": 10,    # la wiki esta frenando al bot
    "upstream_failure": 3,  # error no clasificado, red, read-only
}

# Codigos de error de la API de MediaWiki mapeados a categoria. Lo que no
# figure aca cae en upstream_failure conservando el mensaje crudo: se pierde
# precision, no informacion.
MW_ERROR_MAP = {
    "missingtitle": "not_found",
    "nosuchrevid": "not_found",
    "nosuchsection": "not_found",
    "notanarticle": "not_found",
    "cantundelete": "not_found",
    "permissiondenied": "permission_denied",
    "protectedpage": "permission_denied",
    "protectedtitle": "permission_denied",
    "cascadeprotected": "permission_denied",
    "blocked": "permission_denied",
    "autoblocked": "permission_denied",
    "abusefilter-disallowed": "permission_denied",
    "readapidenied": "permission_denied",
    "writeapidenied": "permission_denied",
    "badtags": "invalid_input",
    "invalidtitle": "invalid_input",
    "invalidparammix": "invalid_input",
    "missingparam": "invalid_input",
    "unknownformat": "invalid_input",
    "badquery": "invalid_input",
    "articleexists": "conflict",
    "editconflict": "conflict",
    "fileexists-no-change": "conflict",
    "assertuserfailed": "authentication",
    "assertbotfailed": "authentication",
    "notloggedin": "authentication",
    "badtoken": "authentication",
    "mustbeloggedin": "authentication",
    "ratelimited": "rate_limited",
    "maxlag": "rate_limited",
    "readonly": "upstream_failure",
}


def classify(code: str | None) -> str:
    """
    Traduce un codigo de error de MediaWiki a una de las siete categorias.

    Se usa desde fail() y desde _write(). Devolver upstream_failure para lo
    desconocido es deliberado: preferimos una categoria gruesa y el mensaje
    intacto antes que inventar una clasificacion.
    """
    if not code:
        return "upstream_failure"
    return MW_ERROR_MAP.get(code, "upstream_failure")


def fail(category: str, message: str, hint: str | None = None) -> None:
    """
    Aborta imprimiendo "categoria: mensaje" en stderr y saliendo con el codigo
    de la categoria.

    Se llama desde cada punto donde el CLI se rinde. El formato es estable a
    proposito: es la interfaz que consume el skill (y el wrapper MCP) para
    decidir si reintentar o pedirle algo a la persona.
    """
    sys.stderr.write(f"{category}: {message}\n")
    if hint:
        sys.stderr.write(f"  sugerencia: {hint}\n")
    sys.exit(ERROR_CATEGORIES.get(category, 3))


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
            "authentication: no hay credenciales de Casiopea en ninguna ruta conocida.\n\n"
            "Define CASIOPEA_BOT_USER y CASIOPEA_BOT_PASS como variables de\n"
            "entorno, o crea un archivo en una de estas rutas:\n"
            "  ~/Sites/casiopea-skill/credentials\n"
            "  ~/.config/casiopea/credentials\n"
            "  ~/casiopea-bot/credentials\n"
            "  (o monta una carpeta cuyo nombre contenga 'casiopea' en el sandbox)\n\n"
            "Con este contenido y permisos 600:\n\n"
            "  CASIOPEA_BOT_USER=TuCuenta@NombreDelBot\n"
            "  CASIOPEA_BOT_PASS=la-contrasena-larga-de-bot-password\n\n"
            "El bot se crea con TU cuenta en https://wiki.ead.pucv.cl/Special:BotPasswords\n"
            "y todo lo que haga queda firmado con tu nombre en el historial.\n"
        )
        sys.exit(ERROR_CATEGORIES["authentication"])

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
                cat = "rate_limited" if exc.code in (429, 503) else "upstream_failure"
                if exc.code in (401, 403):
                    cat = "permission_denied"
                fail(cat, f"HTTP {exc.code} desde {self.api_url}: {exc.reason}")
            except urllib.error.URLError as exc:
                if attempt <= MAX_RETRIES:
                    self._sleep_retry(None, attempt, f"red ({exc.reason})")
                    continue
                fail("upstream_failure", f"sin respuesta de {self.api_url}: {exc.reason}",
                     "si apuntas a casiopea.local, solo es alcanzable desde la maquina "
                     "que lo hospeda")

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
            fail(
                "authentication",
                f"login rechazado ({result}): {reason}",
                "el usuario va en formato TuCuenta@NombreDelBot, no solo TuCuenta. "
                "Se regenera en https://wiki.ead.pucv.cl/Special:BotPasswords",
            )

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
    # Lectura: introspeccion, lote, secciones, preview y diff
    #
    # Este bloque nacio de mirar que herramientas expone el MediaWiki MCP
    # Server de Professional Wiki y cuales de ellas le faltaban a este CLI.
    # Casi todas existen para que un agente pueda VERIFICAR antes de escribir,
    # que es de donde viene el 90% del valor.
    # -------------------------------------------------------------------------

    def prefix_search(self, prefix: str, namespace: int | None = None,
                      limit: int = 20) -> list[str]:
        """
        Titulos que empiezan con un prefijo (list=prefixsearch).

        Distinto de search(): no mira el contenido, solo el titulo, y es lo
        correcto para resolver "como se llama exactamente esa pagina" antes de
        pedirla con page(). Tambien sirve para enumerar un arbol de subpaginas
        ("Stella Nova/" devuelve todas sus hijas).
        """
        params = {
            "action": "query",
            "list": "prefixsearch",
            "pssearch": prefix,
            "pslimit": str(min(limit, 100)),
        }
        if namespace is not None:
            params["psnamespace"] = str(namespace)
        items = self._paginate(params, "prefixsearch", limit)
        return [p["title"] for p in items]

    def pages(self, titles: list[str]) -> dict[str, str | None]:
        """
        Wikitexto de varias paginas en una sola llamada (hasta 50 titulos).

        Se usa cuando hay que comparar o auditar un conjunto: las 12 plantillas
        con sufijo "2", las subpaginas de un curso, las fichas de una categoria.
        Una llamada en vez de 50 ahorra tiempo y cuota. Un titulo inexistente
        aparece con valor None en vez de romper el lote entero.
        """
        if len(titles) > MAX_TITLES_PER_CALL:
            fail("invalid_input",
                 f"pages acepta hasta {MAX_TITLES_PER_CALL} titulos, se pidieron {len(titles)}",
                 "partir la lista en tandas")
        resp = self._request({
            "action": "query",
            "prop": "revisions",
            "titles": "|".join(titles),
            "rvprop": "content",
            "rvslots": "main",
        })
        out: dict[str, str | None] = {}
        for page in resp.get("query", {}).get("pages", []) or []:
            title = page.get("title", "")
            if page.get("missing"):
                out[title] = None
                continue
            revs = page.get("revisions", [])
            out[title] = (revs[0].get("slots", {}).get("main", {}).get("content", "")
                          if revs else "")
        return out

    def sections(self, title: str) -> list[dict[str, Any]]:
        """
        Indice de secciones de una pagina (action=parse&prop=sections).

        Se usa para navegar una pagina larga sin traerla entera: primero el
        indice, despues page(title, section=N). Tambien lo emite el marcador
        de truncado, para que el siguiente paso sea obvio.
        """
        resp = self._request({
            "action": "parse",
            "page": title,
            "prop": "sections",
        })
        if "error" in resp:
            err = resp["error"]
            fail(classify(err.get("code")), err.get("info", str(err)))
        return resp.get("parse", {}).get("sections", []) or []

    def page_section(self, title: str, section: str) -> str:
        """Wikitexto de una sola seccion (prop=wikitext + section=N)."""
        resp = self._request({
            "action": "parse",
            "page": title,
            "section": section,
            "prop": "wikitext",
        })
        if "error" in resp:
            err = resp["error"]
            fail(classify(err.get("code")), err.get("info", str(err)))
        return resp.get("parse", {}).get("wikitext", "")

    def revision(self, revid: int) -> dict[str, Any]:
        """
        Una revision historica concreta por su id (prop=revisions&revids=).

        Distinto de history(), que lista metadatos: esto trae el contenido de
        esa revision. Util para recuperar una version anterior de una plantilla
        que se rompio, sin pasar por la interfaz web.
        """
        resp = self._request({
            "action": "query",
            "prop": "revisions",
            "revids": str(revid),
            "rvprop": "ids|timestamp|user|comment|content",
            "rvslots": "main",
        })
        pages = resp.get("query", {}).get("pages", []) or []
        if not pages or not pages[0].get("revisions"):
            fail("not_found", f"no existe la revision {revid}")
        page = pages[0]
        rev = page["revisions"][0]
        return {
            "title": page.get("title"),
            "revid": rev.get("revid"),
            "timestamp": rev.get("timestamp"),
            "user": rev.get("user"),
            "comment": rev.get("comment"),
            "content": rev.get("slots", {}).get("main", {}).get("content", ""),
        }

    def compare(self, from_ref: str, to_ref: str) -> str:
        """
        Diff calculado por el servidor entre dos revisiones o dos titulos
        (action=compare).

        Acepta ids numericos ("948231") o titulos ("Plantilla:Persona"). Se
        prefiere a traer los dos textos y diffearlos aca: el servidor ya sabe
        hacerlo, devuelve menos bytes y respeta el algoritmo que la wiki
        muestra en su propia vista de diferencias.
        """
        def ref(value: str, side: str) -> dict[str, str]:
            key = "fromrev" if side == "from" else "torev"
            title_key = "fromtitle" if side == "from" else "totitle"
            return {key: value} if value.isdigit() else {title_key: value}

        params = {"action": "compare", "prop": "diff|title", "difftype": "unified"}
        params.update(ref(from_ref, "from"))
        params.update(ref(to_ref, "to"))
        resp = self._request(params)
        if "error" in resp:
            err = resp["error"]
            # difftype=unified existe desde MW 1.35; si esta wiki es mas vieja,
            # se reintenta con el diff de tabla (que hay que aplanar despues).
            if err.get("code") == "badvalue":
                params.pop("difftype")
                resp = self._request(params)
            if "error" in resp:
                err = resp["error"]
                fail(classify(err.get("code")), err.get("info", str(err)))
        return resp.get("compare", {}).get("body", "")

    def parse_wikitext(self, text: str, title: str = "Previsualización") -> dict[str, Any]:
        """
        Renderiza wikitexto contra la wiki real SIN guardarlo (action=parse).

        Es la herramienta central del flujo de diseno: valida que las
        plantillas invocadas existan, que las clases del skin esten bien
        escritas y que el parser no proteste, antes de que nada quede en el
        historial. El parametro title da el contexto (afecta a {{PAGENAME}} y
        a los enlaces relativos), pero no crea ni toca esa pagina.
        """
        resp = self._request({
            "action": "parse",
            "title": title,
            "text": text,
            "contentmodel": "wikitext",
            "prop": "text|templates|links|externallinks|categories|warnings|modules",
            "pst": "1",
        }, method="POST")
        if "error" in resp:
            err = resp["error"]
            fail(classify(err.get("code")), err.get("info", str(err)))
        return resp.get("parse", {})

    def siteinfo(self) -> dict[str, Any]:
        """
        Version de MediaWiki, extensiones instaladas, namespaces y estadisticas.

        Sirve para no adivinar: si una receta depende de TemplateStylesExtender
        o de NoTitle, esto dice si estan. Tambien da los nombres localizados de
        los namespaces, que en Casiopea estan en espanol.
        """
        resp = self._request({
            "action": "query",
            "meta": "siteinfo",
            "siprop": "general|namespaces|extensions|statistics",
        })
        return resp.get("query", {})

    def whoami(self) -> dict[str, Any]:
        """
        Identidad de la sesion: nombre, grupos y permisos efectivos.

        Se corre antes de intentar una escritura dudosa. Si el bot no tiene el
        permiso, es mas barato saberlo aca que fallar a mitad de una tanda.
        """
        resp = self._request({
            "action": "query",
            "meta": "userinfo",
            "uiprop": "groups|rights|editcount|blockinfo",
        })
        return resp.get("query", {}).get("userinfo", {})

    def smw_properties(self, limit: int = 500) -> list[str]:
        """
        Propiedades SMW declaradas en la wiki (paginas del namespace 102).

        En Casiopea el namespace de propiedades es 102 y los nombres estan en
        espanol con tildes reales. Esta lista es el antidoto contra el error
        mas comun de este skill: escribir `Coleccion` cuando la propiedad se
        llama `Colección` y recibir columnas vacias sin ningun mensaje.
        """
        items = self._paginate({
            "action": "query",
            "list": "allpages",
            "apnamespace": "102",
            "aplimit": str(min(limit, 500)),
        }, "allpages", limit)
        return [p["title"].split(":", 1)[-1] for p in items]

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

    def undelete(self, title: str, reason: str = "") -> dict[str, Any]:
        """
        Restaura una pagina borrada (action=undelete).

        Restaura todas las revisiones archivadas. Es la contraparte de delete()
        y la razon por la que un borrado no es el fin del mundo, siempre que la
        wiki no haya purgado el archivo. Requiere el mismo grant que delete.
        """
        base = {
            "action": "undelete",
            "title": title,
            "reason": reason or "Restauracion via casiopea-wiki bot",
        }
        return self._write("undelete", base)

    def purge(self, titles: list[str], forcelinkupdate: bool = True) -> dict[str, Any]:
        """
        Purga la cache de parseo de una o varias paginas (action=purge).

        Necesario despues de editar una plantilla o su /style.css: MediaWiki
        cachea el HTML renderizado y las paginas que la transcluyen siguen
        mostrando la version vieja durante un rato largo. forcelinkupdate
        ademas recalcula las tablas de enlaces y las anotaciones semanticas.

        No modifica contenido, pero se cuenta como escritura porque consume
        cuota y requiere POST con token.
        """
        base = {
            "action": "purge",
            "titles": "|".join(titles),
        }
        if forcelinkupdate:
            base["forcelinkupdate"] = "1"
        return self._write("purge", base)

    def upload_from_url(self, url: str, filename: str, comment: str = "",
                        text: str | None = None,
                        ignorewarnings: bool = False) -> dict[str, Any]:
        """
        Sube un archivo haciendo que el servidor lo descargue (action=upload
        con url=).

        Evita el viaje de ida y vuelta cuando el original ya esta en linea. La
        wiki debe tener habilitado $wgAllowCopyUploads y el dominio de origen
        en la lista blanca; si no, devuelve copyuploaddisabled y hay que bajar
        el archivo y usar upload() normal.
        """
        base = {
            "action": "upload",
            "filename": filename,
            "url": url,
            "comment": comment or "Upload via casiopea-wiki bot",
        }
        if text is not None:
            base["text"] = text
        if ignorewarnings:
            base["ignorewarnings"] = "1"
        return self._write("upload", base)

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
                code = err.get("code")
                info = err.get("info") or str(err)
                hints = {
                    "permission_denied": "revisa los grants del bot en "
                                         "Special:BotPasswords; puede que la pagina "
                                         "este protegida",
                    "conflict": "alguien edito la pagina en el intervalo, o ya existe: "
                                "vuelve a traerla y reconstruye el cambio",
                    "not_found": "verifica el titulo exacto con prefix o search",
                }
                category = classify(code)
                fail(category, f"{action} fallo ({code}): {info}", hints.get(category))
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


def emit_content(text: str, max_bytes: int, sections: list[dict[str, Any]] | None,
                 remedy: str) -> None:
    """
    Vuelca texto a stdout truncandolo si excede el presupuesto de bytes.

    Se usa en `page`, `pages` y `revision`. Cuando trunca imprime un marcador
    al final con el indice de secciones disponibles y una frase de remedio,
    para que quien lea la salida (una persona o un agente) sepa exactamente
    con que comando conseguir el resto en vez de asumir que eso era todo.
    Truncar en silencio es la peor opcion posible: se ve igual que un exito.
    """
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        sys.stdout.write(text)
        return

    cut = raw[:max_bytes].decode("utf-8", errors="ignore")
    sys.stdout.write(cut)
    marker = f"\n\n[truncado en {max_bytes} de {len(raw)} bytes]"
    if sections:
        listado = ", ".join(
            f"{s.get('index')} ({s.get('line', '').strip()})"
            for s in sections[:40] if s.get("index")
        )
        marker += f"\n[secciones disponibles: 0 (encabezado), {listado}]"
    marker += f"\n[{remedy}]\n"
    sys.stderr.write(marker)


def emit_list(items: list[str], limit: int, what: str, narrow_hint: str) -> None:
    """
    Imprime una lista y avisa si toco el tope.

    Misma logica que emit_content pero para listados: si se devolvieron
    exactamente `limit` elementos, es muy probable que haya mas y el marcador
    lo dice. Sin esto, un `category` con --limit 100 sobre una categoria de
    4000 paginas parece una categoria de 100 paginas.
    """
    for item in items:
        print(item)
    if len(items) >= limit:
        sys.stderr.write(
            f"[tope alcanzado: {len(items)} {what}. Puede haber mas — {narrow_hint}]\n"
        )


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
# Mantenimiento: diagnostico y sincronizacion de la doctrina grafica
# -----------------------------------------------------------------------------

def run_doctor(api_url: str) -> int:
    """
    Diagnostico de instalacion. No toca la wiki mas alla de un login y un par
    de lecturas.

    Existe porque el 90% de los reportes de "no funciona" son una de cuatro
    cosas: Python demasiado viejo, credenciales en una ruta que el script no
    mira, el usuario escrito sin @NombreBot, o grants insuficientes. Este
    comando responde las cuatro de una vez, en orden, y sigue adelante aunque
    un paso falle para dar el cuadro completo en una sola corrida.
    """
    ok = True
    print(f"casiopea.py {VERSION}")
    print(f"python {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 10):
        print("  FALLA: se requiere Python 3.10 o superior (se usa `X | Y` en anotaciones)")
        ok = False
    print(f"script: {os.path.abspath(__file__)}")
    print(f"endpoint: {api_url}")

    print("\ncredenciales")
    env_user = os.environ.get("CASIOPEA_BOT_USER")
    if env_user:
        print(f"  origen: variables de entorno (usuario {env_user})")
    else:
        found = [p for p in _candidate_credential_paths() if p and os.path.isfile(p)]
        if found:
            print(f"  origen: {found[0]}")
            try:
                mode = oct(os.stat(found[0]).st_mode & 0o777)
                print(f"  permisos: {mode}"
                      + ("" if mode == "0o600" else "  (conviene chmod 600)"))
            except OSError:
                pass
            for extra in found[1:]:
                print(f"  (tambien existe, ignorado: {extra})")
        else:
            print("  FALLA: ningun archivo de credenciales en las rutas conocidas")
            for p in _candidate_credential_paths():
                if p:
                    print(f"    buscado en: {p}")
            ok = False

    if not ok:
        print("\nresultado: hay problemas que resolver antes de usar el skill")
        return 1

    print("\nconexion e identidad")
    try:
        _, user, password = load_credentials()
        client = CasiopeaClient(api_url, user, password)
        client.login()
        info = client.whoami()
        print(f"  autenticado como: {info.get('name')}")
        print(f"  grupos: {', '.join(info.get('groups', [])) or '(ninguno)'}")
        if info.get("blockedby"):
            print(f"  FALLA: la cuenta esta bloqueada por {info['blockedby']}")
            ok = False
        rights = set(info.get("rights", []))
        for right, label in (("read", "leer"), ("edit", "editar"),
                             ("createpage", "crear paginas"), ("move", "mover"),
                             ("upload", "subir archivos"), ("delete", "borrar")):
            mark = "si" if right in rights else "no"
            print(f"  permiso {label}: {mark}")
    except SystemExit:
        return 1

    print("\nextensiones relevantes")
    try:
        site = client.siteinfo()
        general = site.get("general", {})
        print(f"  MediaWiki {general.get('generator', '?')}")
        # Los nombres que reporta siteinfo son los del extension.json, sin
        # espacios: "SemanticMediaWiki", no "Semantic MediaWiki".
        installed = {e.get("name", ""): e.get("version", "")
                     for e in site.get("extensions", [])}
        for wanted, porque in (
            ("SemanticMediaWiki", "queries #ask"),
            ("SemanticResultFormats", "formatos de resultado"),
            ("TemplateStyles", "CSS por plantilla"),
            ("TemplateStylesExtender", "custom properties en TemplateStyles"),
            ("PageForms", "formularios Nuevo X"),
            ("NoTitle", "__NOTITLE__"),
            ("Widgets", "widgets tipo FlickrSetShow"),
        ):
            if wanted in installed:
                ver = installed[wanted]
                print(f"  {wanted} {ver}".rstrip() + f"  ({porque})")
            else:
                print(f"  {wanted}: NO INSTALADA  ({porque} no funcionara)")
    except SystemExit:
        print("  (no se pudo consultar siteinfo)")

    print("\nresultado: todo en orden" if ok else "\nresultado: revisa las FALLAs")
    return 0 if ok else 1


# Fuentes de la doctrina grafica. sn-sync las lee y destila un inventario
# mecanico (tokens y clases realmente existentes) que acompana al documento
# curado `references/stella-nova.md`. Se separan a proposito: lo generado se
# puede regenerar, lo curado se escribe a mano.
SN_RAW_BASE = "https://raw.githubusercontent.com/hspencer/stella-nova/main"
SN_WIKI_PAGES = [
    "Stella Nova",
    "Stella Nova/Wikitexto",
    "Stella Nova/Grilla",
    "Stella Nova/Diseño CSS para Casiopea",
]


def _http_get(url: str) -> str:
    """GET simple sin autenticacion. Se usa solo para leer el repo del skin."""
    req = urllib.request.Request(url, headers={"User-Agent": f"casiopea-cli/{VERSION}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def run_sn_sync(out_path: str | None, check_wiki: bool, api_url: str) -> int:
    """
    Regenera el inventario de tokens y clases de Stella Nova.

    Lee `resources/tokens.css` y `skin.json` del repo del skin y extrae la
    lista real de custom properties por capa, mas la version. Opcionalmente
    compara contra las paginas [[Stella Nova/*]] de la wiki para senalar
    divergencias entre repo y documentacion publicada, que las hay.

    No requiere credenciales para la parte del repo. El resultado se escribe
    en references/stella-nova-inventario.md, junto al documento curado.
    """
    print("leyendo el repositorio del skin...", file=sys.stderr)
    try:
        tokens_css = _http_get(f"{SN_RAW_BASE}/resources/tokens.css")
        skin_json = _http_get(f"{SN_RAW_BASE}/skin.json")
        wikitexto = _http_get(f"{SN_RAW_BASE}/docs/WIKITEXTO.md")
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        fail("upstream_failure", f"no se pudo leer el repo de Stella Nova: {exc}")

    version = json.loads(skin_json).get("version", "desconocida")

    # Capas: una custom property es primitiva si su nombre sigue el patron
    # --sn-<familia>-<stop numerico>; de componente si empieza por uno de los
    # prefijos de control; semantica en cualquier otro caso.
    import re
    declared = re.findall(r"^\s*(--sn-[a-z0-9-]+)\s*:\s*([^;]+);", tokens_css,
                          flags=re.MULTILINE)
    seen: dict[str, str] = {}
    for name, value in declared:
        seen.setdefault(name, " ".join(value.split()))

    component_prefixes = ("--sn-btn-", "--sn-field-", "--sn-on-", "--sn-opt-",
                          "--sn-focus-")
    # Primitivas sin stop numerico: la unica del sistema es el blanco puro.
    primitive_exceptions = {"--sn-blanco"}
    primitives, semantics, components = [], [], []
    for name, value in sorted(seen.items()):
        # Los data-URI de los iconos son ilegibles en una tabla y no aportan.
        if len(value) > 90:
            value = value[:87] + "..."
        if name.startswith(component_prefixes):
            components.append((name, value))
        elif re.match(r"^--sn-[a-z]+-\d+$", name) or name in primitive_exceptions:
            primitives.append((name, value))
        else:
            semantics.append((name, value))

    classes = sorted(set(re.findall(r"^### `([a-z0-9*\- ]+?)`", wikitexto,
                                    flags=re.MULTILINE)))

    lines = [
        "# Stella Nova — inventario generado",
        "",
        "Archivo **generado** por `casiopea.py sn-sync`. No editarlo a mano: el",
        "siguiente sync lo sobreescribe. La doctrina curada, que sí se escribe a",
        "mano, vive en `stella-nova.md`.",
        "",
        f"Versión del skin leída del repositorio: **{version}**.",
        "",
        "## Tokens semánticos (los que consumen las plantillas)",
        "",
        "| Token | Valor declarado |",
        "|---|---|",
    ]
    lines += [f"| `{n}` | `{v}` |" for n, v in semantics]
    lines += [
        "",
        "## Tokens de componente (chrome del skin, rara vez en plantillas)",
        "",
        "| Token | Valor declarado |",
        "|---|---|",
    ]
    lines += [f"| `{n}` | `{v}` |" for n, v in components]
    lines += [
        "",
        "## Primitivas (paleta interna, no usar en plantillas)",
        "",
        "| Primitiva | Valor |",
        "|---|---|",
    ]
    lines += [f"| `{n}` | `{v}` |" for n, v in primitives]
    lines += [
        "",
        "## Clases opt-in documentadas en el repositorio",
        "",
    ]
    lines += [f"- `{c}`" for c in classes]

    if check_wiki:
        lines += ["", "## Cotejo con la wiki de producción", ""]
        try:
            _, user, password = load_credentials()
            client = CasiopeaClient(api_url, user, password)
            client.login()
            for title in SN_WIKI_PAGES:
                text = client.page(title)
                if not text:
                    lines.append(f"- `{title}`: **no existe** en esta wiki")
                    continue
                missing = [n for n, _ in semantics if n not in text]
                lines.append(
                    f"- `{title}`: {len(text)} caracteres; "
                    f"menciona {len(semantics) - len(missing)} de {len(semantics)} "
                    "tokens semánticos"
                )
        except SystemExit:
            lines.append("- (no se pudo consultar la wiki; solo inventario del repositorio)")

    lines += [
        "",
        "Regenerar con:",
        "",
        "```bash",
        "python casiopea.py sn-sync",
        "```",
        "",
    ]

    body = "\n".join(lines)
    target = out_path or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "references", "stella-nova-inventario.md",
    )
    target = os.path.normpath(target)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"escrito: {target}", file=sys.stderr)
    print(f"  skin v{version} · {len(semantics)} semánticos · "
          f"{len(components)} de componente · {len(primitives)} primitivas · "
          f"{len(classes)} clases", file=sys.stderr)
    return 0


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Define los subcomandos del CLI. Cada uno mapea 1:1 a un metodo del cliente."""
    parser = argparse.ArgumentParser(
        prog="casiopea",
        description="Cliente para la wiki Casiopea de la e[ad] PUCV (Semantic MediaWiki).",
    )
    parser.add_argument("--version", action="version", version=f"casiopea.py {VERSION}")
    parser.add_argument("--wiki", choices=sorted(WIKI_PRESETS),
                        help="Instancia a la que apuntar (default: prod)")
    parser.add_argument("--api", help="URL completa de api.php; gana sobre --wiki")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ---- Lectura ----
    p_search = sub.add_parser("search", help="Busqueda full-text")
    p_search.add_argument("term")
    p_search.add_argument("--limit", type=int, default=20,
                          help="Total de resultados (pagina automaticamente)")

    p_prefix = sub.add_parser("prefix", help="Titulos que empiezan con un prefijo")
    p_prefix.add_argument("prefix")
    p_prefix.add_argument("--namespace", type=int,
                          help="Restringe a un namespace (10=Plantilla, 102=Propiedad)")
    p_prefix.add_argument("--limit", type=int, default=20)

    p_page = sub.add_parser("page", help="Wikitexto de una pagina")
    p_page.add_argument("title")
    p_page.add_argument("--section", help="Solo una seccion (0=encabezado, 1..N)")
    p_page.add_argument("--max-bytes", type=int, dest="max_bytes",
                        default=int(os.environ.get("CASIOPEA_MAX_BYTES",
                                                   DEFAULT_CONTENT_MAX_BYTES)),
                        help=f"Tope antes de truncar (default {DEFAULT_CONTENT_MAX_BYTES})")

    p_pages = sub.add_parser("pages", help=f"Wikitexto de hasta {MAX_TITLES_PER_CALL} paginas")
    p_pages.add_argument("titles", nargs="+")
    p_pages.add_argument("--max-bytes", type=int, dest="max_bytes",
                         default=int(os.environ.get("CASIOPEA_MAX_BYTES",
                                                    DEFAULT_CONTENT_MAX_BYTES)))

    p_sec = sub.add_parser("sections", help="Indice de secciones de una pagina")
    p_sec.add_argument("title")

    p_rev = sub.add_parser("revision", help="Wikitexto de una revision historica")
    p_rev.add_argument("revid", type=int)
    p_rev.add_argument("--max-bytes", type=int, dest="max_bytes",
                       default=int(os.environ.get("CASIOPEA_MAX_BYTES",
                                                  DEFAULT_CONTENT_MAX_BYTES)))

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

    p_props = sub.add_parser("properties",
                             help="Propiedades SMW declaradas (namespace 102)")
    p_props.add_argument("--limit", type=int, default=500)
    p_props.add_argument("--grep", help="Filtra por subcadena, sin distinguir tildes")

    p_cmp = sub.add_parser("compare", help="Diff entre dos revisiones o dos titulos")
    p_cmp.add_argument("from_ref", metavar="desde", help="revid numerico o titulo")
    p_cmp.add_argument("to_ref", metavar="hasta", help="revid numerico o titulo")

    p_parse = sub.add_parser("parse",
                             help="Previsualiza wikitexto sin guardarlo en la wiki")
    p_parse.add_argument("--from-file", help="Leer el wikitexto de un archivo")
    p_parse.add_argument("--title", default="Previsualización",
                         help="Titulo de contexto (no se crea ni se toca esa pagina)")
    p_parse.add_argument("--html", action="store_true",
                         help="Volcar tambien el HTML renderizado")

    sub.add_parser("siteinfo", help="Version de MediaWiki, extensiones y namespaces")
    sub.add_parser("whoami", help="Identidad, grupos y permisos de la sesion")

    # ---- Mantenimiento ----
    sub.add_parser("doctor", help="Diagnostico de credenciales, red, grants y rutas")

    p_sn = sub.add_parser("sn-sync",
                          help="Regenera el inventario de tokens de Stella Nova")
    p_sn.add_argument("--out", help="Ruta de salida (default: references/)")
    p_sn.add_argument("--check-wiki", action="store_true",
                      help="Ademas cotejar contra las paginas [[Stella Nova/*]]")

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

    p_undel = sub.add_parser("undelete", help="Restaura una pagina borrada")
    p_undel.add_argument("title")
    p_undel.add_argument("--reason", default="Restauracion via casiopea-wiki bot")
    p_undel.add_argument("--confirm", action="store_true")

    p_purge = sub.add_parser(
        "purge",
        help="Purga la cache de parseo (correr tras editar una plantilla o su CSS)")
    p_purge.add_argument("titles", nargs="+")
    p_purge.add_argument("--no-linkupdate", action="store_true",
                         help="No recalcular enlaces ni anotaciones semanticas")
    p_purge.add_argument("--confirm", action="store_true")

    p_up = sub.add_parser("upload", help="Sube un archivo (imagen, PDF, etc.)")
    p_up.add_argument("filepath")
    p_up.add_argument("--as", dest="as_name", help="Nombre de archivo en la wiki")
    p_up.add_argument("--comment", default="Upload via casiopea-wiki bot")
    p_up.add_argument("--text", help="Wikitexto inicial de la pagina File:")
    p_up.add_argument("--ignorewarnings", action="store_true")
    p_up.add_argument("--confirm", action="store_true")

    p_upurl = sub.add_parser("upload-from-url",
                             help="Sube un archivo descargandolo del lado del servidor")
    p_upurl.add_argument("url")
    p_upurl.add_argument("--as", dest="as_name", required=True,
                         help="Nombre de archivo en la wiki (obligatorio)")
    p_upurl.add_argument("--comment", default="Upload via casiopea-wiki bot")
    p_upurl.add_argument("--text", help="Wikitexto inicial de la pagina File:")
    p_upurl.add_argument("--ignorewarnings", action="store_true")
    p_upurl.add_argument("--confirm", action="store_true")

    return parser


def _read_text_input(args) -> str:
    """Lee el contenido a escribir desde --from-file o desde stdin."""
    if args.from_file:
        with open(args.from_file, "r", encoding="utf-8") as fh:
            return fh.read()
    return sys.stdin.read()


def _resolve_api(args) -> str:
    """
    Decide contra que endpoint hablar.

    Precedencia: --api explicito, luego --wiki (atajo), luego lo que traiga el
    archivo de credenciales o CASIOPEA_API_URL, y por ultimo produccion.
    Devolver esto por separado permite que `doctor` y `sn-sync` lo usen sin
    haber cargado credenciales todavia.
    """
    if getattr(args, "api", None):
        return args.api
    if getattr(args, "wiki", None):
        return WIKI_PRESETS[args.wiki]
    return os.environ.get("CASIOPEA_API_URL", DEFAULT_API_URL)


def main() -> None:
    """Punto de entrada del CLI. Carga credenciales, hace login y despacha."""
    args = build_parser().parse_args()

    # sn-sync lee un repositorio publico; no hace falta molestar a la wiki
    # (salvo con --check-wiki, que carga credenciales por su cuenta).
    if args.cmd == "sn-sync":
        sys.exit(run_sn_sync(args.out, args.check_wiki, _resolve_api(args)))

    if args.cmd == "doctor":
        sys.exit(run_doctor(_resolve_api(args)))

    api_url, user, password = load_credentials()
    if getattr(args, "api", None) or getattr(args, "wiki", None):
        api_url = _resolve_api(args)
    client = CasiopeaClient(api_url, user, password)
    client.login()

    # ---- Lectura ----
    if args.cmd == "search":
        for r in client.search(args.term, limit=args.limit):
            print(f"{r['title']}\n  {r.get('snippet', '').strip()}\n")

    elif args.cmd == "prefix":
        emit_list(client.prefix_search(args.prefix, args.namespace, args.limit),
                  args.limit, "titulos", "sube --limit o afina el prefijo")

    elif args.cmd == "page":
        if args.section is not None:
            text = client.page_section(args.title, args.section)
            secciones = None
        else:
            text = client.page(args.title)
            secciones = None
        if not text:
            fail("not_found", f"pagina no encontrada o vacia: {args.title}",
                 "verifica el titulo exacto con `prefix` o `search`")
        if args.section is None and len(text.encode("utf-8")) > args.max_bytes:
            secciones = client.sections(args.title)
        emit_content(text, args.max_bytes, secciones,
                     f'para una seccion concreta: page "{args.title}" --section N')

    elif args.cmd == "pages":
        result = client.pages(args.titles)
        for title, content in result.items():
            print(f"\n===== {title} =====")
            if content is None:
                print("(no existe)")
                continue
            emit_content(content, args.max_bytes, None,
                         f'para el texto completo: page "{title}"')
            sys.stdout.write("\n")

    elif args.cmd == "sections":
        for s in client.sections(args.title):
            print(f"{s.get('index', ''):>4}  h{s.get('level', '?')}  {s.get('line', '')}")

    elif args.cmd == "revision":
        rev = client.revision(args.revid)
        print(f"# {rev['title']} · r{rev['revid']} · {rev['timestamp']} · {rev['user']}")
        print(f"# {(rev.get('comment') or '').strip()}\n")
        emit_content(rev["content"], args.max_bytes, None,
                     "sube --max-bytes para ver el resto")

    elif args.cmd == "category":
        emit_list(client.category(args.name, limit=args.limit), args.limit,
                  "paginas", "sube --limit")

    elif args.cmd == "backlinks":
        emit_list(client.backlinks(args.title, limit=args.limit), args.limit,
                  "paginas", "sube --limit")

    elif args.cmd == "transclusions":
        emit_list(client.transclusions(args.template, limit=args.limit), args.limit,
                  "paginas", "sube --limit antes de concluir que es seguro borrarla")

    elif args.cmd == "fileusage":
        emit_list(client.fileusage(args.filename, limit=args.limit), args.limit,
                  "paginas", "sube --limit antes de concluir que es seguro borrarlo")

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

    elif args.cmd == "properties":
        props = client.smw_properties(limit=args.limit)
        if args.grep:
            import unicodedata

            def flatten(s: str) -> str:
                # Compara sin tildes ni mayusculas: la propiedad se llama
                # "Colección" y la persona casi siempre escribe "coleccion".
                return "".join(
                    c for c in unicodedata.normalize("NFD", s.lower())
                    if unicodedata.category(c) != "Mn"
                )

            needle = flatten(args.grep)
            props = [p for p in props if needle in flatten(p)]
        emit_list(props, args.limit, "propiedades", "sube --limit")

    elif args.cmd == "compare":
        body = client.compare(args.from_ref, args.to_ref)
        if not body.strip():
            print("(sin diferencias)")
        else:
            # La API envuelve el diff en filas de tabla HTML aunque se pida
            # difftype=unified. Se despoja el marcado y queda un diff unificado
            # normal, que es lo que espera leer una terminal o un agente.
            import html
            import re
            text = re.sub(r"</tr\s*>", "\n", body)
            text = re.sub(r"<[^>]+>", "", text)
            print(html.unescape(text).strip())

    elif args.cmd == "parse":
        source = _read_text_input(args)
        data = client.parse_wikitext(source, title=args.title)
        # formatversion=2 marca la existencia con "exists": false, no con
        # "missing". Una plantilla inexistente en el borrador es casi siempre
        # un error de tipeo, y es exactamente lo que este comando existe para
        # cazar antes de que quede en el historial.
        warnings = data.get("warnings") or []
        templates = data.get("templates", []) or []
        faltantes = [t for t in templates if t.get("exists") is False]
        redlinks = [ln.get("title") for ln in data.get("links", []) or []
                    if ln.get("exists") is False and ln.get("ns") == 0]
        print(f"OK: el wikitexto parsea ({len(source)} caracteres).")
        if warnings:
            print("\nAdvertencias del parser:")
            for w in (warnings if isinstance(warnings, list) else [warnings]):
                print(f"  - {w}")
        if templates:
            print(f"\nPlantillas invocadas ({len(templates)}):")
            for t in templates:
                mark = "   <-- NO EXISTE" if t.get("exists") is False else ""
                print(f"  - {t.get('title')}{mark}")
        if redlinks:
            print(f"\nEnlaces a paginas inexistentes ({len(redlinks)}):")
            for ln in redlinks[:30]:
                print(f"  - {ln}")
        cats = [c.get("category") for c in data.get("categories", []) or []]
        if cats:
            print(f"\nCategorias: {', '.join(cats)}")
        if faltantes or redlinks:
            print("\nRevisa lo anterior antes de guardar: cada plantilla inexistente "
                  "se renderiza como un enlace rojo en la pagina publicada.")
        if args.html:
            print("\n--- HTML renderizado ---")
            print(data.get("text", ""))

    elif args.cmd == "siteinfo":
        data = client.siteinfo()
        general = data.get("general", {})
        print(f"sitio:      {general.get('sitename')} ({general.get('server')})")
        print(f"generador:  {general.get('generator')}")
        print(f"idioma:     {general.get('lang')}")
        stats = data.get("statistics", {})
        if stats:
            print(f"paginas:    {stats.get('pages')} ({stats.get('articles')} articulos), "
                  f"{stats.get('images')} archivos, {stats.get('users')} usuarios")
        print("\nextensiones:")
        for ext in sorted(data.get("extensions", []), key=lambda e: e.get("name", "")):
            ver = ext.get("version", "")
            print(f"  {ext.get('name', '?')}" + (f"  {ver}" if ver else ""))

    elif args.cmd == "whoami":
        info = client.whoami()
        print(f"usuario:  {info.get('name')}")
        print(f"id:       {info.get('id')}")
        print(f"ediciones:{info.get('editcount')}")
        print(f"grupos:   {', '.join(info.get('groups', []))}")
        if info.get("blockedby"):
            print(f"BLOQUEADO por {info['blockedby']}: {info.get('blockreason')}")
        rights = set(info.get("rights", []))
        interesting = ["read", "edit", "createpage", "move", "upload",
                       "reupload", "delete", "undelete", "protect", "apihighlimits"]
        print("permisos: " + ", ".join(
            f"{r}{'' if r in rights else ' (NO)'}" for r in interesting))

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

    elif args.cmd == "upload-from-url":
        require_confirmation(
            args.as_name, f"subir {args.url} descargandolo del lado del servidor",
            args.confirm,
        )
        result = client.upload_from_url(args.url, args.as_name,
                                        comment=args.comment, text=args.text,
                                        ignorewarnings=args.ignorewarnings)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "undelete":
        require_confirmation(
            args.title, f"restaurar pagina borrada (motivo: {args.reason})",
            args.confirm,
        )
        result = client.undelete(args.title, reason=args.reason)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "purge":
        require_confirmation(
            ", ".join(args.titles),
            f"purgar la cache de {len(args.titles)} pagina(s)"
            + ("" if args.no_linkupdate else " y recalcular enlaces"),
            args.confirm,
        )
        result = client.purge(args.titles, forcelinkupdate=not args.no_linkupdate)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
