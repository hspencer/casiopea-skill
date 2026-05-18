# casiopea-skill

Repositorio del plugin **casiopea** (carpeta fuente `casiopea-wiki/`) para Claude Code y Claude Cowork: acceso autenticado a la wiki [Casiopea](https://wiki.ead.pucv.cl) de la Escuela de Arquitectura y Diseño PUCV (una instalación de Semantic MediaWiki). Comandos: `/casiopea:leer`, `/casiopea:consultar`, `/casiopea:escribir`, `/casiopea:auditar`.

## Estructura

```
casiopea-skill/
├── casiopea-wiki/         # Fuente del plugin instalable
│   ├── .claude-plugin/    # Manifiesto (plugin.json)
│   ├── commands/          # /casiopea:leer :consultar :escribir :auditar
│   ├── skills/casiopea/   # Skill: SKILL.md, scripts/, references/
│   └── README.md          # README del plugin (lo que ve el usuario final)
├── docs/                  # Material de referencia que originó el skill
│   ├── ontologia/         # Esquema SMW de Casiopea (clases, propiedades)
│   └── limpieza/          # Notas de auditoría y limpieza de la wiki
├── credentials.example    # Plantilla — copiar a `credentials` y rellenar
├── credentials            # IGNORADO por git (contiene secretos)
├── build.sh               # Reempaqueta casiopea-wiki/ → casiopea-wiki.plugin
├── casiopea-wiki.plugin   # IGNORADO (artefacto de build, generado)
├── LICENSE                # MIT
└── README.md              # Este archivo
```

## Workflow

**1. Setup local.**

```bash
git clone <repo>
cd casiopea-skill
cp credentials.example credentials
chmod 600 credentials
# Editar credentials con los valores reales obtenidos en
# https://wiki.ead.pucv.cl/Special:BotPasswords
```

**2. Build.**

```bash
./build.sh
```

Genera `casiopea-wiki.plugin` en la raíz. Es un zip con la fuente de `casiopea-wiki/`.

**3. Instalar.**

Claude Code:

```bash
claude plugin marketplace add /ruta/a/casiopea-skill
claude plugin install casiopea@ead-pucv
# luego /reload-plugins (o reiniciar)
```

Claude Cowork: doble clic sobre `casiopea-wiki.plugin`, o arrástralo a la ventana de chat.

**4. Uso.**

Cuatro comandos, todos prefijados `/casiopea:`

```text
/casiopea:leer trae la página Amereida
/casiopea:consultar travesías por año a CSV
/casiopea:escribir agrega una sección Notas a la página X
/casiopea:auditar qué cambió hoy
```

También se activa automáticamente cuando mencionas Casiopea, una travesía, una observación u otro contenido de la wiki, sin escribir comando.

## Desarrollo

Las fuentes del plugin viven en `casiopea-wiki/`. Después de cualquier cambio:

```bash
./build.sh           # regenera el .plugin
# arrastrar el .plugin nuevo a Cowork para reinstalar
```

Los documentos en `docs/` no se empaquetan en el plugin; son material de trabajo del administrador de la wiki que sirvió para diseñar el skill (clases ontológicas core, propiedades semánticas, listas de páginas candidatas a limpieza). Mantenerlos versionados ayuda a justificar decisiones del SKILL.md.

## Seguridad

- `credentials` está en `.gitignore`. No debe aparecer nunca en un commit.
- El bot password se otorga con grants mínimos en `Special:BotPasswords`. Para uso de solo lectura basta con `Read pages`.
- Toda escritura (`edit`, `append`, `create`, `delete`, `upload`) hace dry-run obligatorio. El flag `--confirm` es explícito.

## Licencia

MIT. Ver `LICENSE`.
