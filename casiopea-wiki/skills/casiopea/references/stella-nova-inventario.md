# Stella Nova — inventario generado

Archivo **generado** por `casiopea.py sn-sync`. No editarlo a mano: el
siguiente sync lo sobreescribe. La doctrina curada, que sí se escribe a
mano, vive en `stella-nova.md`.

Versión del skin leída del repositorio: **0.7.2**.

## Tokens semánticos (los que consumen las plantillas)

| Token | Valor declarado |
|---|---|
| `--sn-baseline` | `calc(var(--sn-fs-base) * var(--sn-leading))` |
| `--sn-baseline-half` | `calc(var(--sn-baseline) / 2)` |
| `--sn-ctl` | `2.4rem` |
| `--sn-danger` | `light-dark(var(--sn-rojo-600), var(--sn-coral-400))` |
| `--sn-danger-wash` | `color-mix(in oklab, var(--sn-danger) 12%, var(--sn-paper))` |
| `--sn-ease` | `cubic-bezier(.22, 1, .36, 1)` |
| `--sn-edit-surface` | `color-mix(in oklab, var(--sn-ink) 3%, var(--sn-paper))` |
| `--sn-ext-icon` | `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' f...` |
| `--sn-field` | `light-dark(var(--sn-papel-75), var(--sn-tinta-950))` |
| `--sn-font-display` | `var(--sn-font-text)` |
| `--sn-font-mono` | `'IBM Plex Mono', ui-monospace, 'SFMono-Regular', 'Cascadia Code', Menlo, Consolas, mono...` |
| `--sn-font-quote` | `var(--sn-font-serif)` |
| `--sn-font-sans` | `'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif` |
| `--sn-font-scale` | `1` |
| `--sn-font-serif` | `'Roboto Serif', 'Iowan Old Style', Palatino, 'Times New Roman', Georgia, serif` |
| `--sn-font-text` | `var(--sn-font-sans)` |
| `--sn-fs-base` | `calc(clamp(1.04rem, 1rem + .18vw, 1.1rem) * var(--sn-font-scale))` |
| `--sn-fs-display` | `calc(clamp(1.5rem, 1.32rem + .85vw, 2rem) * var(--sn-font-scale))` |
| `--sn-fs-lg` | `calc(clamp(1.2rem, 1.12rem + .40vw, 1.42rem) * var(--sn-font-scale))` |
| `--sn-fs-md` | `calc(clamp(1.15rem, 1.1rem + .24vw, 1.28rem) * var(--sn-font-scale))` |
| `--sn-fs-page-title` | `calc(clamp(1.85rem, 1.55rem + 1.3vw, 2.5rem) * var(--sn-font-scale))` |
| `--sn-fs-root` | `calc(1rem * var(--sn-font-scale))` |
| `--sn-fs-sm` | `clamp(.82rem, .79rem + .14vw, .90rem)` |
| `--sn-fs-table` | `calc(var(--sn-fs-base) * .8)` |
| `--sn-fs-xl` | `calc(clamp(1.35rem, 1.22rem + .55vw, 1.62rem) * var(--sn-font-scale))` |
| `--sn-fs-xs` | `clamp(.72rem, .70rem + .10vw, .78rem)` |
| `--sn-hair` | `1px solid var(--sn-hairline)` |
| `--sn-hairline` | `light-dark(var(--sn-papel-600), var(--sn-tinta-500))` |
| `--sn-hairline-soft` | `light-dark(var(--sn-papel-500), var(--sn-tinta-650))` |
| `--sn-header-h` | `3.5rem` |
| `--sn-icon` | `color-mix(in oklab, var(--sn-ink) 55%, transparent)` |
| `--sn-icon-active` | `var(--sn-ink)` |
| `--sn-info-wash` | `color-mix(in oklab, var(--sn-warn) 8%, var(--sn-paper))` |
| `--sn-ink` | `light-dark(var(--sn-tinta-750), var(--sn-papel-300))` |
| `--sn-ink-faint` | `light-dark(var(--sn-papel-800), var(--sn-tinta-300))` |
| `--sn-ink-soft` | `light-dark(var(--sn-tinta-400), var(--sn-papel-700))` |
| `--sn-leading` | `1.61` |
| `--sn-leading-table` | `1.305` |
| `--sn-lift` | `0 1px 1px rgba(40, 33, 20, .06), 0 8px 6px -3px rgba(40, 33, 20, .16)` |
| `--sn-lift-paper` | `0 1px 1px rgba(40, 33, 20, .03), 0 3px 8px rgba(40, 33, 20, .04)` |
| `--sn-lift-soft` | `0 2px 8px rgba(40, 33, 20, .05)` |
| `--sn-link` | `light-dark(var(--sn-rojo-500), var(--sn-coral-400))` |
| `--sn-link-hover` | `light-dark(var(--sn-rojo-700), color-mix(in oklab, var(--sn-coral-400) 80%, white))` |
| `--sn-link-new` | `light-dark(var(--sn-rosa-400), var(--sn-rosa-300))` |
| `--sn-link-visited` | `light-dark(var(--sn-rojo-900), color-mix(in oklab, var(--sn-coral-400) 75%, black))` |
| `--sn-measure` | `64rem` |
| `--sn-motion` | `1` |
| `--sn-notice-bg` | `light-dark(var(--sn-masking-300), var(--sn-masking-900))` |
| `--sn-notice-ink` | `light-dark(var(--sn-tinta-600), var(--sn-masking-300))` |
| `--sn-nova` | `light-dark(var(--sn-rojo-500), var(--sn-coral-400))` |
| `--sn-nova-ink` | `light-dark(var(--sn-blanco), var(--sn-tinta-850))` |
| `--sn-nova-wash` | `light-dark(#f7e9e6, #2b1c1d)` |
| `--sn-ok` | `light-dark(var(--sn-verde-500), var(--sn-verde-400))` |
| `--sn-ok-wash` | `color-mix(in oklab, var(--sn-ok) 14%, var(--sn-paper))` |
| `--sn-paper` | `light-dark(var(--sn-papel-50), var(--sn-tinta-800))` |
| `--sn-paper-edge` | `light-dark(var(--sn-papel-100), var(--sn-tinta-700))` |
| `--sn-paper-raised` | `light-dark(var(--sn-blanco), var(--sn-tinta-950))` |
| `--sn-poem-size` | `85%` |
| `--sn-poem-weight` | `500` |
| `--sn-poem-width` | `77%` |
| `--sn-radius` | `4px` |
| `--sn-radius-l` | `8px` |
| `--sn-radius-paper` | `3px` |
| `--sn-radius-pill` | `999px` |
| `--sn-radius-s` | `2px` |
| `--sn-rail` | `15.5rem` |
| `--sn-scrim` | `color-mix(in oklab, var(--sn-ink) 45%, transparent)` |
| `--sn-serif-grade` | `70` |
| `--sn-serif-size-adjust` | `0.516` |
| `--sn-shell` | `81rem` |
| `--sn-sunk` | `light-dark(var(--sn-papel-200), var(--sn-tinta-900))` |
| `--sn-text-width` | `80%` |
| `--sn-warn` | `light-dark(var(--sn-masking-700), var(--sn-masking-500))` |
| `--sn-warn-ink` | `light-dark(var(--sn-papel-50), var(--sn-tinta-850))` |
| `--sn-warn-wash` | `color-mix(in oklab, var(--sn-warn) 14%, var(--sn-paper))` |
| `--sn-z-header` | `910` |
| `--sn-z-panel` | `920` |
| `--sn-z-rail` | `900` |
| `--sn-z-skip` | `930` |

## Tokens de componente (chrome del skin, rara vez en plantillas)

| Token | Valor declarado |
|---|---|
| `--sn-btn-bg` | `var(--sn-sunk)` |
| `--sn-btn-bg-hover` | `var(--sn-paper)` |
| `--sn-btn-border` | `var(--sn-hairline)` |
| `--sn-btn-border-hover` | `var(--sn-ink-faint)` |
| `--sn-btn-danger-bg` | `var(--sn-danger)` |
| `--sn-btn-danger-fg` | `var(--sn-nova-ink)` |
| `--sn-btn-fg` | `var(--sn-ink)` |
| `--sn-btn-primary-bg` | `var(--sn-ink)` |
| `--sn-btn-primary-bg-hover` | `color-mix(in oklab, var(--sn-ink) 86%, var(--sn-paper))` |
| `--sn-btn-primary-fg` | `var(--sn-paper)` |
| `--sn-field-bg` | `var(--sn-paper)` |
| `--sn-field-bg-disabled` | `var(--sn-sunk)` |
| `--sn-field-border` | `var(--sn-hairline)` |
| `--sn-field-fg` | `var(--sn-ink)` |
| `--sn-field-grain` | `0.035` |
| `--sn-field-placeholder` | `var(--sn-ink-faint)` |
| `--sn-focus-border` | `var(--sn-nova)` |
| `--sn-focus-ring` | `0 0 0 2px var(--sn-nova-wash)` |
| `--sn-on-bg` | `var(--sn-ink)` |
| `--sn-on-fg` | `var(--sn-paper)` |
| `--sn-opt-fg` | `var(--sn-ink)` |
| `--sn-opt-hover-bg` | `var(--sn-sunk)` |
| `--sn-opt-sel-bg` | `var(--sn-nova-wash)` |

## Primitivas (paleta interna, no usar en plantillas)

| Primitiva | Valor |
|---|---|
| `--sn-azul-200` | `#b3cef2` |
| `--sn-azul-300` | `#8fb4e8` |
| `--sn-baseline-2` | `calc(var(--sn-baseline) * 2)` |
| `--sn-baseline-3` | `calc(var(--sn-baseline) * 3)` |
| `--sn-blanco` | `#ffffff` |
| `--sn-coral-300` | `#c8a89a` |
| `--sn-coral-400` | `#ff6b7e` |
| `--sn-dur-1` | `calc(120ms * var(--sn-motion))` |
| `--sn-dur-2` | `calc(220ms * var(--sn-motion))` |
| `--sn-dur-3` | `calc(420ms * var(--sn-motion))` |
| `--sn-malva-400` | `#a99cae` |
| `--sn-masking-300` | `#f7db7e` |
| `--sn-masking-500` | `#d9a14b` |
| `--sn-masking-700` | `#8a5a12` |
| `--sn-masking-900` | `#5a4416` |
| `--sn-papel-100` | `#f3f0e7` |
| `--sn-papel-200` | `#efece2` |
| `--sn-papel-300` | `#ece7da` |
| `--sn-papel-400` | `#e8e4da` |
| `--sn-papel-50` | `#fcfbf7` |
| `--sn-papel-500` | `#e7e1d3` |
| `--sn-papel-600` | `#ddd6c7` |
| `--sn-papel-700` | `#a39a86` |
| `--sn-papel-75` | `#f4f2ed` |
| `--sn-papel-800` | `#968c7c` |
| `--sn-rojo-500` | `#ae2d13` |
| `--sn-rojo-600` | `#b21e3e` |
| `--sn-rojo-700` | `#962c08` |
| `--sn-rojo-900` | `#612403` |
| `--sn-rosa-300` | `#e6acb7` |
| `--sn-rosa-400` | `#a94f66` |
| `--sn-s-1` | `.25rem` |
| `--sn-s-4` | `1rem` |
| `--sn-s-7` | `3.5rem` |
| `--sn-tinta-300` | `#756d5d` |
| `--sn-tinta-400` | `#6b6357` |
| `--sn-tinta-500` | `#353123` |
| `--sn-tinta-600` | `#2c2410` |
| `--sn-tinta-650` | `#2a2719` |
| `--sn-tinta-700` | `#262318` |
| `--sn-tinta-750` | `#221f1a` |
| `--sn-tinta-800` | `#1e1c15` |
| `--sn-tinta-850` | `#1a0f0b` |
| `--sn-tinta-900` | `#181610` |
| `--sn-tinta-950` | `#141209` |
| `--sn-verde-400` | `#6cc18a` |
| `--sn-verde-500` | `#2f6f43` |

## Clases opt-in documentadas en el repositorio

- `fondo-*`
- `full-width`
- `fw-*`
- `grid`
- `img-circle`
- `noprint`
- `sn-notice`
- `template`
- `wiki-btn`

Regenerar con:

```bash
python casiopea.py sn-sync
```
