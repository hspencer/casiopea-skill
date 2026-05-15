---
name: casiopea
description: Consulta y opcionalmente edita la wiki Casiopea de la e[ad] PUCV (https://wiki.ead.pucv.cl), una instalacion de Semantic MediaWiki. Activar este skill cuando el usuario mencione Casiopea, una pagina de la wiki, una travesia, una observacion, una etapa, una colecccion, una edicion, un proyecto de taller de la e[ad], o cuando pida buscar, listar, exportar a CSV, agregar, editar o crear contenido en la wiki de la escuela.
---

# Skill: casiopea

Acceso autenticado a la wiki Casiopea de la e[ad] PUCV. Casiopea es una instalacion de Semantic MediaWiki: ademas de busqueda full-text admite queries estructuradas sobre propiedades anotadas en cada pagina.

## Cuando usar este skill

Activarlo cuando el usuario:

- pide buscar, traer o leer una pagina de Casiopea
- menciona una travesia, etapa, observacion, coleccion o proyecto de la e[ad]
- pide listar paginas de una categoria o vinculadas a otra pagina
- pide exportar contenido tabular a CSV o JSON desde la wiki
- pide editar, crear o subir contenido a la wiki

## Como invocarlo

El skill provee un script CLI en `scripts/casiopea.py`. Llamarlo siempre via `python` desde Bash. La ruta al script en el plugin instalado:

```
/var/folders/dk/b0hdr3g14m58xvch43cw52hm0000gn/T/claude-hostloop-plugins/8139d02ddc034f43/skills/casiopea/scripts/casiopea.py
```

Para ahorrar tipeo, asignarla a una variable de shell al inicio de la primera invocacion:

```bash
CASIOPEA=/var/folders/dk/b0hdr3g14m58xvch43cw52hm0000gn/T/claude-hostloop-plugins/8139d02ddc034f43/skills/casiopea/scripts/casiopea.py
```

## Operaciones de lectura

### Busqueda full-text

```bash
python $CASIOPEA search "termino" --limit 10
```

Devuelve titulos y snippets. Util cuando el usuario pide algo abierto como "busca paginas sobre X".

### Wikitexto de una pagina

```bash
python $CASIOPEA page "Titulo Exacto"
```

Devuelve el wikitexto crudo. Cuando el usuario pida "el contenido de la pagina X", usar esto y luego resumir o citar selectivamente, no volcar wikitexto crudo a chat.

### Paginas de una categoria

```bash
python $CASIOPEA category "Travesia" --limit 200
```

Acepta el nombre con o sin prefijo `Category:`.

### Backlinks

```bash
python $CASIOPEA backlinks "Amereida"
```

Lista paginas que enlazan a la pagina dada. Util para entender el alcance de un concepto o autor.

### Transclusiones

```bash
python $CASIOPEA transclusions "Plantilla:Mis Cursos2"
```

Lista paginas que **transcluyen** (usan `{{X}}`) una plantilla. Distinto de `backlinks`, que solo encuentra `[[X]]`. Es imprescindible **antes de borrar o renombrar una plantilla**: te dice exactamente que paginas se romperian. Si devuelve 0 resultados, la plantilla esta segura para borrar.

### Query semantica (lo distintivo de SMW)

```bash
python $CASIOPEA ask '[[Category:Travesia]][[Año::2018]]|?Autor|?Colección|limit=50' --format csv
```

Sintaxis SMW estandar. El parametro `--format` acepta `table` (default, lectura humana), `csv` (importable a Excel o Numbers) y `json` (datos completos).

**Particularidades criticas de Casiopea** (no son las defaults de SMW):

1. **SMW configurado en espanol.** Las metapropiedades del esquema son:
   - `Tiene tipo de datos::X` (no `Has type::X`)
   - `Permite el valor::X` (no `Allows value::X`)
2. **Tipos de datos en espanol:** `Página`, `Número`, `Cadena de caracteres`, `Fecha`, `URL`, `Booleano`, `Texto`. Cuando se reciben en respuestas API tambien vienen asi.
3. **Las propiedades NO usan el prefijo "Tiene como"** que es el default vanilla. Son nombres directos en espanol, con tildes y mayusculas reales: `Autor`, `Coautores`, `Año`, `Colección`, `Edición`, `Editorial`, `Tipo de Publicación`, `Carreras Relacionadas`, `Palabras Clave`, `Título`, `Ciudad`, `Imagen`, `Páginas`. Las tildes importan: `Coleccion` no existe, `Colección` si.
4. **Las clases ontologicas core son 22**, todas con un formulario `Nuevo X` o `Nueva X`. Estas son: Acto, Asignatura, Bibliografía, Caso de Estudio, Clase, Curso, Evento, Exposición, Obra, Objeto de Archivo, Observación, Página de Cuaderno, Persona, Presencia en la Sociedad, Proyecto, Proyecto de Investigación, Proyecto de Vinculación con el Medio, Publicación, Revista Académica, Tarea, Trabajo en MADLAB, Travesía. Antes de armar una query compleja, verificar que la categoria/plantilla mencionada sea una de estas.
5. **Plantillas con sufijo "2"** (`Persona2`, `Proyecto2`, etc.) son pruebas obsoletas. Nunca usarlas en queries ni recomendar al usuario consultarlas.

Si una query devuelve filas vacias en las columnas pedidas, probablemente el nombre de la propiedad esta mal escrito (frecuentemente la tilde o un guion bajo de mas). Usar `browse` sobre una pagina representativa para ver las propiedades reales.

### Inspeccionar propiedades de una pagina

```bash
python $CASIOPEA browse "Amereida"
```

Devuelve JSON con todas las propiedades SMW anotadas. Usar antes de armar una query con `ask` cuando no se conozca el esquema.

## Operaciones de escritura

Toda escritura **requiere confirmacion explicita del usuario en el chat antes de invocar el comando con `--confirm`**. Sin `--confirm` el script hace dry-run y no toca la wiki.

Flujo obligatorio cuando el usuario pide editar o crear:

1. Confirmar con el usuario el titulo de la pagina y el contenido exacto.
2. Hacer una corrida de dry-run primero (sin `--confirm`) para mostrar lo que pasaria.
3. Mostrar al usuario lo que se va a escribir y pedir confirmacion explicita: "lo confirmo" o equivalente.
4. Solo entonces ejecutar el comando con `--confirm` agregado.

Nunca invocar `edit`, `append`, `create` o `upload` con `--confirm` en la primera vuelta, aun si el usuario sono entusiasta. Casiopea es una wiki institucional con historial; las escrituras quedan firmadas como bot y atribuidas en RecentChanges.

### Editar (reemplazar contenido)

```bash
echo "nuevo wikitexto completo" | python $CASIOPEA edit "Mi pagina" --summary "Actualizacion seccion X" --confirm
```

### Anadir al final

```bash
echo "== Nueva seccion ==" | python $CASIOPEA append "Mi pagina" --summary "Anade seccion X" --confirm
```

### Crear pagina nueva

```bash
python $CASIOPEA create "Pagina nueva" --from-file borrador.txt --summary "Creacion inicial" --confirm
```

Falla si la pagina ya existe (`createonly=1`). En ese caso usar `edit` o `append`.

### Subir archivo

```bash
python $CASIOPEA upload diagrama.png --as "Diagrama_propuesta.png" --comment "Diagrama del programa" --text "[[Category:Material doctorado]]" --confirm
```

### Borrar pagina

Requiere que el bot tenga el grant `Delete pages` en `Special:BotPasswords`. Sin grant la operacion devuelve `permissiondenied`.

```bash
python $CASIOPEA delete "Pagina obsoleta" --reason "Limpieza: pagina de prueba" --confirm
```

Borrado MUY cuidadoso: confirmar siempre con el usuario antes de invocar con `--confirm`. El borrado es reversible solo via Special:Undelete (que requiere ser sysop, no algo que el bot tenga).

## Credenciales

El skill se autentica con un Bot Password de MediaWiki. Las busca en este orden:

1. Variables de entorno `CASIOPEA_BOT_USER` y `CASIOPEA_BOT_PASS`.
2. Path indicado en `CASIOPEA_CREDENTIALS`.
3. Archivo `credentials` en cualquier carpeta montada al sandbox cuyo nombre contenga `casiopea` (ej. `~/Sites/casiopea-skill/`).
4. `~/.config/casiopea/credentials` o `~/casiopea-bot/credentials` (host local).

Si el script falla con error de credenciales, mostrar al usuario el mensaje completo: el propio script ya guia los siguientes pasos.

## Errores comunes y como diagnosticar

- **Login Failed: WrongPass** → el formato del usuario es `Usuario@NombreBot`, no solo `Usuario`. Confirmar con el usuario.
- **Query semantica devuelve columnas vacias** → propiedad mal escrita. Correr `browse` sobre una pagina representativa para descubrir las reales.
- **`createonly` falla con "articleexists"** → la pagina ya existe. Confirmar con el usuario si quiere reemplazar (`edit`) o anadir (`append`).
- **Edit retorna `result: Failure` con `code: protectedpage`** → el bot no tiene grant para editar paginas protegidas. Avisar al usuario; no insistir.

## Referencias internas

- `references/mediawiki-api.md`: detalles de la API de MediaWiki y SMW, parametros completos de cada accion, ejemplos avanzados de queries semanticas, errores comunes.
- `references/esquema-casiopea.md`: las 22 clases ontologicas core de Casiopea con sus propiedades, campos de formulario y queries semanticas de ejemplo. Cargar este archivo cuando se necesite armar una query no trivial sin tener que descubrir el esquema con `browse` cada vez.
