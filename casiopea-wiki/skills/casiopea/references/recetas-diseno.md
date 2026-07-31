# Recetas de maquetación Stella Nova

Patrones listos para copiar y adaptar. Presuponen la doctrina de `stella-nova.md`; acá solo está el wikitexto que funciona.

Todo lo que sigue se **previsualiza antes de guardar** con:

```bash
python "$CASIOPEA" parse --from-file borrador.mw --title "Nombre de la página"
```

`parse` renderiza contra la wiki real sin escribir nada, y devuelve advertencias del parser, plantillas usadas y enlaces resueltos. Si una plantilla no existe o una clase está mal escrita, aparece ahí, no en la página publicada.

## Portada a sangre

Primera pantalla limpia, sin colisión con el chrome.

```wiki
__NOTITLE__
__PANTALLACOMPLETA__

[[Archivo:portada.jpg|class=full-width]]

<div class="grid cols-3 gap-l full">
<div class="center">
=== Travesías ===
Una línea de bajada.
</div>
<div class="center">
=== Obras ===
Otra línea.
</div>
<div class="center">
=== Publicaciones ===
Una tercera.
</div>
</div>
```

La imagen debe medir al menos 1600 px de ancho. `full` hace que la grilla ocupe todo el viewport en modo pantalla completa; sin `__PANTALLACOMPLETA__` ocuparía el ancho de la hoja.

## Galería de imágenes que se reacomoda sola

```wiki
<div class="grid cols-auto gap-m">
[[Archivo:a.jpg|frameless]]
[[Archivo:b.jpg|frameless]]
[[Archivo:c.jpg|frameless]]
[[Archivo:d.jpg|frameless]]
</div>
```

`cols-auto` calcula cuántas columnas de al menos 16 rem caben. No hay que declarar breakpoints.

## Bloque destacado sin sacarlo del flujo

```wiki
<div class="fondo-verde">
El fondo sangra a los bordes de la hoja, el texto vuelve al ancho de lectura.
</div>

<div class="fondo-coral grid cols-3">
Tres columnas dentro de una banda a sangre.
</div>

<div class="fondo-opuesto">
Este bloque entero se dibuja en el tema contrario al de la página.
</div>
```

## Ficha clave→valor

```wiki
{| class="wikitable template"
! Autor
| [[Herbert Spencer]]
|-
! Año
| 2026
|-
! Carreras Relacionadas
| Diseño Gráfico
|}
```

La clase `template` (o `plantilla`) solo actúa combinada con `wikitable`. Sin filetes, etiqueta a la derecha en versalita tenue.

## Listado semántico en tarjetas

Este es el caso donde la gente se estrella. Un `#ask` con `format=ul` **no se reparte** en las columnas de una grilla, porque `flujo-v` pone `break-inside: avoid` a los hijos directos y la lista es un solo hijo. La solución es que el propio `#ask` emita una tarjeta por resultado:

```wiki
<div class="grid cols-auto gap-m">
{{#ask: [[Categoría:Travesía]][[Año::2018]]
 |?Destino
 |?Profesores
 |format=template
 |template=Documento miniatura
 |limit=60
}}
</div>
```

Así cada resultado es un hijo directo de la grilla y las columnas funcionan. La plantilla de tarjeta define su propio `/style.css` con tokens semánticos.

## Botonera de navegación

```wiki
<span class="wiki-btn">[[Travesías|Travesías]]</span>
<span class="wiki-btn red">[[Obras|Obras]]</span>
<span class="wiki-btn green">[[Publicaciones|Publicaciones]]</span>
```

Sin líneas en blanco entre los `<span>`: MediaWiki los envuelve en un solo `<p>` y el skin lo hace transparente. Con líneas en blanco cada uno queda en su propio párrafo, que casi nunca es lo que se quiere.

## Plantilla nueva con TemplateStyles

Archivo `Plantilla:Ficha Breve`:

```wiki
<templatestyles src="Plantilla:Ficha Breve/style.css" />
<div class="fbreve">
<div class="fbreve-titulo">{{{titulo|}}}</div>
<div class="fbreve-bajada">{{{bajada|}}}</div>
</div><noinclude>
[[Categoría:Plantillas]]
</noinclude>
```

Archivo `Plantilla:Ficha Breve/style.css`:

```css
.fbreve {
	background: var(--sn-paper-raised);
	border: 1px solid var(--sn-hairline);
	border-radius: var(--sn-radius);
	padding: var(--sn-baseline-half) var(--sn-s-4);
}

.fbreve-titulo {
	color: var(--sn-ink);
	font-weight: 600;
}

.fbreve-bajada {
	color: var(--sn-ink-soft);
	font-family: var(--sn-font-quote);
}
```

Lo que hace que esto pase el sanitizador y funcione en ambos temas: los `var()` van desnudos, el relleno vertical usa `--sn-baseline-half` para cerrar en la retícula, el relleno horizontal usa la escala de espaciado, y `--sn-paper-raised` es un token que ya voltea solo (una plantilla no puede escribir `light-dark()`).

## Tabla que debe estirar sus columnas

El skin pone `display: block` a las tablas para que tengan scroll horizontal en móvil. Si una tabla concreta debe ocupar el 100% y repartir el ancho entre columnas, hay que devolverle `display: table` desde la hoja de la plantilla, acotado:

```css
.mi-plantilla table.wikitable {
	display: table;
	width: 100%;
}
```

Acotado a la plantilla, nunca global: el scroll en móvil está ahí por una razón.

## Verificaciones antes de publicar

```bash
# 1. previsualizar el render y ver advertencias del parser
python "$CASIOPEA" parse --from-file borrador.mw --title "Mi página"

# 2. si se toca una plantilla existente, medir el impacto primero
python "$CASIOPEA" transclusions "Plantilla:Ficha Breve"

# 3. dry-run con diff
python "$CASIOPEA" edit "Mi página" --from-file borrador.mw --summary "..."

# 4. recién ahí, con confirmación explícita de la persona
python "$CASIOPEA" edit "Mi página" --from-file borrador.mw --summary "..." --confirm

# 5. tras tocar una /style.css, purgar la caché de las páginas que la usan
python "$CASIOPEA" purge "Mi página" --confirm
```

El paso 5 se olvida siempre y produce media hora de depurar un cambio que ya estaba bien.
