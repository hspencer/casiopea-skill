#!/usr/bin/env python3
# casiopea_mcp.py
#
# Servidor MCP (Model Context Protocol) sobre stdio que expone la wiki
# Casiopea como herramientas, para clientes que hablan MCP y no ejecutan
# scripts: Claude Desktop, Cursor, LM Studio, Zed, Codex, VS Code.
#
# Reusa `casiopea.py` como biblioteca: toda la logica de red, credenciales,
# reintentos, taxonomia de errores y salvaguardas de escritura vive alli y no
# se duplica. Este archivo es solo la capa de protocolo.
#
# Sin dependencias externas. JSON-RPC 2.0 sobre stdin/stdout, un mensaje por
# linea (framing de MCP stdio).
#
# Uso:
#   python casiopea_mcp.py
#
# Declaracion tipica en un cliente MCP:
#   {
#     "mcpServers": {
#       "casiopea": {
#         "command": "python3",
#         "args": ["/ruta/a/skills/casiopea/scripts/casiopea_mcp.py"],
#         "env": { "CASIOPEA_CREDENTIALS": "/ruta/a/credentials" }
#       }
#     }
#   }
#
# Doctrina de escritura, identica a la del CLI: ninguna herramienta que
# modifique la wiki actua sin `confirm: true`. Sin esa bandera devuelve el
# diff de lo que haria y no toca nada. La aprobacion de herramientas del
# cliente MCP es una segunda reja, no la primera.

import json
import os
import sys
import traceback
import urllib.parse
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import casiopea as cw  # noqa: E402

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "casiopea"

# Ruta a las referencias del skill. Se exponen como recursos MCP para que un
# cliente pueda cargar la doctrina grafica de Stella Nova sin que el agente
# tenga que adivinarla ni salir a buscarla a la web.
REFERENCES_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references")
)

RESOURCES = [
    ("casiopea://doctrina/stella-nova", "stella-nova.md",
     "Doctrina grafica de Stella Nova",
     "Tokens semanticos, clases opt-in del skin, grilla, palabras magicas y "
     "las reglas del sanitizador de TemplateStyles. Cargar antes de escribir "
     "CSS o maquetar una pagina."),
    ("casiopea://doctrina/inventario", "stella-nova-inventario.md",
     "Inventario de tokens de Stella Nova",
     "Lista generada de todos los tokens declarados en tokens.css, por capa, "
     "con su valor. Regenerable con `casiopea.py sn-sync`."),
    ("casiopea://doctrina/recetas-diseno", "recetas-diseno.md",
     "Recetas de maquetacion",
     "Patrones de wikitexto listos para adaptar: portada a sangre, galeria, "
     "ficha, listado semantico en tarjetas, plantilla con TemplateStyles."),
    ("casiopea://esquema/clases", "esquema-casiopea.md",
     "Esquema semantico de Casiopea",
     "Las 22 clases ontologicas core con sus propiedades, campos de formulario "
     "y queries de ejemplo."),
    ("casiopea://recetas/consultas", "recetas.md",
     "Recetas de consulta SMW",
     "Queries #ask listas para usar y flujo de auditoria de plantillas."),
    ("casiopea://api/mediawiki", "mediawiki-api.md",
     "Detalles de la API de MediaWiki y SMW",
     "Parametros completos de cada accion y errores comunes."),
]


# -----------------------------------------------------------------------------
# Clientes perezosos, uno por wiki
# -----------------------------------------------------------------------------

_clients: dict[str, cw.CasiopeaClient] = {}


def available_wikis() -> list[str]:
    """
    Wikis con credenciales en esta instalacion. Casi siempre solo 'prod'; el
    espejo local aparece unicamente si alguien configuro CASIOPEA_LOCAL_*.
    """
    return cw.configured_wikis() or ["prod"]


def default_wiki() -> str:
    """
    Wiki a la que va una llamada que no dice cual.

    CASIOPEA_DEFAULT_WIKI permite que quien tiene espejo local trabaje contra
    el por defecto y vaya a produccion solo cuando lo pide explicitamente. Si
    esa wiki no tiene credenciales, se cae a la primera configurada.
    """
    wikis = available_wikis()
    wanted = cw.canonical_wiki(os.environ.get("CASIOPEA_DEFAULT_WIKI") or wikis[0])
    return wanted if wanted in wikis else wikis[0]


def client(wiki: str | None = None) -> cw.CasiopeaClient:
    """
    Devuelve el cliente autenticado de una wiki, creandolo en la primera
    llamada.

    Es perezoso a proposito: un cliente MCP arranca el servidor al abrir la
    aplicacion, mucho antes de que nadie pida nada. Hacer login en ese momento
    gastaria una sesion por cada arranque y fallaria ruidosamente en maquinas
    donde las credenciales aun no estan puestas.
    """
    w = cw.canonical_wiki(wiki) if wiki else default_wiki()
    if w not in _clients:
        api_url, user, password = cw.load_credentials(w)
        c = cw.CasiopeaClient(api_url, user, password, wiki=w)
        c.login()
        _clients[w] = c
    return _clients[w]


def forget_client(wiki: str | None) -> None:
    """Descarta la sesion de una wiki para forzar un login nuevo (sesion vencida)."""
    w = cw.canonical_wiki(wiki) if wiki else default_wiki()
    _clients.pop(w, None)


# -----------------------------------------------------------------------------
# Definicion de herramientas
#
# Convenciones seguidas (tomadas de docs/tool-conventions.md del MediaWiki MCP
# Server de Professional Wiki):
#   · un trabajo por herramienta, nombres verbo-sustantivo en kebab-case;
#   · descripcion en tercera persona que dice QUE hace y QUE devuelve;
#   · desambiguacion explicita entre hermanas que se parecen;
#   · las cuatro anotaciones de comportamiento siempre declaradas, porque hay
#     clientes que rechazan la herramienta si falta alguna;
#   · nada de imperativos al modelo ("debes llamar a..."): se describe la
#     condicion en que la herramienta es la adecuada y decide el modelo.
# -----------------------------------------------------------------------------

def _s(desc: str, **extra) -> dict:
    out = {"type": "string", "description": desc}
    out.update(extra)
    return out


def _i(desc: str, **extra) -> dict:
    out = {"type": "integer", "description": desc}
    out.update(extra)
    return out


def _b(desc: str, default: bool = False) -> dict:
    return {"type": "boolean", "description": desc, "default": default}


RO = {"readOnlyHint": True, "destructiveHint": False,
      "idempotentHint": True, "openWorldHint": True}
ADD = {"readOnlyHint": False, "destructiveHint": False,
       "idempotentHint": False, "openWorldHint": True}
DESTR = {"readOnlyHint": False, "destructiveHint": True,
         "idempotentHint": False, "openWorldHint": True}

CONFIRM = _b("Ejecuta el cambio de verdad. Sin esto la herramienta devuelve el "
             "diff de lo que haria y la wiki queda intacta.", False)

TOOLS: list[dict[str, Any]] = [
    # ---------------------------------------------------------------- lectura
    {
        "name": "search-pages",
        "title": "Buscar paginas",
        "description": "Busca un termino en el contenido de las paginas de Casiopea y "
                       "devuelve titulos con fragmentos de contexto. Para resolver un "
                       "titulo del que solo se conoce el comienzo, o para enumerar un "
                       "arbol de subpaginas, usar search-by-prefix.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["term"], "properties": {
            "term": _s("Termino de busqueda full-text."),
            "limit": _i("Total de resultados; se pagina automaticamente.", default=20),
        }},
    },
    {
        "name": "search-by-prefix",
        "title": "Buscar titulos por prefijo",
        "description": "Devuelve titulos que empiezan con un prefijo dado. Solo mira "
                       "titulos, no contenido. Con un prefijo terminado en barra "
                       "enumera las subpaginas de una pagina. Para buscar en el texto, "
                       "usar search-pages.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["prefix"], "properties": {
            "prefix": _s("Comienzo del titulo, por ejemplo 'Stella Nova/'."),
            "namespace": _i("Restringe a un namespace: 10 Plantilla, 102 Propiedad, "
                            "14 Categoria."),
            "limit": _i("Maximo de titulos.", default=20),
        }},
    },
    {
        "name": "get-page",
        "title": "Traer una pagina",
        "description": "Devuelve el wikitexto de una pagina. Con section devuelve solo "
                       "esa seccion. El contenido se trunca a 50000 bytes por defecto y "
                       "el resultado indica las secciones disponibles para volver a "
                       "pedir la parte que interese. Para varias paginas de una vez, "
                       "usar get-pages; para una version historica, get-revision.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["title"], "properties": {
            "title": _s("Titulo exacto, con prefijo de namespace si corresponde."),
            "section": _s("Numero de seccion: 0 es el encabezado, 1..N las secciones."),
            "maxBytes": _i("Presupuesto de bytes antes de truncar.", default=50000),
            "metadata": _b("Antepone la revision vigente (latestRevisionId) y su fecha. "
                           "Ese numero se pasa despues como latestId a update-page o "
                           "find-replace para detectar ediciones ajenas."),
        }},
    },
    {
        "name": "get-pages",
        "title": "Traer varias paginas",
        "description": "Devuelve el wikitexto de hasta 50 paginas en una sola llamada. "
                       "Un titulo inexistente se marca como tal sin invalidar el resto "
                       "del lote. Para una sola pagina con control de secciones, usar "
                       "get-page.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["titles"], "properties": {
            "titles": {"type": "array", "items": {"type": "string"},
                       "description": "Hasta 50 titulos exactos.", "maxItems": 50},
            "maxBytes": _i("Presupuesto de bytes por pagina.", default=20000),
        }},
    },
    {
        "name": "get-page-sections",
        "title": "Indice de secciones",
        "description": "Devuelve el indice de secciones de una pagina con su numero, "
                       "nivel y titulo. Sirve para navegar una pagina larga sin "
                       "traerla entera: el numero se pasa despues a get-page.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["title"], "properties": {
            "title": _s("Titulo exacto."),
        }},
    },
    {
        "name": "get-revision",
        "title": "Traer una revision",
        "description": "Devuelve el contenido y los metadatos de una revision "
                       "historica por su identificador. Sirve para recuperar la version "
                       "anterior de una plantilla que se rompio. Para la lista de "
                       "revisiones, usar get-page-history.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["revid"], "properties": {
            "revid": _i("Identificador numerico de revision."),
        }},
    },
    {
        "name": "get-page-history",
        "title": "Historial de una pagina",
        "description": "Lista las revisiones de una pagina, de la mas nueva a la mas "
                       "vieja, con fecha, autor, tamano y resumen de edicion. Devuelve "
                       "metadatos, no contenido: para el texto de una revision usar "
                       "get-revision.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["title"], "properties": {
            "title": _s("Titulo exacto."),
            "limit": _i("Cuantas revisiones traer.", default=20),
        }},
    },
    {
        "name": "compare-revisions",
        "title": "Comparar revisiones",
        "description": "Calcula el diff entre dos revisiones o dos paginas y lo "
                       "devuelve en formato unificado. Cada extremo acepta un "
                       "identificador numerico de revision o un titulo. El calculo lo "
                       "hace el servidor, asi que devuelve menos texto que traer ambas "
                       "versiones y compararlas.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["from", "to"], "properties": {
            "from": _s("Revision o titulo de partida."),
            "to": _s("Revision o titulo de llegada."),
        }},
    },
    {
        "name": "get-category-members",
        "title": "Paginas de una categoria",
        "description": "Lista las paginas de una categoria, paginando hasta el limite "
                       "pedido. Acepta el nombre con o sin prefijo. El resultado avisa "
                       "si se alcanzo el tope y podria haber mas.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["category"], "properties": {
            "category": _s("Nombre de la categoria, con o sin prefijo 'Categoría:'."),
            "limit": _i("Tope de paginas.", default=100),
        }},
    },
    {
        "name": "get-links-here",
        "title": "Que apunta a esto",
        "description": "Lista las paginas que dependen de una pagina dada, segun el "
                       "tipo pedido: 'links' son enlaces [[X]], 'transclusions' son "
                       "usos {{X}} de una plantilla, y 'fileusage' son paginas que "
                       "muestran un archivo. Es la medida de impacto antes de "
                       "renombrar o borrar algo: cero resultados significa que no se "
                       "rompe nada.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["title"], "properties": {
            "title": _s("Titulo exacto de la pagina, plantilla o archivo."),
            "type": _s("Tipo de dependencia.", enum=["links", "transclusions", "fileusage"],
                       default="links"),
            "limit": _i("Tope de resultados.", default=500),
        }},
    },
    {
        "name": "get-recent-changes",
        "title": "Cambios recientes",
        "description": "Lista los cambios recientes de la wiki con fecha, autor, tipo, "
                       "variacion de tamano y resumen. Filtrable por namespace, "
                       "usuario y tipo de cambio, y con opcion de excluir ediciones "
                       "marcadas como de bot.",
        "annotations": RO,
        "inputSchema": {"type": "object", "properties": {
            "limit": _i("Cuantos cambios traer.", default=30),
            "namespace": _s("Identificador numerico de namespace."),
            "user": _s("Restringe a las ediciones de una cuenta."),
            "type": _s("edit, new, log o categorize; admite lista separada por comas."),
            "excludeBots": _b("Oculta las ediciones marcadas como de bot."),
        }},
    },
    {
        "name": "smw-ask",
        "title": "Consulta semantica",
        "description": "Ejecuta una consulta Semantic MediaWiki con sintaxis #ask y "
                       "devuelve los resultados como tabla, CSV o JSON, paginando por "
                       "offset hasta el maximo pedido. Casiopea tiene SMW configurado "
                       "en espanol y sus propiedades llevan tildes reales "
                       "(`[[Categoría:Travesía]][[Año::2018]]|?Colección`): un nombre "
                       "mal escrito devuelve columnas vacias sin ningun error. Para "
                       "descubrir los nombres exactos, usar smw-list-properties o "
                       "smw-browse.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["query"], "properties": {
            "query": _s("Consulta en sintaxis #ask, sin las llaves."),
            "format": _s("Formato de salida.", enum=["table", "csv", "json"],
                         default="table"),
            "max": _i("Tope total de filas al paginar.", default=500),
        }},
    },
    {
        "name": "smw-browse",
        "title": "Propiedades de una pagina",
        "description": "Devuelve todas las propiedades semanticas anotadas en una "
                       "pagina concreta. Es la forma de descubrir el esquema real de "
                       "un tipo de contenido mirando un ejemplar representativo, antes "
                       "de escribir una consulta con smw-ask.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["title"], "properties": {
            "title": _s("Titulo exacto de la pagina a inspeccionar."),
        }},
    },
    {
        "name": "smw-list-properties",
        "title": "Listar propiedades",
        "description": "Lista las propiedades semanticas declaradas en la wiki, con "
                       "filtro opcional por subcadena que ignora tildes y mayusculas. "
                       "Resuelve el error mas frecuente al consultar Casiopea: "
                       "escribir 'Coleccion' cuando la propiedad se llama 'Colección'.",
        "annotations": RO,
        "inputSchema": {"type": "object", "properties": {
            "contains": _s("Subcadena a buscar, insensible a tildes y mayusculas."),
            "limit": _i("Tope de propiedades.", default=500),
        }},
    },
    {
        "name": "parse-wikitext",
        "title": "Previsualizar wikitexto",
        "description": "Renderiza wikitexto contra la wiki real sin guardarlo, y "
                       "devuelve las advertencias del parser, las plantillas invocadas "
                       "marcando las que no existen, los enlaces a paginas "
                       "inexistentes y las categorias resultantes. Es la verificacion "
                       "previa a cualquier escritura de contenido maquetado: un "
                       "nombre de plantilla mal escrito aparece aca y no en el "
                       "historial de la wiki.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["text"], "properties": {
            "text": _s("Wikitexto a previsualizar."),
            "title": _s("Titulo de contexto; no se crea ni se modifica esa pagina.",
                        default="Previsualización"),
            "includeHtml": _b("Incluye tambien el HTML renderizado."),
        }},
    },
    {
        "name": "get-site-info",
        "title": "Informacion del sitio",
        "description": "Devuelve la version de MediaWiki, las extensiones instaladas "
                       "con su version, los namespaces y las estadisticas de la wiki. "
                       "Responde si una receta es viable en esta instalacion en vez de "
                       "suponerlo.",
        "annotations": RO,
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get-file",
        "title": "Datos de un archivo",
        "description": "Devuelve los metadatos de un archivo subido: si existe, quien "
                       "y cuando lo subio, tamano, tipo MIME, dimensiones y las URLs del "
                       "original y de su pagina. Sirve para comprobar una imagen antes "
                       "de usarla en una ficha, o antes de pasar una pagina de una wiki "
                       "a otra. Para ver la imagen, usar get-file-data.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["title"], "properties": {
            "title": _s("Nombre del archivo, con o sin prefijo 'Archivo:'."),
        }},
    },
    {
        "name": "get-file-data",
        "title": "Ver un archivo",
        "description": "Descarga una version escalada de un archivo y la devuelve como "
                       "imagen para mirarla. La wiki rasteriza imagenes, SVG y PDF; otros "
                       "tipos fallan. Para metadatos o la URL, usar get-file.",
        "annotations": RO,
        "inputSchema": {"type": "object", "required": ["title"], "properties": {
            "title": _s("Nombre del archivo, con o sin prefijo 'Archivo:'."),
            "width": _i("Ancho en pixeles de la version escalada.", default=1024),
        }},
    },
    {
        "name": "whoami",
        "title": "Quien soy",
        "description": "Devuelve la identidad con la que esta autenticada la sesion: "
                       "cuenta, grupos, numero de ediciones y permisos efectivos. "
                       "Comprobar los permisos antes de una tanda de escrituras es mas "
                       "barato que descubrir a mitad de camino que falta un grant.",
        "annotations": RO,
        "inputSchema": {"type": "object", "properties": {}},
    },

    # -------------------------------------------------------------- escritura
    {
        "name": "update-page",
        "title": "Actualizar pagina",
        "description": "Reemplaza el contenido de una pagina existente; falla si la "
                       "pagina no existe. Sin confirm devuelve el diff unificado y la "
                       "revision base, y no modifica nada. Con latestId rechaza la "
                       "escritura si alguien edito la pagina despues de esa revision. "
                       "La edicion queda registrada como bot, atribuida a la cuenta "
                       "duena del bot password. Para cambiar solo un fragmento, usar "
                       "find-replace; para agregar al final, append-to-page; para una "
                       "pagina nueva, create-page.",
        "annotations": DESTR,
        "inputSchema": {"type": "object", "required": ["title", "text"], "properties": {
            "title": _s("Titulo exacto de la pagina a reemplazar."),
            "text": _s("Wikitexto completo que reemplaza al actual."),
            "summary": _s("Resumen de edicion que vera quien lea el historial.",
                          default="Edicion via casiopea MCP"),
            "section": _s("Limita el reemplazo a una seccion."),
            "latestId": _i("Revision sobre la que se preparo el cambio (la da get-page "
                           "con metadata, o el ensayo). Si la pagina cambio desde "
                           "entonces, la escritura se rechaza con conflict."),
            "confirm": CONFIRM,
        }},
    },
    {
        "name": "find-replace",
        "title": "Reemplazar un fragmento",
        "description": "Cambia un fragmento exacto de una pagina y deja el resto byte "
                       "por byte, sin reenviar la pagina entera. El fragmento debe "
                       "aparecer una sola vez (en la pagina o en la seccion pedida): si "
                       "no aparece o aparece varias veces, no escribe nada y pide "
                       "ampliarlo. Sin confirm devuelve el diff. Es la forma segura de "
                       "tocar una plantilla grande. Para reescribir todo, update-page.",
        "annotations": DESTR,
        "inputSchema": {"type": "object", "required": ["title", "find", "replace"],
                        "properties": {
            "title": _s("Titulo exacto."),
            "find": _s("Texto exacto a buscar, espacios y saltos de linea incluidos."),
            "replace": _s("Texto que lo reemplaza; vacio borra el fragmento."),
            "section": _s("Buscar solo dentro de esta seccion."),
            "summary": _s("Resumen de edicion.", default="Edicion via casiopea MCP"),
            "latestId": _i("Revision base; si la pagina cambio desde entonces, se "
                           "rechaza con conflict."),
            "confirm": CONFIRM,
        }},
    },
    {
        "name": "append-to-page",
        "title": "Anadir al final",
        "description": "Anade wikitexto al final de una pagina conservando lo que ya "
                       "estaba. Sin confirm devuelve el diff y no modifica nada. Para "
                       "reemplazar el contenido completo, usar update-page.",
        "annotations": ADD,
        "inputSchema": {"type": "object", "required": ["title", "text"], "properties": {
            "title": _s("Titulo exacto."),
            "text": _s("Wikitexto a anadir al final."),
            "summary": _s("Resumen de edicion.", default="Adicion via casiopea MCP"),
            "confirm": CONFIRM,
        }},
    },
    {
        "name": "create-page",
        "title": "Crear pagina",
        "description": "Crea una pagina nueva. Falla si el titulo ya existe, en vez de "
                       "sobreescribirlo. Sin confirm devuelve el contenido propuesto y "
                       "avisa si el titulo esta ocupado. Para modificar una pagina "
                       "existente, usar update-page.",
        "annotations": ADD,
        "inputSchema": {"type": "object", "required": ["title", "text"], "properties": {
            "title": _s("Titulo de la pagina nueva."),
            "text": _s("Wikitexto inicial."),
            "summary": _s("Resumen de edicion.", default="Creacion via casiopea MCP"),
            "confirm": CONFIRM,
        }},
    },
    {
        "name": "move-page",
        "title": "Mover pagina",
        "description": "Renombra una pagina. Por defecto deja un redirect en el titulo "
                       "viejo, de modo que los enlaces existentes siguen funcionando, y "
                       "arrastra la pagina de discusion. Antes de mover una plantilla o "
                       "un archivo conviene medir el impacto con get-links-here.",
        "annotations": DESTR,
        "inputSchema": {"type": "object", "required": ["from", "to"], "properties": {
            "from": _s("Titulo actual."),
            "to": _s("Titulo nuevo."),
            "reason": _s("Motivo que queda en el registro de movimientos.",
                         default="Normalizacion via casiopea MCP"),
            "leaveRedirect": _b("Deja un redirect en el titulo viejo.", True),
            "confirm": CONFIRM,
        }},
    },
    {
        "name": "delete-page",
        "title": "Borrar pagina",
        "description": "Borra una pagina. El contenido queda archivado y es "
                       "recuperable con undelete-page mientras la wiki no purgue el "
                       "archivo. Requiere que el bot password tenga el grant de "
                       "borrado. Antes de borrar una plantilla o un archivo conviene "
                       "medir el impacto con get-links-here.",
        "annotations": DESTR,
        "inputSchema": {"type": "object", "required": ["title"], "properties": {
            "title": _s("Titulo exacto de la pagina a borrar."),
            "reason": _s("Motivo que queda en el registro de borrados.",
                         default="Limpieza via casiopea MCP"),
            "confirm": CONFIRM,
        }},
    },
    {
        "name": "undelete-page",
        "title": "Restaurar pagina",
        "description": "Restaura una pagina borrada con todas sus revisiones "
                       "archivadas. Es la contraparte de delete-page y requiere el "
                       "mismo grant.",
        "annotations": ADD,
        "inputSchema": {"type": "object", "required": ["title"], "properties": {
            "title": _s("Titulo exacto de la pagina a restaurar."),
            "reason": _s("Motivo del registro.", default="Restauracion via casiopea MCP"),
            "confirm": CONFIRM,
        }},
    },
    {
        "name": "purge-pages",
        "title": "Purgar cache",
        "description": "Fuerza a MediaWiki a re-renderizar una o varias paginas y a "
                       "recalcular sus enlaces y anotaciones semanticas. Necesario "
                       "despues de editar una plantilla o su hoja de estilos: las "
                       "paginas que la transcluyen siguen sirviendo la version "
                       "cacheada. No cambia contenido.",
        "annotations": {"readOnlyHint": False, "destructiveHint": False,
                        "idempotentHint": True, "openWorldHint": True},
        "inputSchema": {"type": "object", "required": ["titles"], "properties": {
            "titles": {"type": "array", "items": {"type": "string"},
                       "description": "Titulos a purgar."},
            "confirm": CONFIRM,
        }},
    },
    {
        "name": "upload-file",
        "title": "Subir archivo",
        "description": "Sube un archivo desde el disco local a la wiki, partiendolo en "
                       "trozos automaticamente si pesa mas de 8 MB. Para un original "
                       "que ya esta publicado en linea, usar upload-file-from-url y "
                       "ahorrar el viaje de ida y vuelta.",
        "annotations": ADD,
        "inputSchema": {"type": "object", "required": ["path"], "properties": {
            "path": _s("Ruta del archivo en el disco de esta maquina."),
            "filename": _s("Nombre con el que quedara en la wiki; por defecto el del "
                           "archivo."),
            "comment": _s("Comentario de subida.", default="Upload via casiopea MCP"),
            "text": _s("Wikitexto inicial de la pagina de archivo."),
            "confirm": CONFIRM,
        }},
    },
    {
        "name": "upload-file-from-url",
        "title": "Subir archivo desde URL",
        "description": "Sube un archivo haciendo que el servidor de la wiki lo "
                       "descargue de una direccion publica. Requiere que la wiki "
                       "permita copy-uploads y tenga el dominio de origen autorizado; "
                       "si no, hay que bajar el archivo y usar upload-file.",
        "annotations": ADD,
        "inputSchema": {"type": "object", "required": ["url", "filename"], "properties": {
            "url": _s("Direccion publica del archivo."),
            "filename": _s("Nombre con el que quedara en la wiki."),
            "comment": _s("Comentario de subida.", default="Upload via casiopea MCP"),
            "text": _s("Wikitexto inicial de la pagina de archivo."),
            "confirm": CONFIRM,
        }},
    },
]


def tools_for_session() -> list[dict[str, Any]]:
    """
    Lista de herramientas tal como se anuncia al cliente.

    Si la instalacion solo tiene produccion (el caso de casi todos), las
    herramientas se anuncian tal cual, sin parametro de wiki. Si ademas hay un
    espejo configurado, cada herramienta gana un parametro `wiki` con las
    opciones disponibles y la wiki por defecto: asi el modelo no ve una opcion
    que en esa maquina no funciona.
    """
    wikis = available_wikis()
    if len(wikis) < 2:
        return TOOLS
    dflt = default_wiki()
    desc = ("Wiki destino: 'prod' es https://wiki.ead.pucv.cl y 'local' el espejo "
            f"de desarrollo en http://casiopea.local. Por defecto, '{dflt}'.")
    out = []
    for tool in TOOLS:
        t = json.loads(json.dumps(tool))
        t["inputSchema"].setdefault("properties", {})["wiki"] = _s(
            desc, enum=wikis, default=dflt)
        out.append(t)
    return out


# -----------------------------------------------------------------------------
# Ejecucion de herramientas
# -----------------------------------------------------------------------------

def _truncate(text: str, max_bytes: int, note: str) -> str:
    """Recorta al presupuesto de bytes dejando constancia de que se recorto."""
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        return text
    return (raw[:max_bytes].decode("utf-8", errors="ignore")
            + f"\n\n[truncado en {max_bytes} de {len(raw)} bytes. {note}]")


def _dry_run(c: cw.CasiopeaClient, title: str, accion: str,
             diff: str | None = None) -> str:
    """Texto uniforme del ensayo previo, con la wiki destino y el diff cuando lo hay."""
    out = ["ENSAYO: no se modifico nada en la wiki.",
           f"  Wiki: {c.wiki} ({c.api_url.rsplit('/', 1)[0]})",
           f"  Pagina: {title}",
           f"  Operacion: {accion}"]
    if diff:
        out += ["", diff, ""]
    out.append("Para ejecutarlo de verdad, repetir la llamada con confirm: true. "
               "La edicion quedara firmada con la cuenta duena del bot password.")
    return "\n".join(out)


def _write_result(c: cw.CasiopeaClient, res: dict[str, Any]) -> str:
    """Resultado de una edicion, rotulado con la wiki y la URL de la pagina."""
    title = res.get("title", "")
    base = c.api_url.rsplit("/", 1)[0]
    url = f"{base}/index.php?title={urllib.parse.quote(title.replace(' ', '_'))}"
    head = (f"Guardado en {c.wiki}: {title} · r{res.get('newrevid', res.get('oldrevid', '?'))}"
            + (" (sin cambios)" if res.get("nochange") else "") + f"\n{url}\n\n")
    return head + json.dumps(res, ensure_ascii=False)


def call_tool(name: str, args: dict[str, Any]) -> str | list[dict[str, Any]]:
    """
    Despacha una llamada de herramienta y devuelve texto plano.

    Toda herramienta devuelve texto, no JSON estructurado, salvo donde el JSON
    ES el resultado util (smw-browse, smw-ask con format json). Es deliberado:
    el consumidor es un modelo de lenguaje, y el texto tabulado se lee mejor y
    gasta menos tokens que un objeto anidado. La excepcion es get-file-data,
    que devuelve bloques de contenido (una imagen) en vez de texto.
    """
    c = client(args.get("wiki"))

    if name == "search-pages":
        rs = c.search(args["term"], limit=args.get("limit", 20))
        if not rs:
            return "Sin resultados."
        return "\n".join(f"{r['title']}\n    {r.get('snippet', '').strip()}" for r in rs)

    if name == "search-by-prefix":
        titles = c.prefix_search(args["prefix"], args.get("namespace"),
                                 args.get("limit", 20))
        return "\n".join(titles) or "Sin resultados."

    if name == "get-page":
        head = ""
        if args.get("metadata"):
            meta = c.page_meta(args["title"])
            if not meta["exists"]:
                raise cw.CasiopeaError("not_found", f"la pagina '{args['title']}' no existe en {c.wiki}.")
            head = (f"latestRevisionId: {meta['revid']}\n"
                    f"timestamp: {meta['timestamp']}\nwiki: {c.wiki}\n\n")
        if args.get("section") is not None:
            return head + (c.page_section(args["title"], str(args["section"]))
                           or "(seccion vacia)")
        text = c.page(args["title"])
        if not text:
            raise cw.CasiopeaError("not_found", f"la pagina '{args['title']}' no existe o esta vacia en {c.wiki}.")
        max_bytes = args.get("maxBytes", 50000)
        if len(text.encode("utf-8")) > max_bytes:
            secs = c.sections(args["title"])
            listado = ", ".join(f"{s.get('index')} ({s.get('line', '').strip()})"
                                for s in secs[:40] if s.get("index"))
            return head + _truncate(text, max_bytes,
                                    f"Secciones: 0 (encabezado), {listado}. "
                                    "Volver a llamar con section=N para una en concreto.")
        return head + text

    if name == "get-pages":
        res = c.pages(args["titles"])
        max_bytes = args.get("maxBytes", 20000)
        chunks = []
        for title, content in res.items():
            if content is None:
                chunks.append(f"===== {title} =====\n(no existe)")
            else:
                chunks.append(f"===== {title} =====\n"
                              + _truncate(content, max_bytes,
                                          "Usar get-page para el texto completo."))
        return "\n\n".join(chunks)

    if name == "get-page-sections":
        secs = c.sections(args["title"])
        if not secs:
            return "La pagina no tiene secciones."
        return "\n".join(f"{s.get('index', ''):>4}  h{s.get('level', '?')}  "
                         f"{s.get('line', '')}" for s in secs)

    if name == "get-revision":
        rev = c.revision(int(args["revid"]))
        head = (f"{rev['title']} · r{rev['revid']} · {rev['timestamp']} · "
                f"{rev['user']}\n{(rev.get('comment') or '').strip()}\n")
        return head + "\n" + _truncate(rev["content"], 50000, "")

    if name == "get-page-history":
        revs = c.history(args["title"], limit=args.get("limit", 20))
        if not revs:
            raise cw.CasiopeaError("not_found", f"sin historial para '{args['title']}'.")
        return "\n".join(
            f"{r.get('timestamp')}  r{r.get('revid')}  {r.get('user')}  "
            f"({r.get('size')}b)  {(r.get('comment') or '').strip()}" for r in revs)

    if name == "compare-revisions":
        import html
        import re
        body = c.compare(str(args["from"]), str(args["to"]))
        if not body.strip():
            return "Sin diferencias."
        text = re.sub(r"</tr\s*>", "\n", body)
        return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()

    if name == "get-category-members":
        limit = args.get("limit", 100)
        items = c.category(args["category"], limit=limit)
        out = "\n".join(items) or "Categoria vacia o inexistente."
        if len(items) >= limit:
            out += f"\n\n[tope de {limit} alcanzado; puede haber mas]"
        return out

    if name == "get-links-here":
        kind = args.get("type", "links")
        limit = args.get("limit", 500)
        fn = {"links": c.backlinks, "transclusions": c.transclusions,
              "fileusage": c.fileusage}[kind]
        items = fn(args["title"], limit=limit)
        if not items:
            return (f"Ninguna pagina depende de '{args['title']}' por {kind}. "
                    "Renombrarla o borrarla no rompe nada.")
        out = f"{len(items)} pagina(s) dependen de '{args['title']}' ({kind}):\n"
        out += "\n".join(items)
        if len(items) >= limit:
            out += f"\n\n[tope de {limit} alcanzado; puede haber mas]"
        return out

    if name == "get-recent-changes":
        changes = c.recentchanges(
            limit=args.get("limit", 30), namespace=args.get("namespace"),
            user=args.get("user"), rctype=args.get("type"),
            bots=not args.get("excludeBots", False))
        lines = []
        for ch in changes:
            delta = ch.get("newlen", 0) - ch.get("oldlen", 0)
            sign = f"+{delta}" if delta >= 0 else str(delta)
            lines.append(f"{ch.get('timestamp')}  {ch.get('type', ''):<5}  "
                         f"{ch.get('user')}  ({sign})  {ch.get('title')}  "
                         f"{(ch.get('comment') or '').strip()}")
        return "\n".join(lines) or "Sin cambios en el rango consultado."

    if name == "smw-ask":
        data = c.ask(args["query"], max_results=args.get("max", 500))
        if not data.get("results"):
            return ("La consulta no devolvio filas. Si esperabas resultados, revisa "
                    "los nombres de propiedad con smw-list-properties: en Casiopea "
                    "llevan tildes reales y un nombre mal escrito devuelve vacio "
                    "sin error.")
        return cw.format_ask_results(data, args.get("format", "table"))

    if name == "smw-browse":
        return json.dumps(c.browse(args["title"]), indent=2, ensure_ascii=False)

    if name == "smw-list-properties":
        props = c.smw_properties(limit=args.get("limit", 500))
        if args.get("contains"):
            import unicodedata

            def flat(s: str) -> str:
                return "".join(ch for ch in unicodedata.normalize("NFD", s.lower())
                               if unicodedata.category(ch) != "Mn")

            needle = flat(args["contains"])
            props = [p for p in props if needle in flat(p)]
        return "\n".join(props) or "Ninguna propiedad coincide."

    if name == "parse-wikitext":
        data = c.parse_wikitext(args["text"], title=args.get("title", "Previsualización"))
        templates = data.get("templates", []) or []
        faltan = [t.get("title") for t in templates if t.get("exists") is False]
        redlinks = [ln.get("title") for ln in data.get("links", []) or []
                    if ln.get("exists") is False and ln.get("ns") == 0]
        cats = [x.get("category") for x in data.get("categories", []) or []]
        out = [f"El wikitexto parsea ({len(args['text'])} caracteres)."]
        if data.get("warnings"):
            out.append(f"Advertencias del parser: {data['warnings']}")
        if templates:
            out.append("Plantillas invocadas: " + ", ".join(
                f"{t.get('title')}{' [NO EXISTE]' if t.get('exists') is False else ''}"
                for t in templates))
        if redlinks:
            out.append("Enlaces a paginas inexistentes: " + ", ".join(redlinks[:30]))
        if cats:
            out.append("Categorias: " + ", ".join(cats))
        if faltan or redlinks:
            out.append("Conviene resolver lo anterior antes de guardar: cada nombre "
                       "inexistente se publica como enlace rojo.")
        if args.get("includeHtml"):
            out.append("\n--- HTML ---\n" + _truncate(data.get("text", ""), 30000, ""))
        return "\n".join(out)

    if name == "get-site-info":
        data = c.siteinfo()
        g = data.get("general", {})
        st = data.get("statistics", {})
        exts = sorted(f"{e.get('name')} {e.get('version', '')}".strip()
                      for e in data.get("extensions", []))
        return (f"{g.get('sitename')} — {g.get('server')}\n"
                f"{g.get('generator')} · idioma {g.get('lang')}\n"
                f"{st.get('pages')} paginas ({st.get('articles')} articulos), "
                f"{st.get('images')} archivos, {st.get('users')} usuarios\n\n"
                "Extensiones:\n" + "\n".join(f"  {e}" for e in exts))

    if name == "whoami":
        info = c.whoami()
        rights = set(info.get("rights", []))
        interesting = ["read", "edit", "createpage", "move", "upload", "delete",
                       "undelete", "protect", "apihighlimits"]
        return (f"Cuenta: {info.get('name')} (id {info.get('id')})\n"
                f"Ediciones: {info.get('editcount')}\n"
                f"Grupos: {', '.join(info.get('groups', []))}\n"
                + (f"BLOQUEADA por {info['blockedby']}\n" if info.get("blockedby") else "")
                + "Permisos: " + ", ".join(
                    f"{r}{'' if r in rights else ' (NO)'}" for r in interesting))

    # ------------------------------------------------------------- escrituras
    if name == "update-page":
        meta = c.check_base(args["title"], args.get("latestId"))
        if not meta["exists"]:
            raise cw.CasiopeaError("not_found", f"la pagina '{args['title']}' no existe en {c.wiki}. "
                    "Para crearla, usar create-page.")
        if not args.get("confirm"):
            diff = (None if args.get("section")
                    else cw._unified_diff(meta["content"], args["text"], args["title"]))
            return _dry_run(c, args["title"],
                            f"reemplazar contenido ({len(args['text'])} caracteres) "
                            f"sobre r{meta['revid']}; confirmar con latestId: "
                            f"{meta['revid']}", diff)
        res = c.edit(args["title"], text=args["text"], section=args.get("section"),
                     summary=args.get("summary", "Edicion via casiopea MCP"),
                     nocreate=True, baserevid=meta["revid"],
                     basetimestamp=meta["timestamp"])
        return _write_result(c, res)

    if name == "find-replace":
        meta = c.check_base(args["title"], args.get("latestId"))
        if not meta["exists"]:
            raise cw.CasiopeaError("not_found", f"la pagina '{args['title']}' no existe en {c.wiki}.")
        section = args.get("section")
        target = (c.page_section(args["title"], str(section))
                  if section is not None else meta["content"])
        proposed = cw.apply_find_replace(target, args["find"], args.get("replace", ""))
        if not args.get("confirm"):
            return _dry_run(c, args["title"],
                            f"reemplazar un fragmento sobre r{meta['revid']}; confirmar "
                            f"con latestId: {meta['revid']}",
                            cw._unified_diff(target, proposed, args["title"]))
        res = c.edit(args["title"], text=proposed,
                     section=str(section) if section is not None else None,
                     summary=args.get("summary", "Edicion via casiopea MCP"),
                     nocreate=True, baserevid=meta["revid"],
                     basetimestamp=meta["timestamp"])
        return _write_result(c, res)

    if name == "get-file":
        info = c.file_info(args["title"])
        if not info.get("exists"):
            raise cw.CasiopeaError("not_found", f"no existe {info['title']} en {c.wiki}. El espejo local "
                    "no tiene los binarios de produccion: un archivo puede estar en una "
                    "wiki y no en la otra.")
        keys = ["title", "user", "timestamp", "size", "width", "height", "mime",
                "url", "descriptionurl", "comment"]
        return "\n".join(f"{k}: {info.get(k)}" for k in keys if info.get(k) is not None)

    if name == "get-file-data":
        import base64
        width = min(int(args.get("width", 1024)), 1568)
        data, mime, info = c.file_bytes(args["title"], width=width)
        if not mime.startswith("image/"):
            raise cw.CasiopeaError("invalid_input", f"{info['title']} es {mime}; no se puede mostrar como "
                    "imagen. Usar get-file para su URL.")
        return [
            {"type": "image", "data": base64.b64encode(data).decode("ascii"),
             "mimeType": mime},
            {"type": "text", "text": f"{info['title']} ({info.get('width')}x"
                                     f"{info.get('height')} original, {c.wiki})"},
        ]

    if name == "append-to-page":
        if not args.get("confirm"):
            current = c.page(args["title"])
            if not current:
                raise cw.CasiopeaError("not_found", f"la pagina '{args['title']}' no existe en {c.wiki}.")
            diff = cw._unified_diff(current, current + args["text"], args["title"])
            return _dry_run(c, args["title"],
                            f"anadir {len(args['text'])} caracteres al final", diff)
        res = c.edit(args["title"], appendtext=args["text"], nocreate=True,
                     summary=args.get("summary", "Adicion via casiopea MCP"))
        return _write_result(c, res)

    if name == "create-page":
        if not args.get("confirm"):
            existing = c.page(args["title"])
            aviso = ("\nATENCION: la pagina ya existe con "
                     f"{len(existing)} caracteres; create-page fallara. "
                     "Usar update-page o append-to-page.") if existing else ""
            return _dry_run(c, args["title"],
                            f"crear pagina ({len(args['text'])} caracteres)",
                            cw._unified_diff("", args["text"], args["title"])) + aviso
        res = c.edit(args["title"], text=args["text"], createonly=True,
                     summary=args.get("summary", "Creacion via casiopea MCP"))
        return _write_result(c, res)

    if name == "move-page":
        redirect = args.get("leaveRedirect", True)
        if not args.get("confirm"):
            return _dry_run(c, args["from"], f"mover a '{args['to']}'"
                            + (" dejando redirect" if redirect else " SIN redirect, "
                               "lo que rompe los enlaces existentes"))
        res = c.move(args["from"], args["to"], reason=args.get("reason", ""),
                     noredirect=not redirect)
        return f"Hecho en {c.wiki}: " + json.dumps(res, ensure_ascii=False)

    if name == "delete-page":
        if not args.get("confirm"):
            usos = c.backlinks(args["title"], limit=20)
            extra = (f"\nAviso: {len(usos)} pagina(s) enlazan a esta." if usos else "")
            return _dry_run(c, args["title"],
                            f"borrar (motivo: {args.get('reason', '')})") + extra
        res = c.delete(args["title"], reason=args.get("reason", ""))
        return f"Hecho en {c.wiki}: " + json.dumps(res, ensure_ascii=False)

    if name == "undelete-page":
        if not args.get("confirm"):
            return _dry_run(c, args["title"], "restaurar pagina borrada")
        res = c.undelete(args["title"], reason=args.get("reason", ""))
        return f"Hecho en {c.wiki}: " + json.dumps(res, ensure_ascii=False)

    if name == "purge-pages":
        if not args.get("confirm"):
            return _dry_run(c, ", ".join(args["titles"]),
                            f"purgar cache de {len(args['titles'])} pagina(s)")
        res = c.purge(args["titles"])
        return f"Hecho en {c.wiki}: " + json.dumps(res, ensure_ascii=False)

    if name == "upload-file":
        target = args.get("filename") or os.path.basename(args["path"])
        if not args.get("confirm"):
            return _dry_run(c, target, f"subir {args['path']}")
        res = c.upload(args["path"], filename=args.get("filename"),
                       comment=args.get("comment", ""), text=args.get("text"))
        return f"Hecho en {c.wiki}: " + json.dumps(res, ensure_ascii=False)

    if name == "upload-file-from-url":
        if not args.get("confirm"):
            return _dry_run(c, args["filename"], f"subir desde {args['url']}")
        res = c.upload_from_url(args["url"], args["filename"],
                                comment=args.get("comment", ""), text=args.get("text"))
        return f"Hecho en {c.wiki}: " + json.dumps(res, ensure_ascii=False)

    raise ValueError(f"herramienta desconocida: {name}")


# -----------------------------------------------------------------------------
# Protocolo JSON-RPC / MCP
# -----------------------------------------------------------------------------

def handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    """
    Atiende un mensaje JSON-RPC y devuelve la respuesta, o None si era una
    notificacion (los mensajes sin `id` no llevan respuesta).
    """
    method = msg.get("method")
    mid = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": SERVER_NAME, "version": cw.VERSION},
            "instructions": (
                "Acceso a la wiki Casiopea de la e[ad] PUCV, una instalacion de "
                "Semantic MediaWiki. Antes de maquetar una pagina o escribir CSS de "
                "plantilla, leer el recurso casiopea://doctrina/stella-nova: la wiki "
                "tiene un sistema de diseno propio con reglas que el sanitizador de "
                "TemplateStyles hace cumplir. Antes de guardar contenido maquetado, "
                "verificarlo con parse-wikitext. Toda escritura requiere confirm: "
                "true y queda firmada, en el historial publico, con la cuenta duena "
                "del bot password. Antes de reemplazar una pagina, traerla con "
                "get-page metadata: true y pasar su latestRevisionId como latestId, "
                "para no pisar ediciones ajenas; para cambios chicos, find-replace."
                + (" Hay dos wikis configuradas (parametro wiki): 'prod' y 'local'; "
                   f"por defecto '{default_wiki()}'. Cada resultado dice en cual "
                   "actuo." if len(available_wikis()) > 1 else "")
            ),
        }}

    if method in ("notifications/initialized", "notifications/cancelled"):
        return None

    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": tools_for_session()}}

    if method == "resources/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"resources": [
            {"uri": uri, "name": name, "description": desc, "mimeType": "text/markdown"}
            for uri, _f, name, desc in RESOURCES
            if os.path.isfile(os.path.join(REFERENCES_DIR, _f))
        ]}}

    if method == "resources/read":
        uri = params.get("uri", "")
        for res_uri, fname, _n, _d in RESOURCES:
            if res_uri == uri:
                path = os.path.join(REFERENCES_DIR, fname)
                if not os.path.isfile(path):
                    break
                with open(path, encoding="utf-8") as fh:
                    return {"jsonrpc": "2.0", "id": mid, "result": {"contents": [
                        {"uri": uri, "mimeType": "text/markdown", "text": fh.read()}
                    ]}}
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32602, "message": f"recurso desconocido: {uri}"}}

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments") or {}
        try:
            try:
                result = call_tool(name, args)
            except cw.CasiopeaError as exc:
                # Una sesion de larga vida vence: se descarta y se intenta una
                # vez mas con login nuevo. Solo ante authentication, que falla
                # antes de escribir nada, asi que repetir es seguro.
                if exc.category != "authentication":
                    raise
                forget_client(args.get("wiki"))
                result = call_tool(name, args)
            content = (result if isinstance(result, list)
                       else [{"type": "text", "text": result}])
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": content, "isError": False}}
        except cw.CasiopeaError as exc:
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": str(exc)}], "isError": True}}
        except SystemExit as exc:
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text",
                             "text": f"La operacion fallo (codigo {exc.code}). "
                                     "El detalle esta en el registro del servidor."}],
                "isError": True}}
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc(file=sys.stderr)
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": f"upstream_failure: {exc}"}],
                "isError": True}}

    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"metodo no soportado: {method}"}}


def main() -> None:
    """
    Bucle principal: una linea de stdin es un mensaje JSON-RPC.

    stdout queda reservado exclusivamente para el protocolo. Cualquier
    diagnostico va a stderr; un `print` accidental en stdout corrompe la
    sesion y el cliente desconecta sin explicar por que.
    """
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(msg)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
