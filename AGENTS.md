# AGENTS.md

Contrato para agentes que operan la wiki Casiopea de la e[ad] PUCV a través de este repositorio. Aplica a cualquier agente que lea este archivo: Codex, Cursor, Copilot, Gemini CLI, Claude Code, o el que venga. Para personas, empezar por [README.md](README.md).

## Lo primero

Las credenciales que usa este código son un **bot password derivado de una cuenta personal**. Cada escritura queda en el historial público de la wiki atribuida a esa persona. No hay atribución a un agente, no hay deshacer silencioso, y las revisiones se conservan desde 2007.

Esto tiene una consecuencia operativa concreta: **ninguna operación que modifique la wiki se ejecuta sin confirmación humana explícita en la conversación**, por inequívoca que parezca la petición. El ensayo previo no es una sugerencia del diseño; es el comportamiento por defecto y saltárselo es un error.

## Qué hay aquí

```
casiopea-wiki/skills/casiopea/
  SKILL.md                      instrucciones operativas completas
  scripts/casiopea.py           el CLI; toda la logica vive aqui
  scripts/casiopea_mcp.py       servidor MCP stdio sobre el mismo codigo
  references/stella-nova.md     doctrina grafica del skin
  references/recetas-diseno.md  patrones de maquetacion
  references/esquema-casiopea.md las 22 clases semanticas
  references/recetas.md         consultas SMW listas
  references/mediawiki-api.md   detalle de la API
casiopea-wiki/commands/         cinco comandos slash (Claude Code / Cowork)
docs/                           material de trabajo, no se empaqueta
```

Dos formas de usarlo, con el mismo código detrás:

- **CLI**: `python3 casiopea-wiki/skills/casiopea/scripts/casiopea.py <verbo>`. Sin dependencias externas, Python 3.10+.
- **MCP**: `python3 casiopea-wiki/skills/casiopea/scripts/casiopea_mcp.py` sobre stdio. 26 herramientas y las referencias publicadas como recursos MCP.

## Configuración

Credenciales, en orden de precedencia:

1. `CASIOPEA_BOT_USER` y `CASIOPEA_BOT_PASS`
2. el archivo apuntado por `CASIOPEA_CREDENTIALS`
3. `credentials` en cualquier carpeta montada cuyo nombre contenga `casiopea`
4. `~/.config/casiopea/credentials`, `~/casiopea-bot/credentials`, `~/Sites/casiopea-skill/credentials`

Formato del archivo:

```ini
CASIOPEA_BOT_USER=TuCuenta@nombre-del-bot
CASIOPEA_BOT_PASS=contrasena-larga
```

El sufijo `@nombre-del-bot` es obligatorio. Sin él, MediaWiki responde `WrongPass` y parece un problema de contraseña.

Otras variables: `CASIOPEA_API_URL` (endpoint alternativo), `CASIOPEA_MAX_BYTES` (presupuesto de truncado, 50000 por defecto).

Diagnóstico en una sola corrida: `python3 .../casiopea.py doctor`.

## Verbos del CLI

Lectura, sin efectos: `search`, `prefix`, `page`, `pages`, `sections`, `revision`, `category`, `backlinks`, `transclusions`, `fileusage`, `history`, `compare`, `recentchanges`, `ask`, `browse`, `properties`, `parse`, `siteinfo`, `whoami`.

Escritura, requieren `--confirm`: `edit`, `append`, `create`, `move`, `delete`, `undelete`, `purge`, `upload`, `upload-from-url`.

Mantenimiento: `doctor`, `sn-sync`.

Opciones globales: `--wiki prod|local`, `--api URL`.

## Reglas de operación

**Antes de escribir contenido maquetado, previsualizarlo.** `parse --from-file borrador.mw --title "X"` renderiza contra la wiki real sin guardar nada y reporta plantillas inexistentes, enlaces rojos y advertencias del parser. Publicar sin este paso es cómo se publican plantillas mal escritas.

**Antes de renombrar o borrar, medir el impacto.** `transclusions` para plantillas, `fileusage` para archivos, `backlinks` para páginas. La respuesta correcta a "¿se puede borrar?" es un número, no una impresión.

**Antes de confirmar, volver a traer.** Las páginas se editan en vivo. Reconstruir el cambio sobre la versión actual, no sobre la que se leyó hace diez minutos. Un error `conflict` es exactamente ese descuido.

**Después de tocar una plantilla o su `/style.css`, purgar.** MediaWiki cachea el HTML renderizado; sin `purge` las páginas que transcluyen la plantilla siguen mostrando la versión vieja y parece que el cambio falló.

**Al diseñar, leer `references/stella-nova.md` primero.** La wiki tiene sistema de diseño con tokens semánticos, y el sanitizador de TemplateStyles rechaza construcciones comunes: `var(--x, fallback)`, `light-dark()`, `:is()`, `font-stretch` en porcentaje literal, divisiones dentro de `calc()`. Improvisar produce hojas de estilo que no se guardan.

**No inventar tokens ni clases del skin.** El conjunto se mantiene chico deliberadamente. Proponer y esperar decisión humana.

## Categorías de error

Todo fallo sale por stderr como `categoria: detalle`, con código de salida propio:

| Categoría | Código | Respuesta apropiada |
|---|---|---|
| `not_found` | 6 | verificar el título con `prefix` o `search` |
| `permission_denied` | 7 | reportar a la persona; no reintentar igual |
| `invalid_input` | 8 | corregir argumentos y reintentar |
| `conflict` | 9 | re-traer, reconstruir, reintentar |
| `authentication` | 4 | mostrar el mensaje completo; no seguir |
| `rate_limited` | 10 | el CLI ya reintenta; si persiste, esperar |
| `upstream_failure` | 3 | reintentar con cuidado; si persiste, reportar |

Un código desconocido de MediaWiki cae en `upstream_failure` conservando el mensaje crudo: se pierde precisión, no información.

## Particularidades de Casiopea

SMW está configurado en español. Las propiedades no usan el prefijo `Tiene como` de vanilla: son nombres directos con tildes y mayúsculas reales (`Colección`, `Año`, `Carreras Relacionadas`). Un nombre mal escrito **devuelve columnas vacías sin ningún error**, así que ante un resultado vacío inesperado la primera hipótesis es la ortografía:

```bash
python3 .../casiopea.py properties --grep coleccion   # responde: Colección
```

Las plantillas con sufijo `2` (`Persona2`, `Proyecto2`) son pruebas obsoletas. No usarlas ni recomendarlas.

Los borradores y snapshots de wikitexto usan extensión `.mw`.

## Al modificar este repositorio

- La lógica va en `casiopea.py`. `casiopea_mcp.py` es solo capa de protocolo y lo importa: no duplicar lógica de red, credenciales ni salvaguardas.
- Un verbo nuevo del CLI que deba estar disponible por MCP necesita también su entrada en `TOOLS` y su rama en `call_tool`.
- Toda herramienta MCP declara las cuatro anotaciones de comportamiento (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`). Hay clientes que rechazan la herramienta si falta alguna.
- Las descripciones de herramienta van en tercera persona, dicen qué hace y qué devuelve, y desambiguan explícitamente frente a las hermanas parecidas. Sin imperativos dirigidos al modelo.
- Cambios en el skin Stella Nova: regenerar el inventario con `casiopea.py sn-sync`. `references/stella-nova-inventario.md` es generado y se sobreescribe; `references/stella-nova.md` es curado y se edita a mano.
- Tras cualquier cambio en `casiopea-wiki/`, `./build.sh` regenera el `.plugin`.
