# Referencia tecnica: API de MediaWiki y Semantic MediaWiki en Casiopea

Esta referencia documenta los endpoints y parametros que el script `casiopea.py` usa contra `https://wiki.ead.pucv.cl/api.php`. Sirve para entender que esta haciendo el script bajo el capo, depurar errores raros y armar queries no cubiertas por los subcomandos del CLI.

## Endpoint base

Todas las llamadas van a un mismo endpoint `https://wiki.ead.pucv.cl/api.php`. La accion se especifica con el parametro `action` y el formato de respuesta con `format=json&formatversion=2`. El script siempre usa `formatversion=2` porque devuelve listas en vez de dicts indexados por id, lo que simplifica el parseo.

## Autenticacion: Bot Passwords

MediaWiki distingue entre la contrasena normal de un usuario y un Bot Password. Los Bot Passwords se generan en `Special:BotPasswords`, tienen permisos acotados (grants) y un nombre propio. El usuario para login debe combinar ambos:

```
lgname=NombreUsuario@NombreBot
lgpassword=<contrasena-larga-de-bot-password>
```

El login es en dos pasos:

1. Pedir un login token: `action=query&meta=tokens&type=login`. La respuesta contiene `query.tokens.logintoken`.
2. Llamar `action=login` con `lgname`, `lgpassword` y `lgtoken=<el token del paso 1>`. La respuesta exitosa tiene `login.result == "Success"`.

Las cookies de sesion devueltas se mantienen en un `CookieJar` y viajan automaticamente en cada request siguiente. No hace falta volver a autenticar mientras dure el proceso del CLI.

## Operaciones de lectura

### list=search

Busqueda full-text:

```
action=query&list=search&srsearch=<termino>&srlimit=20
```

La respuesta es `query.search`, una lista de objetos con `title`, `pageid`, `snippet`, `timestamp`, `wordcount`.

### prop=revisions

Wikitexto crudo de una pagina:

```
action=query&prop=revisions&titles=<titulo>&rvprop=content&rvslots=main
```

El contenido vive en `query.pages[0].revisions[0].slots.main.content`. Si la pagina no existe el primer page tiene `missing: true`.

### list=categorymembers

Paginas en una categoria:

```
action=query&list=categorymembers&cmtitle=Category:<nombre>&cmlimit=200
```

Acepta paginacion con `cmcontinue` cuando hay mas resultados que el limite.

### list=backlinks

Paginas que enlazan a otra:

```
action=query&list=backlinks&bltitle=<titulo>&bllimit=200
```

## Operaciones SMW

Semantic MediaWiki agrega dos acciones especificas al endpoint estandar.

### action=ask

Ejecuta una query semantica en formato `#ask`:

```
action=ask&query=[[Category:X]][[Propiedad::Valor]]|?Prop1|?Prop2|limit=50
```

Estructura de la query:

- Las condiciones van entre dobles corchetes: `[[Category:X]]`, `[[Propiedad::Valor]]`. Se concatenan con AND implicito.
- Los printouts (columnas a devolver) van precedidos por `?` y separados por `|`.
- Parametros adicionales van como `key=value`: `limit=50`, `offset=0`, `sort=Año`, `order=desc`.

La respuesta tiene la forma:

```json
{
  "query": {
    "results": {
      "Titulo de la pagina": {
        "fulltext": "Titulo de la pagina",
        "fullurl": "https://...",
        "printouts": {
          "Año": [2023],
          "Autor": [{"fulltext": "Herbert Spencer", "fullurl": "..."}]
        }
      }
    },
    "printrequests": [
      {"label": "Año", "key": "Año", "typeid": "_num", ...}
    ]
  }
}
```

El formateador del CLI aplana esto: para cada propiedad emite `; ` entre valores multiples, y para valores que son objetos extrae `fulltext`.

### action=browsebysubject

Devuelve todas las propiedades semanticas anotadas en una pagina dada:

```
action=browsebysubject&subject=<titulo>
```

Util para descubrir el esquema real de propiedades antes de armar una query con `ask`. La respuesta devuelve una lista de propiedades con sus valores.

## Particularidades de Casiopea (importantes)

### SMW configurado en español

Casiopea localiza Semantic MediaWiki al espanol. Esto cambia las metapropiedades del esquema:

| Estandar SMW (ingles)     | En Casiopea                        |
|---------------------------|------------------------------------|
| `[[Has type::Page]]`      | `[[Tiene tipo de datos::Página]]`  |
| `[[Has type::Number]]`    | `[[Tiene tipo de datos::Número]]`  |
| `[[Has type::Text]]`      | `[[Tiene tipo de datos::Cadena de caracteres]]` |
| `[[Allows value::Foo]]`   | `[[Permite el valor::Foo]]`        |

Esto importa al inspeccionar el wikitexto de las propiedades (`Property:Autor`, etc.) o al definir nuevas. Los nombres de las propiedades de usuario (no metapropiedades) son simplemente nombres en espanol con tildes.

### Propiedades reales en Casiopea

Casiopea **no** usa el prefijo "Tiene como" que es el default vanilla de SMW. Las propiedades de usuario son nombres directos en espanol, con tildes y mayusculas reales. Lista no exhaustiva descubierta inspeccionando el esquema (ver `esquema-casiopea.md` para la lista completa por clase):

| Propiedad             | Tipo                  | Ejemplo                         |
|-----------------------|-----------------------|---------------------------------|
| Autor                 | Página                | Herbert Spencer                 |
| Coautores             | Página                | Ricardo Lang; Andres Garcés     |
| Año                   | Número                | 2018                            |
| Colección             | Página/Cadena         | Amereida                        |
| Edición               | Cadena                | Primera                         |
| Editorial             | Cadena                | Ediciones e[ad]                 |
| Tipo de Publicación   | Cadena (con enum)     | Ponencia; Proceeding            |
| Carreras Relacionadas | Cadena (con enum)     | Arquitectura; Diseño            |
| Palabras Clave        | Cadena                | Travesía; Patagonia             |
| Título                | Cadena                | Título completo de la obra      |
| Ciudad                | Cadena                | Valparaíso                      |
| Imagen                | Página (File:)        | Carátula.jpg                    |
| Páginas               | Número                | 240                             |

Las propiedades que empiezan con guion bajo (`_ERRC`, `_INST`, `_MDAT`, `_SKEY`, `_cod`) son metadatos internos de SMW; no usarlas en queries de usuario.

### Clases ontologicas core

Casiopea tiene 22 clases ontologicas con formulario asociado (`Form:Nuevo X` o `Form:Nueva X`). Ver `esquema-casiopea.md` para el listado completo con propiedades de cada una.

### Plantillas con sufijo "2"

Existen plantillas `Persona2`, `Proyecto2`, `Travesía2`, etc. Son **pruebas obsoletas** y no deben usarse. La plantilla canonica es siempre la sin sufijo.

## Operaciones de escritura

Todas requieren un CSRF token previo:

```
action=query&meta=tokens&type=csrf
```

El token vive en `query.tokens.csrftoken` y se reusa para todas las escrituras en la sesion.

### action=edit

```
action=edit
title=<titulo>
text=<wikitexto completo>           # reemplaza
appendtext=<wikitexto a anadir>      # alternativo a text
prependtext=<wikitexto a anteponer>  # alternativo a text
section=<numero o nombre>            # opcional, edita una seccion
summary=<descripcion del cambio>
token=<csrf token>
bot=1                                # marca la edicion como hecha por bot
createonly=1                         # falla si la pagina ya existe
```

Respuesta exitosa contiene `edit.result == "Success"` y datos de la nueva revision.

### action=upload

Requiere multipart/form-data porque incluye el binario del archivo:

```
action=upload
filename=<nombre destino>
comment=<descripcion>
text=<wikitexto inicial de la pagina File:>
token=<csrf token>
ignorewarnings=1     # opcional, fuerza upload aunque haya warnings (ej. duplicado)
file=<binario>       # campo multipart con el contenido
```

Respuesta exitosa tiene `upload.result == "Success"` y los metadatos del archivo subido.

## Limites y rate limiting

Los bots tienen limites mas generosos que usuarios anonimos pero igual hay rate limits. Para grandes volumenes:

- Usar `bot=1` en escrituras para que MediaWiki aplique los limites de bot.
- Espaciar requests si se procesan cientos de paginas (300-500 ms entre llamadas como minimo).
- Para descargas masivas, considerar el dump XML de la wiki en vez de iterar via API.

## Errores comunes y respuestas

| Codigo MediaWiki      | Causa probable                                       |
|-----------------------|------------------------------------------------------|
| `WrongPass`           | Usuario sin formato `Usuario@NombreBot`              |
| `NotExists`           | El bot password fue revocado o nunca existio         |
| `articleexists`       | `createonly=1` y la pagina ya existe                 |
| `protectedpage`       | El bot no tiene permiso para editar esa pagina       |
| `badtoken`            | CSRF token expirado, pedir uno nuevo                 |
| `cantcreate-anon`     | El bot perdio sesion, hacer login nuevamente         |
| `verification-error`  | Upload rechazado por extension de archivo no permitida |

## Referencias externas

- API estandar de MediaWiki: https://www.mediawiki.org/wiki/API:Main_page
- API de Semantic MediaWiki action=ask: https://www.semantic-mediawiki.org/wiki/Help:API:ask
- Bot passwords: https://www.mediawiki.org/wiki/Manual:Bot_passwords
- Sintaxis #ask: https://www.semantic-mediawiki.org/wiki/Help:Inline_queries
