---
name: casiopea
description: Consulta y opcionalmente edita la wiki Casiopea de la e[ad] PUCV (https://wiki.ead.pucv.cl), una instalacion de Semantic MediaWiki. Activar este skill cuando el usuario mencione Casiopea, una pagina de la wiki, una travesia, una observacion, una etapa, una coleccion, una edicion, un proyecto de taller de la e[ad], o cuando pida buscar, listar, exportar a CSV, auditar cambios, agregar, editar, mover o crear contenido en la wiki de la escuela.
---

# Skill: casiopea

Acceso autenticado a la wiki Casiopea de la e[ad] PUCV. Casiopea es una instalacion de Semantic MediaWiki: ademas de busqueda full-text admite queries estructuradas sobre propiedades anotadas en cada pagina.

## Cuando usar este skill

Activarlo cuando el usuario:

- pide buscar, traer o leer una pagina de Casiopea
- menciona una travesia, etapa, observacion, coleccion o proyecto de la e[ad]
- pide listar paginas de una categoria o vinculadas a otra pagina
- pide exportar contenido tabular a CSV o JSON desde la wiki
- pide auditar el historial de una pagina o los cambios recientes de la wiki
- pide editar, crear, mover o subir contenido a la wiki

## Como invocarlo

El skill provee un script CLI en `scripts/casiopea.py`. Llamarlo siempre via `python` desde Bash. **Resolver la ruta en cascada** al inicio de la primera invocacion (funciona en Claude Code, Cowork y desarrollo local):

```bash
CASIOPEA=""
for c in \
  "${CLAUDE_PLUGIN_ROOT:-}/skills/casiopea/scripts/casiopea.py" \
  "${CLAUDE_SKILL_DIR:-}/scripts/casiopea.py" ; do
  [ -n "$c" ] && [ -f "$c" ] && CASIOPEA="$c" && break
done
[ -z "$CASIOPEA" ] && CASIOPEA=$(find /var/folders /tmp -path "*claude-hostloop-plugins*casiopea*/scripts/casiopea.py" 2>/dev/null | head -1)
[ -z "$CASIOPEA" ] && CASIOPEA=$(find ~/Sites /home -path "*casiopea-wiki/skills/casiopea/scripts/casiopea.py" 2>/dev/null | head -1)
echo "CASIOPEA=$CASIOPEA"
```

Luego se usa `python "$CASIOPEA" <subcomando> ...` en cada llamada.

## Operaciones de lectura

### Busqueda full-text

```bash
python "$CASIOPEA" search "termino" --limit 10
```

Devuelve titulos y snippets, **paginando automaticamente** hasta `--limit`. Util cuando el usuario pide algo abierto como "busca paginas sobre X".

### Wikitexto de una pagina

```bash
python "$CASIOPEA" page "Titulo Exacto"
```

Devuelve el wikitexto crudo. Cuando el usuario pida "el contenido de la pagina X", usar esto y luego resumir o citar selectivamente, no volcar wikitexto crudo a chat.

### Paginas de una categoria

```bash
python "$CASIOPEA" category "Travesía" --limit 500
```

Acepta el nombre con o sin prefijo `Category:`. Pagina automaticamente: con `--limit` alto trae la categoria completa, no solo la primera pagina de resultados.

### Backlinks

```bash
python "$CASIOPEA" backlinks "Amereida"
```

Lista paginas que enlazan a la pagina dada. Util para entender el alcance de un concepto o autor.

### Transclusiones

```bash
python "$CASIOPEA" transclusions "Plantilla:Mis Cursos2"
```

Lista paginas que **transcluyen** (usan `{{X}}`) una plantilla. Distinto de `backlinks`, que solo encuentra `[[X]]`. Imprescindible **antes de borrar o renombrar una plantilla**: dice exactamente que paginas se romperian. 0 resultados = plantilla segura para borrar.

### Uso de un archivo

```bash
python "$CASIOPEA" fileusage "Amereida.jpg"
```

Lista paginas que usan un archivo (con o sin prefijo `File:`/`Archivo:`). El equivalente de `transclusions` pero para imagenes/PDFs: imprescindible **antes de borrar o renombrar un archivo**.

### Historial de una pagina

```bash
python "$CASIOPEA" history "Amereida" --limit 20
```

Devuelve revisiones (timestamp, revid, usuario, tamano, comentario), de la mas nueva a la mas vieja. Util para auditar quien edito que y cuando.

### Cambios recientes de la wiki

```bash
python "$CASIOPEA" recentchanges --limit 50 --no-bots
python "$CASIOPEA" recentchanges --user FauveBellenger --type edit
```

Monitoreo de actividad de la wiki. Filtros opcionales: `--namespace` (id), `--user`, `--type` (`edit|new|log|categorize`), `--no-bots` (excluye ediciones de bot).

### Query semantica (lo distintivo de SMW)

```bash
python "$CASIOPEA" ask '[[Category:Travesía]][[Año::2018]]|?Profesores|?Destino' --format csv --max 1000
```

Sintaxis SMW estandar. **Pagina automaticamente por offset** hasta `--max` (default 500): las queries de categorias grandes ya no truncan en silencio en ~50 filas. `--format` acepta `table` (default), `csv` (Excel/Numbers) y `json` (datos completos). Si el usuario pone su propio `offset=`/`limit=` en la query, se respeta y no se pagina.

**Particularidades criticas de Casiopea** (no son las defaults de SMW):

1. **SMW configurado en espanol.** Metapropiedades: `Tiene tipo de datos::X` (no `Has type::X`), `Permite el valor::X` (no `Allows value::X`).
2. **Tipos de datos en espanol:** `Página`, `Número`, `Cadena de caracteres`, `Fecha`, `URL`, `Booleano`, `Texto`.
3. **Las propiedades NO usan el prefijo "Tiene como"** vanilla. Son nombres directos en espanol, con tildes y mayusculas reales: `Autor`, `Coautores`, `Año`, `Colección`, `Edición`, `Editorial`, `Tipo de Publicación`, `Carreras Relacionadas`, `Palabras Clave`, `Título`, `Ciudad`, `Destino`, `Profesores`. Las tildes importan: `Coleccion` no existe, `Colección` si.
4. **Las clases ontologicas core son 22**, todas con formulario `Nuevo X`/`Nueva X`: Acto, Asignatura, Bibliografía, Caso de Estudio, Clase, Curso, Evento, Exposición, Obra, Objeto de Archivo, Observación, Página de Cuaderno, Persona, Presencia en la Sociedad, Proyecto, Proyecto de Investigación, Proyecto de Vinculación con el Medio, Publicación, Revista Académica, Tarea, Trabajo en MADLAB, Travesía.
5. **Plantillas con sufijo "2"** (`Persona2`, `Proyecto2`, etc.) son pruebas obsoletas. Nunca usarlas en queries ni recomendar consultarlas.

Si una query devuelve filas vacias en las columnas pedidas, el nombre de la propiedad probablemente esta mal escrito (tilde o guion bajo). Usar `browse` sobre una pagina representativa, o consultar `references/recetas.md` y `references/esquema-casiopea.md`.

### Inspeccionar propiedades de una pagina

```bash
python "$CASIOPEA" browse "Amereida"
```

Devuelve JSON con todas las propiedades SMW anotadas. Usar antes de armar una query con `ask` cuando no se conozca el esquema.

## Operaciones de escritura

Toda escritura **requiere confirmacion explicita del usuario en el chat antes de invocar el comando con `--confirm`**. Sin `--confirm` el script hace dry-run y no toca la wiki. Para `edit/append/create` el dry-run **muestra un diff unificado** del cambio.

Flujo obligatorio cuando el usuario pide editar, crear o mover:

1. Confirmar con el usuario el titulo de la pagina y el contenido exacto.
2. Hacer una corrida de dry-run primero (sin `--confirm`).
3. Mostrar al usuario el diff y pedir confirmacion explicita: "lo confirmo" o equivalente.
4. Solo entonces ejecutar el comando con `--confirm` agregado.

Nunca invocar `edit`, `append`, `create`, `move`, `delete` o `upload` con `--confirm` en la primera vuelta, aun si el usuario sono entusiasta. Casiopea es una wiki institucional con historial; las escrituras quedan firmadas como bot y atribuidas en RecentChanges.

### Editar (reemplazar contenido)

```bash
echo "nuevo wikitexto completo" | python "$CASIOPEA" edit "Mi pagina" --summary "Actualizacion seccion X" --confirm
```

### Anadir al final

```bash
echo "== Nueva seccion ==" | python "$CASIOPEA" append "Mi pagina" --summary "Anade seccion X" --confirm
```

### Crear pagina nueva

```bash
python "$CASIOPEA" create "Pagina nueva" --from-file borrador.txt --summary "Creacion inicial" --confirm
```

Falla si la pagina ya existe (`createonly=1`). El dry-run avisa si ya existe; en ese caso usar `edit` o `append`.

### Mover / renombrar

```bash
python "$CASIOPEA" move "Titulo viejo" "Titulo nuevo" --reason "Normalizacion de nombre" --confirm
```

Por defecto deja un redirect (no rompe enlaces) y mueve la pagina de discusion. `--noredirect` para no dejar redirect (requiere permiso). Antes de mover una plantilla, correr `transclusions`; antes de mover un archivo, `fileusage`.

### Subir archivo

```bash
python "$CASIOPEA" upload diagrama.png --as "Diagrama_propuesta.png" --comment "Diagrama del programa" --text "[[Category:Material doctorado]]" --confirm
```

Archivos grandes (> 8 MB) suben en chunks automaticamente.

### Borrar pagina

Requiere el grant `Delete pages` en `Special:BotPasswords`. Sin grant devuelve `permissiondenied`.

```bash
python "$CASIOPEA" delete "Pagina obsoleta" --reason "Limpieza: pagina de prueba" --confirm
```

Borrado MUY cuidadoso: confirmar siempre antes de `--confirm`. Reversible solo via Special:Undelete (requiere sysop, no algo que el bot tenga).

## Credenciales

El skill se autentica con un Bot Password de MediaWiki. Las busca en este orden:

1. Variables de entorno `CASIOPEA_BOT_USER` y `CASIOPEA_BOT_PASS`.
2. Path indicado en `CASIOPEA_CREDENTIALS`.
3. Archivo `credentials` en cualquier carpeta montada cuyo nombre contenga `casiopea`.
4. `~/.config/casiopea/credentials`, `~/casiopea-bot/credentials` o `~/Sites/casiopea-skill/credentials`.

Si el script falla con error de credenciales, mostrar al usuario el mensaje completo: el propio script ya guia los siguientes pasos.

## Cortesia de bot (automatica)

El script ya manda `maxlag=5` y `assert=user` en cada llamada, y reintenta con backoff ante `maxlag`, `ratelimited` o HTTP 429/503. Ante `badtoken` en una escritura refresca el CSRF y reintenta una vez. No hace falta espaciar llamadas manualmente para volumenes moderados; para miles de paginas, preferir el dump XML.

## Errores comunes y como diagnosticar

- **Login Failed: WrongPass** → el usuario es `Usuario@NombreBot`, no solo `Usuario`. Confirmar con el usuario.
- **Query semantica devuelve columnas vacias** → propiedad mal escrita. Correr `browse` o revisar `references/recetas.md`.
- **`createonly` falla con "articleexists"** → la pagina ya existe. Confirmar si reemplazar (`edit`) o anadir (`append`).
- **Edit retorna `code: protectedpage`** → el bot no tiene grant para paginas protegidas. Avisar; no insistir.
- **`code: assertuserfailed`** → la sesion se cayo. Re-login (el CLI lo hace al reinvocar).

## Referencias internas

- `references/recetas.md`: recetas de query SMW listas para usar (travesias por anio, publicaciones por autor, observaciones de un proyecto, exportar categoria a CSV) y flujo de auditoria/limpieza de plantillas `*2`. Cargar primero cuando el usuario pida algo tabular.
- `references/esquema-casiopea.md`: las 22 clases ontologicas core con sus propiedades, campos de formulario y queries de ejemplo. Cargar para armar una query no trivial sin descubrir el esquema con `browse`.
- `references/mediawiki-api.md`: detalles de la API de MediaWiki y SMW, parametros completos de cada accion, errores comunes.
