# Changelog

Cambios notables de `casiopea-skill`. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

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
