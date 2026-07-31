---
description: "Disena y maqueta paginas o plantillas de Casiopea respetando Stella Nova: tokens semanticos, grilla, clases opt-in y TemplateStyles. Previsualiza con parse antes de guardar."
argument-hint: "[que maquetar, ej: una portada a sangre para el taller de X]"
allowed-tools: ["Bash", "Read", "Write", "Skill"]
---

# Casiopea — modo maquetacion

Estas disenando para Casiopea, que tiene sistema de diseno propio: el skin **Stella Nova**. No es una wiki donde se improvisa CSS.

1. **Carga el skill `casiopea`** con la herramienta Skill.

2. **Carga `references/stella-nova.md` antes de escribir una sola clase.** Contiene los tokens semanticos, las clases opt-in del skin, la grilla y —lo mas importante— lo que el sanitizador de TemplateStyles rechaza. Para patrones concretos, `references/recetas-diseno.md`. Para la lista completa de tokens con sus valores, `references/stella-nova-inventario.md`.

3. **Las reglas que no se negocian:**
   - Ningun color literal. Tokens semanticos: `var(--sn-ink)`, `var(--sn-paper)`, `var(--sn-hairline)`. Nunca `#000`, `#fff`, ni una primitiva como `--sn-rojo-500`.
   - `var()` **sin valor de respaldo**. Con respaldo la hoja no se guarda.
   - Nada de `light-dark()`, `:is()`, `font-stretch` en porcentaje literal ni divisiones dentro de `calc()`: el sanitizador los rechaza.
   - Maquetacion con `grid` / `grilla`, no con tablas ni con clases de Bootstrap.
   - Relleno vertical con `--sn-baseline*`, no con `--sn-s-*`.

4. **Escribe el borrador en un archivo `.mw`** y previsualizalo:

   ```bash
   python "$CASIOPEA" parse --from-file borrador.mw --title "Nombre de la pagina"
   ```

   Esto reporta plantillas invocadas que no existen, enlaces rojos y advertencias del parser, **sin tocar la wiki**. Resuelve todo lo que aparezca antes de seguir.

5. **Si tocas una plantilla existente**, corre `transclusions` primero: te dice cuantas paginas dependen de ella. Un cambio de estilo en una plantilla usada por 400 fichas es un cambio en 400 paginas.

6. **Para publicar, pasa a `/casiopea:escribir`** o sigue su flujo: dry-run, diff, confirmacion explicita, y recien ahi `--confirm`. Despues, `purge` sobre las paginas afectadas.

7. **Antes de inventar una clase o un token nuevo, no lo hagas.** El set se mantiene chico a proposito. Propone la necesidad y espera respuesta humana.

8. Si no hay argumento, pregunta que se quiere maquetar y para que pagina.

## Instruccion

$ARGUMENTS
