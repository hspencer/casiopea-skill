# Changelog

Cambios notables de `casiopea-skill`. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [0.6.0] — 2026-09-25

El skill queda autónomo: su servidor MCP cubre lo que se hacía con el MediaWiki MCP Server de Professional Wiki, incluido trabajar con un espejo local y producción en la misma sesión.

### Añadido

- **Credenciales por wiki.** `CASIOPEA_PROD_BOT_*` (o los genéricos `CASIOPEA_BOT_*`, que siguen valiendo) para producción y `CASIOPEA_LOCAL_BOT_*` para el espejo local. Antes el CLI usaba el bot de producción también con `--wiki local`, y el login fallaba.
- **El espejo local es opcional.** Sin claves `CASIOPEA_LOCAL_*` no existe para el skill: el MCP no anuncia el parámetro `wiki` y `doctor` lo informa como opcional. Con ellas, cada herramienta MCP gana el parámetro `wiki` (`prod` o `local`, y también `wiki.ead.pucv.cl` o `casiopea.local`), cada wiki mantiene su propia sesión y cada resultado dice en cuál actuó. `CASIOPEA_DEFAULT_WIKI` fija la wiki por defecto.
- **Detección de conflictos.** `update-page` y `find-replace` aceptan `latestId`; el CLI, `--base-rev`. Si la página cambió desde esa revisión, la escritura aborta con `conflict`. El ensayo muestra la revisión base, y la edición viaja además con `baserevid` y `basetimestamp`.
- **`find-replace` (MCP) y `replace` (CLI).** Cambian un fragmento exacto sin reenviar la página; si el fragmento no aparece o aparece más de una vez, no escriben nada.
- **Archivos.** `get-file` y `get-file-data` en el MCP (la segunda devuelve la imagen para mirarla); `file` y `file-download` en el CLI.
- `get-page` con `metadata: true` antepone la revisión vigente.

### Cambiado

- Los errores llegan completos al modelo en el MCP (`categoria: detalle` y sugerencia); antes solo decía «fallo (código N)» y el detalle quedaba en el log del servidor. `fail()` levanta `CasiopeaError`, que hereda de `SystemExit`, así que el CLI se comporta igual.
- El MCP rehace el login una vez si la sesión venció.
- `update-page` y `append-to-page` ya no crean la página si no existe (`nocreate`); para eso está `create-page`.
- `doctor` acepta `--wiki` y lista qué wikis tienen credenciales.

## [0.5.0] — 2026-07-31

Upgrade sustantivo en tres frentes: conocimiento del sistema de diseño, superficie del CLI, y compatibilidad con agentes que no son Claude Code.

### Añadido

- **Doctrina gráfica de Stella Nova.** `references/stella-nova.md` destila el sistema de diseño del skin: las tres capas de tokens, los semánticos de uso frecuente con su valor, las clases opt-in (`grid`/`grilla`, `full-width`, `fondo-*`, `plantilla`, `wiki-btn`, `fw-*`), las palabras mágicas, y la tabla de construcciones que el sanitizador de TemplateStyles rechaza. `references/recetas-diseno.md` acompaña con patrones listos para adaptar.
- **`sn-sync`**: regenera `references/stella-nova-inventario.md` leyendo `tokens.css` y `skin.json` del repositorio del skin, clasificando cada custom property por capa. Con `--check-wiki` coteja además contra las páginas `[[Stella Nova/*]]` publicadas.
- **Comando `/casiopea:maquetar`**: modo de diseño, con la doctrina cargada y el flujo de previsualización obligatorio.
- **Verbos de lectura nuevos**: `prefix` (búsqueda por título), `pages` (lote de hasta 50), `sections` (índice), `revision` (versión histórica), `compare` (diff calculado por el servidor), `properties` (propiedades SMW, con filtro insensible a tildes), `parse` (renderiza wikitexto sin guardarlo), `siteinfo`, `whoami`.
- **Verbos de escritura nuevos**: `undelete`, `purge`, `upload-from-url`.
- **`doctor`**: diagnóstico de versión de Python, origen y permisos de las credenciales, identidad y permisos efectivos del bot, y extensiones instaladas en la wiki.
- **Servidor MCP** (`scripts/casiopea_mcp.py`): stdio, sin dependencias, 26 herramientas sobre el mismo código del CLI. Publica las referencias del skill como recursos MCP para que el agente cargue la doctrina sin salir a buscarla. Declarado en `casiopea-wiki/.mcp.json`.
- **`AGENTS.md`**: contrato para cualquier agente que lea el estándar, no solo Claude Code.
- **Opciones globales** `--wiki prod|local` y `--api URL`.

### Cambiado

- **Taxonomía de errores en siete categorías** (`not_found`, `permission_denied`, `invalid_input`, `conflict`, `authentication`, `rate_limited`, `upstream_failure`), con código de salida propio y formato estable `categoria: detalle`. Un código desconocido de MediaWiki cae en `upstream_failure` conservando el mensaje crudo.
- **Truncado con marcador.** `page` corta a 50 KB por defecto e imprime el índice de secciones disponibles y el comando para pedir la parte que falta. Los listados avisan cuando alcanzan el tope, en vez de parecer completos.
- **READMEs reescritos** partiendo por lo que importa: el bot se crea con la cuenta personal de quien instala, y cada escritura queda firmada con su nombre en el historial público.
- **`build.sh`** valida los manifiestos y compila los scripts antes de empaquetar, y aborta si encuentra un archivo de credenciales dentro del plugin.

### Notas

Las convenciones de descripción de herramienta, la taxonomía de errores y el patrón de marcador de truncado están tomadas del [MediaWiki MCP Server](https://github.com/ProfessionalWiki/MediaWiki-MCP-Server) de Professional Wiki, cuyo `docs/tool-conventions.md` es la mejor documentación pública sobre el tema.

## [0.4.0]

Plugin renombrado a `casiopea`, con cuatro comandos por intención.

## [0.3.0]

Plugin instalable en Claude Code; CLI enriquecido.

## [0.2.0]

Versión inicial.
