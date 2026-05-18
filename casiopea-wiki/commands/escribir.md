---
description: "Edita, crea, mueve, sube o borra paginas en Casiopea. SIEMPRE dry-run con diff y confirmacion explicita del usuario antes de aplicar el cambio."
argument-hint: "[instruccion de escritura, ej: agrega seccion X a la pagina Y]"
allowed-tools: ["Bash", "Read", "Skill"]
---

# Casiopea — modo escritura

Estas en modo escritura de la wiki Casiopea (https://wiki.ead.pucv.cl). Es una wiki institucional con historial; cada cambio queda firmado como bot y atribuido en RecentChanges.

1. **Carga el skill `casiopea`** con la herramienta Skill. Trae la resolucion de `$CASIOPEA`, credenciales y el flujo de salvaguarda.

2. **Verbos disponibles:** `edit`, `append`, `create`, `move`, `upload`, `delete`. Mapea la instruccion al verbo correcto (reemplazar→`edit`, anadir→`append`, nueva→`create`, renombrar→`move`, subir archivo→`upload`, borrar→`delete`).

3. **Flujo OBLIGATORIO, sin excepciones** (aunque el usuario suene apurado o entusiasta):
   1. Confirma con el usuario el titulo y el contenido/efecto exacto.
   2. Corre el comando **sin `--confirm`** (dry-run). Para `edit`/`append`/`create` esto imprime un **diff unificado**.
   3. Muestra el dry-run/diff al usuario y pide confirmacion explicita ("lo confirmo" o equivalente).
   4. Solo entonces re-invoca el **mismo** comando agregando `--confirm`.

   Antes de mover/borrar una plantilla corre `transclusions`; antes de un archivo, `fileusage` (mide el impacto). `delete` requiere el grant `Delete pages` y es casi irreversible: extra cuidado.

4. Nunca uses `--confirm` en la primera vuelta. Si el usuario no confirma, no escribas.

5. Si no hay argumento, pregunta que pagina y que cambio.

## Instruccion

$ARGUMENTS
