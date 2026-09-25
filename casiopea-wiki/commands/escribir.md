---
description: "Edita, crea, mueve, sube, borra o restaura paginas en Casiopea. SIEMPRE dry-run con diff y confirmacion explicita antes de aplicar el cambio."
argument-hint: "[instruccion de escritura, ej: agrega seccion X a la pagina Y]"
allowed-tools: ["Bash", "Read", "Write", "Skill"]
---

# Casiopea — modo escritura

Estas en modo escritura de la wiki Casiopea (https://wiki.ead.pucv.cl). Wiki institucional, con historial publico, activa desde 2007. **Cada cambio queda firmado con la cuenta de la persona duena del bot password, no con la tuya.** Un desastre aca lleva su nombre.

1. **Carga el skill `casiopea`** con la herramienta Skill. Trae la resolucion de `$CASIOPEA`, credenciales y el flujo de salvaguarda.

2. **Verbos disponibles:** `edit`, `replace`, `append`, `create`, `move`, `upload`, `upload-from-url`, `delete`, `undelete`, `purge`. Mapea la instruccion al verbo correcto: reemplazar todo→`edit`, cambiar un fragmento→`replace`, anadir→`append`, nueva→`create`, renombrar→`move`, subir→`upload`, borrar→`delete`, restaurar→`undelete`.

3. **Flujo OBLIGATORIO, sin excepciones** (aunque la persona suene apurada o entusiasta):
   1. Confirma el titulo y el contenido o efecto exacto.
   2. Si el contenido lleva maquetacion, plantillas o clases: **previsualizalo con `parse` antes de nada**. Una plantilla mal escrita se ve en el resultado de `parse`, no en el diff.
   3. Corre el comando **sin `--confirm`** (dry-run). Para `edit`/`replace`/`append`/`create` esto imprime un diff unificado; en `edit` y `replace` anota la revision base (`base rN`) y confirma con `--base-rev N`.
   4. Muestra el dry-run al usuario y pide confirmacion explicita.
   5. Solo entonces re-invoca el **mismo** comando agregando `--confirm`.

4. **Mide el impacto antes de destruir.** Antes de mover o borrar una plantilla, `transclusions`; antes de un archivo, `fileusage`. Cero resultados es luz verde; cualquier otro numero es la lista de paginas que se rompen.

5. **Vuelve a traer antes de confirmar.** Las paginas se editan en vivo. Entre que leiste la pagina y propusiste el cambio pudo haber una edicion ajena: re-trae y reconstruye sobre la version actual. Un error `conflict` es exactamente eso.

6. **Despues de tocar una plantilla o su `/style.css`, corre `purge`** sobre las paginas afectadas. Si no, la wiki sigue sirviendo el HTML cacheado y parece que el cambio no funciono.

7. Nunca uses `--confirm` en la primera vuelta. Si la persona no confirma, no escribes.

8. Los borradores se guardan con extension `.mw`.

## Instruccion

$ARGUMENTS
