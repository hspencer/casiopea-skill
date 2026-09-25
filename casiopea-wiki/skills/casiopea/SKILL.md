---
name: casiopea
description: Lee, consulta, audita, maqueta y edita la wiki Casiopea de la e[ad] PUCV (https://wiki.ead.pucv.cl), una instalacion de Semantic MediaWiki con el skin propio Stella Nova. Activar cuando se mencione Casiopea, una pagina de la wiki, una travesia, observacion, etapa, coleccion, obra, publicacion o proyecto de taller de la e[ad]; cuando se pida buscar, listar, exportar a CSV, auditar cambios, crear, editar o mover contenido en la wiki de la escuela; y cuando se pida disenar, maquetar o dar estilo a una pagina o plantilla de Casiopea, o escribir CSS con TemplateStyles o con los tokens de Stella Nova.
---

# Skill: casiopea

Acceso autenticado a la wiki Casiopea de la e[ad] PUCV. Dos cosas la distinguen de una wiki cualquiera, y de ellas se deriva todo lo demás:

1. Es una instalación de **Semantic MediaWiki**: además de búsqueda full-text admite consultas estructuradas sobre propiedades tipadas anotadas en cada página.
2. Tiene un **sistema de diseño propio**, el skin Stella Nova, con tokens, clases y reglas que el sanitizador de MediaWiki hace cumplir. Maquetar sin conocerlas produce páginas ilegibles en tema oscuro, o CSS que directamente no se guarda.

## Antes que nada: quién firma

Este skill actúa con un **bot password**, que es una credencial derivada de la cuenta personal de quien lo configuró. Todo lo que escriba queda en el historial público de la wiki **atribuido a esa persona**, no a un agente. Esto no es un detalle burocrático: cambia el estándar de cuidado.

En la práctica: nunca ejecutar una escritura sin confirmación explícita en el chat, siempre verificar antes con las herramientas de lectura, y siempre medir el impacto antes de tocar algo que otras páginas usan.

## Cómo invocar el CLI

El skill provee `scripts/casiopea.py`. Resolver la ruta en cascada al inicio de la primera invocación (funciona en Claude Code, Cowork y desarrollo local):

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

Luego `python "$CASIOPEA" <subcomando> ...` en cada llamada. Si algo falla al primer intento, `python "$CASIOPEA" doctor` diagnostica credenciales, red, permisos del bot y extensiones instaladas en una sola corrida.

Opciones globales: `--wiki prod|local` o `--api URL` para apuntar a otra instancia. Por defecto, producción (o lo que diga `CASIOPEA_DEFAULT_WIKI`).

### Si existe un espejo local

`local` es un espejo de desarrollo en `http://casiopea.local` que solo tiene quien lo montó. Existe para el skill únicamente si hay credenciales `CASIOPEA_LOCAL_BOT_USER` y `CASIOPEA_LOCAL_BOT_PASS`; sin ellas, el skill trabaja solo con producción y `doctor` lo informa como opcional. Cuando está configurado, el servidor MCP agrega un parámetro `wiki` a cada herramienta y cada resultado dice en qué wiki actuó. La política de uso (por ejemplo, probar siempre en el espejo antes de publicar) es de quien lo tiene y va en sus propias instrucciones de proyecto, fuera de este skill. El espejo guarda los textos pero no siempre los archivos subidos: comprobar una imagen con `file` en la wiki de destino antes de pasar una página de una a otra.

## Cómo leer los errores

Cada fallo sale por stderr con la forma `categoria: detalle`. La categoría dice qué hacer sin tener que interpretar prosa:

| Categoría | Qué significa | Qué hacer |
|---|---|---|
| `not_found` | el título, revisión o archivo no existe | verificar el título exacto con `prefix` o `search` |
| `permission_denied` | falta el grant, o la página está protegida | avisar a la persona; no reintentar igual |
| `invalid_input` | argumentos incompatibles o mal formados | corregir y reintentar |
| `conflict` | edit conflict, o `create` sobre una página existente | volver a traer la página y reconstruir el cambio |
| `authentication` | credenciales ausentes, inválidas o expiradas | mostrar el mensaje completo a la persona |
| `rate_limited` | la wiki está frenando al bot | el CLI ya reintenta solo; si persiste, esperar |
| `upstream_failure` | error no clasificado, red, modo solo lectura | reintentar con cuidado; si persiste, reportar |

## Operaciones de lectura

### Encontrar la página

```bash
python "$CASIOPEA" search "termino" --limit 10        # busca en el contenido
python "$CASIOPEA" prefix "Stella Nova/" --limit 50   # busca en los titulos
python "$CASIOPEA" prefix "Persona" --namespace 10    # solo plantillas
```

`search` mira el texto; `prefix` mira el título y es la forma correcta de enumerar un árbol de subpáginas o de resolver un título del que solo se sabe el comienzo.

### Traer contenido

```bash
python "$CASIOPEA" page "Titulo Exacto"                    # wikitexto completo
python "$CASIOPEA" sections "Titulo Exacto"                # indice de secciones
python "$CASIOPEA" page "Titulo Exacto" --section 3        # solo una seccion
python "$CASIOPEA" pages "Plantilla:A" "Plantilla:B"       # hasta 50 de una vez
python "$CASIOPEA" revision 1965943                        # una version historica
python "$CASIOPEA" file "Archivo:Foto.jpg"                 # existe?, autor, tamano, URLs
python "$CASIOPEA" file-download "Foto.jpg" --width 800    # baja una miniatura
```

`page` trunca a 50 KB y, cuando lo hace, imprime el índice de secciones para poder volver por la parte que interesa. Nunca volcar wikitexto crudo al chat: resumir o citar selectivamente.

### Medir impacto antes de romper algo

```bash
python "$CASIOPEA" backlinks "Amereida"                    # quien enlaza [[X]]
python "$CASIOPEA" transclusions "Plantilla:Mis Cursos2"   # quien usa {{X}}
python "$CASIOPEA" fileusage "Amereida.jpg"                # quien muestra el archivo
```

Los tres son obligatorios antes de renombrar o borrar. Cero resultados significa que la operación es segura; cualquier otro número es la lista exacta de páginas que se van a romper.

### Auditar

```bash
python "$CASIOPEA" history "Amereida" --limit 20
python "$CASIOPEA" compare 1965943 1965944          # diff entre revisiones
python "$CASIOPEA" compare "Plantilla:A" "Plantilla:B"
python "$CASIOPEA" recentchanges --limit 50 --no-bots
python "$CASIOPEA" whoami                            # identidad y permisos
python "$CASIOPEA" siteinfo                          # version y extensiones
```

### Consulta semántica

```bash
python "$CASIOPEA" ask '[[Category:Travesía]][[Año::2018]]|?Profesores|?Destino' --format csv --max 1000
python "$CASIOPEA" properties --grep coleccion       # como se llama de verdad
python "$CASIOPEA" browse "Amereida"                 # propiedades de una pagina
```

Particularidades de Casiopea que no son las defaults de SMW:

1. **SMW está en español.** Metapropiedades: `Tiene tipo de datos::X`, `Permite el valor::X`. Tipos: `Página`, `Número`, `Cadena de caracteres`, `Fecha`, `URL`, `Booleano`, `Texto`.
2. **Las propiedades no usan el prefijo "Tiene como"** vanilla. Son nombres directos en español, con tildes y mayúsculas reales: `Autor`, `Coautores`, `Año`, `Colección`, `Edición`, `Editorial`, `Tipo de Publicación`, `Carreras Relacionadas`, `Palabras Clave`, `Título`, `Ciudad`, `Destino`, `Profesores`.
3. **Las tildes importan.** `Coleccion` no existe, `Colección` sí, y una propiedad mal escrita devuelve columnas vacías **sin ningún mensaje de error**. Ante columnas vacías inesperadas, `properties --grep` antes que cualquier otra hipótesis.
4. **Las clases ontológicas core son 22**, todas con formulario `Nuevo X`/`Nueva X`: Acto, Asignatura, Bibliografía, Caso de Estudio, Clase, Curso, Evento, Exposición, Obra, Objeto de Archivo, Observación, Página de Cuaderno, Persona, Presencia en la Sociedad, Proyecto, Proyecto de Investigación, Proyecto de Vinculación con el Medio, Publicación, Revista Académica, Tarea, Trabajo en MADLAB, Travesía.
5. **Las plantillas con sufijo "2"** (`Persona2`, `Proyecto2`) son pruebas obsoletas. No usarlas ni recomendarlas.

`ask` pagina automáticamente por offset hasta `--max` (500 por defecto). Si la consulta trae su propio `offset=`/`limit=`, se respeta y no se pagina.

## Diseño y maquetación

Casiopea tiene sistema de diseño. **Antes de escribir wikitexto maquetado, CSS de plantilla o cualquier cosa con clases, cargar `references/stella-nova.md`.** No improvisar: hay construcciones que el sanitizador rechaza, y una página que se ve bien en tema claro puede ser ilegible en oscuro.

Los cuatro hechos que más se olvidan:

1. **Nunca hardcodear color.** Se usan tokens semánticos: `var(--sn-ink)`, `var(--sn-paper)`, `var(--sn-hairline)`. Nunca `#000`, `#fff` ni una primitiva como `--sn-rojo-500`.
2. **`var()` va sin respaldo.** El sanitizador de TemplateStyles rechaza `var(--x, fallback)` y la hoja no se guarda. Tampoco acepta `light-dark()`, `:is()`, `font-stretch` en porcentaje literal, ni divisiones dentro de `calc()`.
3. **La maquetación es `grid` / `grilla`**, no Bootstrap. Cada hijo directo es una celda; los modificadores se suman como clases (`cols-3 gap-l align-center`).
4. **El ritmo vertical usa `--sn-baseline*`**, no la escala de espaciado `--sn-s-*`. Confundirlos deriva la retícula cuando el lector cambia el tamaño de letra.

### El flujo obligatorio de maquetación

```bash
# 1. escribir el borrador en un archivo .mw
# 2. previsualizarlo contra la wiki real, sin guardar nada
python "$CASIOPEA" parse --from-file borrador.mw --title "Mi página"
# 3. si toca una plantilla existente, medir impacto
python "$CASIOPEA" transclusions "Plantilla:X"
# 4. dry-run con diff, mostrar a la persona, pedir confirmacion
python "$CASIOPEA" edit "Mi página" --from-file borrador.mw --summary "..."
# 5. recien entonces, --confirm
# 6. tras tocar una /style.css, purgar las paginas que la usan
python "$CASIOPEA" purge "Mi página" --confirm
```

El paso 2 es el que evita publicar una plantilla mal escrita: `parse` reporta las plantillas invocadas que no existen, los enlaces rojos y las advertencias del parser, todo antes de que quede nada en el historial.

El paso 6 se olvida siempre y produce media hora de depurar un cambio que ya estaba bien.

## Operaciones de escritura

Toda escritura **requiere confirmación explícita de la persona en el chat antes de invocar el comando con `--confirm`**. Sin `--confirm` el script hace dry-run y no toca la wiki; para `edit`, `append` y `create` el dry-run muestra un diff unificado.

Flujo obligatorio:

1. Confirmar el título de la página y el contenido exacto.
2. Correr el dry-run (sin `--confirm`).
3. Mostrar el diff y pedir confirmación explícita.
4. Solo entonces agregar `--confirm`.

Nunca invocar `edit`, `replace`, `append`, `create`, `move`, `delete`, `undelete` o `upload` con `--confirm` en la primera vuelta, por entusiasta que haya sonado la petición.

```bash
python "$CASIOPEA" replace "Plantilla:X" --find "texto exacto" --with "texto nuevo" --base-rev 123 --confirm
echo "wikitexto completo" | python "$CASIOPEA" edit "Página" --summary "..." --base-rev 123 --confirm
echo "== Nueva sección ==" | python "$CASIOPEA" append "Página" --summary "..." --confirm
python "$CASIOPEA" create "Página nueva" --from-file borrador.mw --summary "..." --confirm
python "$CASIOPEA" move "Título viejo" "Título nuevo" --reason "..." --confirm
python "$CASIOPEA" delete "Página obsoleta" --reason "..." --confirm
python "$CASIOPEA" undelete "Página borrada" --reason "..." --confirm
python "$CASIOPEA" purge "Página A" "Página B" --confirm
python "$CASIOPEA" upload diagrama.png --as "Diagrama.png" --comment "..." --confirm
python "$CASIOPEA" upload-from-url "https://..." --as "Foto.jpg" --comment "..." --confirm
```

Notas:

- Para cambiar una parte de una página se usa `replace`: viaja solo el fragmento, y si `--find` no aparece o aparece más de una vez no escribe nada. Se amplía el fragmento con texto de alrededor hasta que sea único.
- El dry-run de `edit` y `replace` muestra la revisión base (`base r123`). Pasarla como `--base-rev` al confirmar hace que la escritura aborte con `conflict` si alguien editó la página entre el ensayo y la confirmación.
- `create` falla si la página ya existe (`createonly=1`); el dry-run avisa. En ese caso, `edit` o `append`.
- `move` deja redirect por defecto y mueve la página de discusión. `--noredirect` requiere permiso y rompe enlaces.
- `delete` requiere el grant `Delete pages`. Es reversible con `undelete` mientras la wiki no purgue el archivo, pero eso no lo convierte en gratis.
- Los archivos de más de 8 MB suben en chunks automáticamente.
- Los borradores y snapshots de wikitexto usan extensión `.mw`.

## Antes de publicar: volver a traer

Las páginas de Casiopea se editan en vivo por personas. Entre que se leyó una página y se propone un cambio pueden haber pasado minutos y una edición ajena. Antes de `--confirm`, **volver a traer la página y reconstruir el cambio sobre la versión actual**, y confirmar con `--base-rev` (en el MCP, `latestId`) igual a la revisión que mostró el ensayo. Un `conflict` es la wiki avisando que eso pasó.

## Credenciales

Producción usa `CASIOPEA_PROD_BOT_USER` y `CASIOPEA_PROD_BOT_PASS`, o los genéricos `CASIOPEA_BOT_USER` y `CASIOPEA_BOT_PASS` de siempre. El espejo local, si existe, usa `CASIOPEA_LOCAL_BOT_USER` y `CASIOPEA_LOCAL_BOT_PASS`: cada wiki tiene su propio bot password y el de una no sirve en la otra.

Cada clave se busca primero en el entorno y luego en el primer archivo que exista, en este orden: el path de `CASIOPEA_CREDENTIALS`; un archivo `credentials` en cualquier carpeta montada cuyo nombre contenga `casiopea`; `~/.config/casiopea/credentials`, `~/casiopea-bot/credentials`, `~/Sites/casiopea-skill/credentials`.

Si falla por credenciales, mostrar el mensaje completo del script a la persona: ya guía los siguientes pasos.

## Cortesía de bot

Automática. El script manda `maxlag=5` y `assert=user` en cada llamada, y reintenta con backoff ante `maxlag`, `ratelimited` o HTTP 429/503. Ante `badtoken` refresca el CSRF y reintenta una vez. No hace falta espaciar llamadas a mano; para miles de páginas, preferir el dump XML.

## Referencias internas

Cargar bajo demanda, no todas de entrada:

- `references/stella-nova.md` — **doctrina gráfica**: tokens semánticos, clases opt-in del skin, la grilla, las palabras mágicas y lo que el sanitizador rechaza. Cargar antes de maquetar o escribir CSS.
- `references/recetas-diseno.md` — patrones de wikitexto listos para adaptar: portada a sangre, galería, ficha, listado semántico en tarjetas, plantilla con TemplateStyles.
- `references/stella-nova-inventario.md` — inventario generado de todos los tokens declarados, con su valor. Regenerable con `python "$CASIOPEA" sn-sync`.
- `references/recetas.md` — consultas SMW listas para usar y flujo de auditoría de plantillas `*2`. Cargar primero cuando se pida algo tabular.
- `references/esquema-casiopea.md` — las 22 clases ontológicas con sus propiedades y campos de formulario. Cargar para armar una consulta no trivial sin descubrir el esquema con `browse`.
- `references/mediawiki-api.md` — parámetros completos de cada acción de la API.
