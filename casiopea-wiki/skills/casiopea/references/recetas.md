# Recetas de query SMW para Casiopea

Queries `ask` listas para usar, con las propiedades reales del esquema (tildes y
mayusculas exactas). El script pagina solo por offset hasta `--max`, asi que
estas recetas devuelven la categoria completa, no las primeras ~50 filas.

Convencion: `$CASIOPEA` es la ruta resuelta al script (ver SKILL.md).

## Travesias

Todas las travesias de un anio, con destino y profesores:

```bash
python "$CASIOPEA" ask '[[Category:Travesía]][[Año::2018]]|?Destino|?Profesores|?Fecha de Inicio' --format csv
```

Travesias por destino (la propiedad es `Destino`, no "Tiene destino"):

```bash
python "$CASIOPEA" ask '[[Category:Travesía]][[Destino::Patagonia]]|?Año|?Profesores' --format table
```

Todas las travesias ordenadas por anio, exportadas a CSV:

```bash
python "$CASIOPEA" ask '[[Category:Travesía]]|?Año|?Destino|?Profesores|?Alumnos|sort=Año|order=desc' --format csv --max 2000
```

## Publicaciones y bibliografia

Publicaciones de un autor:

```bash
python "$CASIOPEA" ask '[[Category:Publicación]][[Autor::Herbert Spencer]]|?Año|?Tipo de Publicación|?Revista' --format csv
```

Publicaciones de un anio por tipo:

```bash
python "$CASIOPEA" ask '[[Category:Publicación]][[Año::2023]]|?Autor|?Tipo de Publicación|?Indexación' --format csv
```

Bibliografia de una asignatura:

```bash
python "$CASIOPEA" ask '[[Category:Bibliografía]][[Asignaturas Relacionadas::Taller de Diseño]]|?Autor|?Año|?Editorial' --format table
```

## Personas

Profesores de la escuela (relacion con la escuela):

```bash
python "$CASIOPEA" ask '[[Category:Persona]][[Relación con la Escuela::Profesor]]|?Apellido|?Jerarquía Académica|?Email' --format csv --max 2000
```

Personas que ingresaron un anio dado:

```bash
python "$CASIOPEA" ask '[[Category:Persona]][[Año de Ingreso a la Escuela::1992]]|?Nombre|?Apellido' --format table
```

## Proyectos y observaciones

Proyectos por tipo y anio de inicio:

```bash
python "$CASIOPEA" ask '[[Category:Proyecto]][[Tipo de Proyecto::Proyecto de Taller]]|?Año de Inicio|?Profesor|?Carreras Relacionadas' --format csv
```

Observaciones de un proyecto (propiedad `Proyectos Relacionados`):

```bash
python "$CASIOPEA" ask '[[Category:Observación]][[Proyectos Relacionados::Amereida]]|?Palabras Clave|?Páginas Relacionadas' --format table
```

## Cursos y travesias asociadas

Cursos de un anio con sus talleres y profesores:

```bash
python "$CASIOPEA" ask '[[Category:Curso]][[Año::2024]]|?Profesores|?Talleres|?Período Académico' --format csv
```

## Exportar una categoria completa a CSV

Patron general (subir `--max` si la categoria es grande):

```bash
python "$CASIOPEA" ask '[[Category:NOMBRE]]|?Prop1|?Prop2|?Prop3' --format csv --max 5000 > salida.csv
```

Si no se conocen las propiedades de la clase, mirar `esquema-casiopea.md`
(seccion de esa clase) o correr `browse` sobre una pagina representativa.

## Auditoria y limpieza (admin)

Cambios recientes excluyendo bots, ultimos 100:

```bash
python "$CASIOPEA" recentchanges --limit 100 --no-bots
```

Historial de una pagina para ver quien la edito:

```bash
python "$CASIOPEA" history "Plantilla:Travesía" --limit 30
```

### Flujo: decidir si una plantilla `*2` (prueba) es segura de borrar

Las plantillas con sufijo `2` (`Persona2`, `Proyecto2`, `Curso2`, etc.) son
pruebas obsoletas. Antes de borrar cada una, medir su impacto real:

```bash
python "$CASIOPEA" transclusions "Plantilla:Mis Cursos2"      # 0 usos -> segura
python "$CASIOPEA" transclusions "Plantilla:Persona2"          # revisa ns0 (contenido real)
```

Regla: si `transclusions` solo lista paginas de Discusion (`Discusión:`/
`Plantilla discusión:`) la plantilla es segura; si aparece una pagina de
contenido real (sin prefijo de namespace), esa pagina hay que migrarla a la
plantilla canonica (sin sufijo) **antes** de borrar.

Para un archivo, el equivalente antes de borrar:

```bash
python "$CASIOPEA" fileusage "Diagrama_viejo.png"              # 0 usos -> seguro
```

### Renombrar dejando el contenido sano

Mover una plantilla/pagina conservando enlaces (deja redirect):

```bash
python "$CASIOPEA" move "Plantilla:Nombre Malo" "Plantilla:Nombre Bueno" --reason "Normalizacion" --confirm
```

Recordar: primero el dry-run sin `--confirm`, mostrar al usuario, y solo
entonces re-invocar con `--confirm`.
