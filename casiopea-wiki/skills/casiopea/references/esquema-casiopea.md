# Esquema ontologico de Casiopea

Las 22 clases ontologicas core de la wiki Casiopea, con las propiedades que define cada plantilla y los campos que expone su formulario `Nuevo X` o `Nueva X` correspondiente.

Esta referencia se descubrio inspeccionando el wikitexto de las plantillas y formularios. Las propiedades listadas son las que la plantilla setea via `[[Propiedad::valor]]`. Para queries semanticas, usar exactamente estos nombres con sus tildes y espacios.

## Indice de clases

- [Acto](#acto) (13 propiedades)
- [Asignatura](#asignatura) (29 propiedades)
- [Bibliografía](#bibliografia) (14 propiedades)
- [Caso de Estudio](#caso-de-estudio) (15 propiedades)
- [Clase](#clase) (3 propiedades)
- [Curso](#curso) (13 propiedades)
- [Evento](#evento) (18 propiedades)
- [Exposición](#exposicion) (8 propiedades)
- [Obra](#obra) (18 propiedades)
- [Objeto de Archivo](#objeto-de-archivo) (29 propiedades)
- [Observación](#observacion) (3 propiedades)
- [Página de Cuaderno](#pagina-de-cuaderno) (9 propiedades)
- [Persona](#persona) (12 propiedades)
- [Presencia en la Sociedad](#presencia-en-la-sociedad) (14 propiedades)
- [Proyecto](#proyecto) (11 propiedades)
- [Proyecto de Investigación](#proyecto-de-investigacion) (15 propiedades)
- [Proyecto de Vinculación con el Medio](#proyecto-de-vinculacion-con-el-medio) (13 propiedades)
- [Publicación](#publicacion) (23 propiedades)
- [Revista Académica](#revista-academica) (16 propiedades)
- [Tarea](#tarea) (6 propiedades)
- [Trabajo en MADLAB](#trabajo-en-madlab) (7 propiedades)
- [Travesía](#travesia) (12 propiedades)

## Acto

- **Plantilla:** [Plantilla:Acto](https://wiki.ead.pucv.cl/Plantilla:Acto)
- **Formulario:** [Form:Nuevo Acto](https://wiki.ead.pucv.cl/Form:Nuevo_Acto)
- **Categoria:** [Category:Acto](https://wiki.ead.pucv.cl/Category:Acto)

### Propiedades semanticas (13)

- [Autor](https://wiki.ead.pucv.cl/Property:Autor)
- [Año](https://wiki.ead.pucv.cl/Property:Año)
- [Coautores](https://wiki.ead.pucv.cl/Property:Coautores)
- [Descripción](https://wiki.ead.pucv.cl/Property:Descripción)
- [Estado en Archivo JVA](https://wiki.ead.pucv.cl/Property:Estado_en_Archivo_JVA)
- [Fecha](https://wiki.ead.pucv.cl/Property:Fecha)
- [Fuente de Financiamiento](https://wiki.ead.pucv.cl/Property:Fuente_de_Financiamiento)
- [Lugar](https://wiki.ead.pucv.cl/Property:Lugar)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Participantes](https://wiki.ead.pucv.cl/Property:Participantes)
- [Talleres Relacionados](https://wiki.ead.pucv.cl/Property:Talleres_Relacionados)
- [Tipo de Acto](https://wiki.ead.pucv.cl/Property:Tipo_de_Acto)
- [Título](https://wiki.ead.pucv.cl/Property:Título)

### Query semantica de ejemplo

```
[[Category:Acto]]|?Autor|?Año|?Coautores|limit=20
```

## Asignatura

- **Plantilla:** [Plantilla:Asignatura](https://wiki.ead.pucv.cl/Plantilla:Asignatura)
- **Formulario:** [Form:Nueva Asignatura](https://wiki.ead.pucv.cl/Form:Nueva_Asignatura)
- **Categoria:** [Category:Asignatura](https://wiki.ead.pucv.cl/Category:Asignatura)

### Propiedades semanticas (29)

- [Asignatura Homologada](https://wiki.ead.pucv.cl/Property:Asignatura_Homologada)
- [Bibliografía](https://wiki.ead.pucv.cl/Property:Bibliografía)
- [Bibliografía Complementaria](https://wiki.ead.pucv.cl/Property:Bibliografía_Complementaria)
- [Carreras Relacionadas](https://wiki.ead.pucv.cl/Property:Carreras_Relacionadas)
- [Ciclo Formativo](https://wiki.ead.pucv.cl/Property:Ciclo_Formativo)
- [Clave](https://wiki.ead.pucv.cl/Property:Clave)
- [Competencias Disciplinares](https://wiki.ead.pucv.cl/Property:Competencias_Disciplinares)
- [Competencias Fundamentales](https://wiki.ead.pucv.cl/Property:Competencias_Fundamentales)
- [Competencias Profesionales](https://wiki.ead.pucv.cl/Property:Competencias_Profesionales)
- [Contenidos](https://wiki.ead.pucv.cl/Property:Contenidos)
- [Criterios de Evaluación](https://wiki.ead.pucv.cl/Property:Criterios_de_Evaluación)
- [Créditos](https://wiki.ead.pucv.cl/Property:Créditos)
- [Currículum](https://wiki.ead.pucv.cl/Property:Currículum)
- [Descripción](https://wiki.ead.pucv.cl/Property:Descripción)
- [Estrategias de Enseñanza](https://wiki.ead.pucv.cl/Property:Estrategias_de_Enseñanza)
- [Horas Teóricas](https://wiki.ead.pucv.cl/Property:Horas_Teóricas)
- [Horas de Ayudantía](https://wiki.ead.pucv.cl/Property:Horas_de_Ayudantía)
- [Horas de Taller](https://wiki.ead.pucv.cl/Property:Horas_de_Taller)
- [Horas de Trabajo](https://wiki.ead.pucv.cl/Property:Horas_de_Trabajo)
- [Línea de Estudio](https://wiki.ead.pucv.cl/Property:Línea_de_Estudio)
- [Mención](https://wiki.ead.pucv.cl/Property:Mención)
- [Período Académico](https://wiki.ead.pucv.cl/Property:Período_Académico)
- [Pre-requisito](https://wiki.ead.pucv.cl/Property:Pre-requisito)
- [Profesores](https://wiki.ead.pucv.cl/Property:Profesores)
- [Profesores Anteriores](https://wiki.ead.pucv.cl/Property:Profesores_Anteriores)
- [Resultados de Aprendizaje](https://wiki.ead.pucv.cl/Property:Resultados_de_Aprendizaje)
- [Régimen](https://wiki.ead.pucv.cl/Property:Régimen)
- [Tipo de Asignatura](https://wiki.ead.pucv.cl/Property:Tipo_de_Asignatura)
- [Área de Estudio](https://wiki.ead.pucv.cl/Property:Área_de_Estudio)

### Query semantica de ejemplo

```
[[Category:Asignatura]]|?Asignatura Homologada|?Bibliografía|?Bibliografía Complementaria|limit=20
```

## Bibliografía

- **Plantilla:** [Plantilla:Bibliografía](https://wiki.ead.pucv.cl/Plantilla:Bibliografía)
- **Formulario:** [Form:Nueva Bibliografía](https://wiki.ead.pucv.cl/Form:Nueva_Bibliografía)
- **Categoria:** [Category:Bibliografía](https://wiki.ead.pucv.cl/Category:Bibliografía)

### Propiedades semanticas (14)

- [Asignaturas Relacionadas](https://wiki.ead.pucv.cl/Property:Asignaturas_Relacionadas)
- [Autor](https://wiki.ead.pucv.cl/Property:Autor)
- [Año](https://wiki.ead.pucv.cl/Property:Año)
- [Carreras Relacionadas](https://wiki.ead.pucv.cl/Property:Carreras_Relacionadas)
- [Coautores](https://wiki.ead.pucv.cl/Property:Coautores)
- [Cursos Relacionados](https://wiki.ead.pucv.cl/Property:Cursos_Relacionados)
- [Código](https://wiki.ead.pucv.cl/Property:Código)
- [Editorial](https://wiki.ead.pucv.cl/Property:Editorial)
- [Nota](https://wiki.ead.pucv.cl/Property:Nota)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Proyectos Relacionados](https://wiki.ead.pucv.cl/Property:Proyectos_Relacionados)
- [Tipo de Publicación](https://wiki.ead.pucv.cl/Property:Tipo_de_Publicación)
- [Título](https://wiki.ead.pucv.cl/Property:Título)
- [URL](https://wiki.ead.pucv.cl/Property:URL)

### Query semantica de ejemplo

```
[[Category:Bibliografía]]|?Asignaturas Relacionadas|?Autor|?Año|limit=20
```

## Caso de Estudio

- **Plantilla:** [Plantilla:Caso de Estudio](https://wiki.ead.pucv.cl/Plantilla:Caso_de_Estudio)
- **Formulario:** [Form:Nuevo Caso de Estudio](https://wiki.ead.pucv.cl/Form:Nuevo_Caso_de_Estudio)
- **Categoria:** [Category:Caso de Estudio](https://wiki.ead.pucv.cl/Category:Caso_de_Estudio)

### Propiedades semanticas (15)

- [Alumnos](https://wiki.ead.pucv.cl/Property:Alumnos)
- [Autor](https://wiki.ead.pucv.cl/Property:Autor)
- [Cursos Relacionados](https://wiki.ead.pucv.cl/Property:Cursos_Relacionados)
- [Descripción](https://wiki.ead.pucv.cl/Property:Descripción)
- [Descripción Corta](https://wiki.ead.pucv.cl/Property:Descripción_Corta)
- [Desde](https://wiki.ead.pucv.cl/Property:Desde)
- [Dimensiones](https://wiki.ead.pucv.cl/Property:Dimensiones)
- [Hasta](https://wiki.ead.pucv.cl/Property:Hasta)
- [Lugar](https://wiki.ead.pucv.cl/Property:Lugar)
- [Materialidad](https://wiki.ead.pucv.cl/Property:Materialidad)
- [Nombre](https://wiki.ead.pucv.cl/Property:Nombre)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Período](https://wiki.ead.pucv.cl/Property:Período)
- [Proyectos Relacionados](https://wiki.ead.pucv.cl/Property:Proyectos_Relacionados)
- [URL](https://wiki.ead.pucv.cl/Property:URL)

### Query semantica de ejemplo

```
[[Category:Caso de Estudio]]|?Alumnos|?Autor|?Cursos Relacionados|limit=20
```

## Clase

- **Plantilla:** [Plantilla:Clase](https://wiki.ead.pucv.cl/Plantilla:Clase)
- **Formulario:** [Form:Nueva Clase](https://wiki.ead.pucv.cl/Form:Nueva_Clase)
- **Categoria:** [Category:Clase](https://wiki.ead.pucv.cl/Category:Clase)

### Propiedades semanticas (3)

- [Asignaturas Relacionadas](https://wiki.ead.pucv.cl/Property:Asignaturas_Relacionadas)
- [Cursos Relacionados](https://wiki.ead.pucv.cl/Property:Cursos_Relacionados)
- [Profesores](https://wiki.ead.pucv.cl/Property:Profesores)

### Query semantica de ejemplo

```
[[Category:Clase]]|?Asignaturas Relacionadas|?Cursos Relacionados|?Profesores|limit=20
```

## Curso

- **Plantilla:** [Plantilla:Curso](https://wiki.ead.pucv.cl/Plantilla:Curso)
- **Formulario:** [Form:Nuevo Curso](https://wiki.ead.pucv.cl/Form:Nuevo_Curso)
- **Categoria:** [Category:Curso](https://wiki.ead.pucv.cl/Category:Curso)

### Propiedades semanticas (13)

- [Alumnos](https://wiki.ead.pucv.cl/Property:Alumnos)
- [Asignaturas Relacionadas](https://wiki.ead.pucv.cl/Property:Asignaturas_Relacionadas)
- [Ayudantes](https://wiki.ead.pucv.cl/Property:Ayudantes)
- [Año](https://wiki.ead.pucv.cl/Property:Año)
- [Carreras Relacionadas](https://wiki.ead.pucv.cl/Property:Carreras_Relacionadas)
- [Docencia Vinculada](https://wiki.ead.pucv.cl/Property:Docencia_Vinculada)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Período Académico](https://wiki.ead.pucv.cl/Property:Período_Académico)
- [Profesores](https://wiki.ead.pucv.cl/Property:Profesores)
- [Profesores Invitados](https://wiki.ead.pucv.cl/Property:Profesores_Invitados)
- [Talleres](https://wiki.ead.pucv.cl/Property:Talleres)
- [Tipo de Curso](https://wiki.ead.pucv.cl/Property:Tipo_de_Curso)
- [Vinculación con el Medio](https://wiki.ead.pucv.cl/Property:Vinculación_con_el_Medio)

### Query semantica de ejemplo

```
[[Category:Curso]]|?Alumnos|?Asignaturas Relacionadas|?Ayudantes|limit=20
```

## Evento

- **Plantilla:** [Plantilla:Evento](https://wiki.ead.pucv.cl/Plantilla:Evento)
- **Formulario:** [Form:Nuevo Evento](https://wiki.ead.pucv.cl/Form:Nuevo_Evento)
- **Categoria:** [Category:Evento](https://wiki.ead.pucv.cl/Category:Evento)

### Propiedades semanticas (18)

- [Audiencia Estimada](https://wiki.ead.pucv.cl/Property:Audiencia_Estimada)
- [Año](https://wiki.ead.pucv.cl/Property:Año)
- [Estado en Archivo JVA](https://wiki.ead.pucv.cl/Property:Estado_en_Archivo_JVA)
- [Fecha](https://wiki.ead.pucv.cl/Property:Fecha)
- [Fecha de Inicio](https://wiki.ead.pucv.cl/Property:Fecha_de_Inicio)
- [Fecha de Término](https://wiki.ead.pucv.cl/Property:Fecha_de_Término)
- [Fuente de Financiamiento](https://wiki.ead.pucv.cl/Property:Fuente_de_Financiamiento)
- [Institución Contraparte](https://wiki.ead.pucv.cl/Property:Institución_Contraparte)
- [Lugar](https://wiki.ead.pucv.cl/Property:Lugar)
- [Nombre](https://wiki.ead.pucv.cl/Property:Nombre)
- [Organizador](https://wiki.ead.pucv.cl/Property:Organizador)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Participantes](https://wiki.ead.pucv.cl/Property:Participantes)
- [Presencias en la Sociedad Relacionadas](https://wiki.ead.pucv.cl/Property:Presencias_en_la_Sociedad_Relacionadas)
- [Rol de la Contraparte](https://wiki.ead.pucv.cl/Property:Rol_de_la_Contraparte)
- [Rol de la Escuela](https://wiki.ead.pucv.cl/Property:Rol_de_la_Escuela)
- [Tipo de Evento](https://wiki.ead.pucv.cl/Property:Tipo_de_Evento)
- [URL](https://wiki.ead.pucv.cl/Property:URL)

### Query semantica de ejemplo

```
[[Category:Evento]]|?Audiencia Estimada|?Año|?Estado en Archivo JVA|limit=20
```

## Exposición

- **Plantilla:** [Plantilla:Exposición](https://wiki.ead.pucv.cl/Plantilla:Exposición)
- **Formulario:** [Form:Nueva Exposición](https://wiki.ead.pucv.cl/Form:Nueva_Exposición)
- **Categoria:** [Category:Exposición](https://wiki.ead.pucv.cl/Category:Exposición)

### Propiedades semanticas (8)

- [Autor](https://wiki.ead.pucv.cl/Property:Autor)
- [Año](https://wiki.ead.pucv.cl/Property:Año)
- [Ciudad](https://wiki.ead.pucv.cl/Property:Ciudad)
- [Coautores](https://wiki.ead.pucv.cl/Property:Coautores)
- [Fecha](https://wiki.ead.pucv.cl/Property:Fecha)
- [Lugar](https://wiki.ead.pucv.cl/Property:Lugar)
- [Nota](https://wiki.ead.pucv.cl/Property:Nota)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)

### Query semantica de ejemplo

```
[[Category:Exposición]]|?Autor|?Año|?Ciudad|limit=20
```

## Obra

- **Plantilla:** [Plantilla:Obra](https://wiki.ead.pucv.cl/Plantilla:Obra)
- **Formulario:** [Form:Nueva Obra](https://wiki.ead.pucv.cl/Form:Nueva_Obra)
- **Categoria:** [Category:Obra](https://wiki.ead.pucv.cl/Category:Obra)

### Propiedades semanticas (18)

- [Autor](https://wiki.ead.pucv.cl/Property:Autor)
- [Coautores](https://wiki.ead.pucv.cl/Property:Coautores)
- [Descripción](https://wiki.ead.pucv.cl/Property:Descripción)
- [Desde](https://wiki.ead.pucv.cl/Property:Desde)
- [Dimensiones](https://wiki.ead.pucv.cl/Property:Dimensiones)
- [Documentos](https://wiki.ead.pucv.cl/Property:Documentos)
- [Hasta](https://wiki.ead.pucv.cl/Property:Hasta)
- [Lugar](https://wiki.ead.pucv.cl/Property:Lugar)
- [Materialidad](https://wiki.ead.pucv.cl/Property:Materialidad)
- [Nombre](https://wiki.ead.pucv.cl/Property:Nombre)
- [Nota](https://wiki.ead.pucv.cl/Property:Nota)
- [Oficios Relacionados](https://wiki.ead.pucv.cl/Property:Oficios_Relacionados)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Período](https://wiki.ead.pucv.cl/Property:Período)
- [Ronda](https://wiki.ead.pucv.cl/Property:Ronda)
- [URL](https://wiki.ead.pucv.cl/Property:URL)
- [Ámbito Geográfico](https://wiki.ead.pucv.cl/Property:Ámbito_Geográfico)
- [Área de Investigación](https://wiki.ead.pucv.cl/Property:Área_de_Investigación)

### Query semantica de ejemplo

```
[[Category:Obra]]|?Autor|?Coautores|?Descripción|limit=20
```

## Objeto de Archivo

- **Plantilla:** [Plantilla:Objeto de Archivo](https://wiki.ead.pucv.cl/Plantilla:Objeto_de_Archivo)
- **Formulario:** [Form:Nuevo Objeto de Archivo](https://wiki.ead.pucv.cl/Form:Nuevo_Objeto_de_Archivo)
- **Categoria:** [Category:Objeto de Archivo](https://wiki.ead.pucv.cl/Category:Objeto_de_Archivo)

### Propiedades semanticas (29)

- [Actividad](https://wiki.ead.pucv.cl/Property:Actividad)
- [Acto](https://wiki.ead.pucv.cl/Property:Acto)
- [Alto](https://wiki.ead.pucv.cl/Property:Alto)
- [Ancho](https://wiki.ead.pucv.cl/Property:Ancho)
- [Autor](https://wiki.ead.pucv.cl/Property:Autor)
- [Año](https://wiki.ead.pucv.cl/Property:Año)
- [Ciudad](https://wiki.ead.pucv.cl/Property:Ciudad)
- [Coautores](https://wiki.ead.pucv.cl/Property:Coautores)
- [Colección](https://wiki.ead.pucv.cl/Property:Colección)
- [Conjunto](https://wiki.ead.pucv.cl/Property:Conjunto)
- [Código](https://wiki.ead.pucv.cl/Property:Código)
- [Edición](https://wiki.ead.pucv.cl/Property:Edición)
- [Ejercicio](https://wiki.ead.pucv.cl/Property:Ejercicio)
- [Estructuras](https://wiki.ead.pucv.cl/Property:Estructuras)
- [Experiencia](https://wiki.ead.pucv.cl/Property:Experiencia)
- [Fecha](https://wiki.ead.pucv.cl/Property:Fecha)
- [Fondo](https://wiki.ead.pucv.cl/Property:Fondo)
- [Imágenes](https://wiki.ead.pucv.cl/Property:Imágenes)
- [Lenguajes](https://wiki.ead.pucv.cl/Property:Lenguajes)
- [Nota](https://wiki.ead.pucv.cl/Property:Nota)
- [Número de Documentos no Encuadernados](https://wiki.ead.pucv.cl/Property:Número_de_Documentos_no_Encuadernados)
- [Número de Ingreso](https://wiki.ead.pucv.cl/Property:Número_de_Ingreso)
- [Número de Páginas Encuadernadas](https://wiki.ead.pucv.cl/Property:Número_de_Páginas_Encuadernadas)
- [Número de Páginas con Inscripción](https://wiki.ead.pucv.cl/Property:Número_de_Páginas_con_Inscripción)
- [Obra de Travesía](https://wiki.ead.pucv.cl/Property:Obra_de_Travesía)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Páginas](https://wiki.ead.pucv.cl/Property:Páginas)
- [Travesías](https://wiki.ead.pucv.cl/Property:Travesías)
- [Título](https://wiki.ead.pucv.cl/Property:Título)

### Query semantica de ejemplo

```
[[Category:Objeto de Archivo]]|?Actividad|?Acto|?Alto|limit=20
```

## Observación

- **Plantilla:** [Plantilla:Observación](https://wiki.ead.pucv.cl/Plantilla:Observación)
- **Formulario:** [Form:Nueva Observación](https://wiki.ead.pucv.cl/Form:Nueva_Observación)
- **Categoria:** [Category:Observación](https://wiki.ead.pucv.cl/Category:Observación)

### Propiedades semanticas (3)

> Nota: `Has type` es una metapropiedad interna de SMW que se filtro al
> descubrir el esquema; no es una propiedad de usuario y no debe usarse en
> queries. La metapropiedad equivalente en Casiopea es `Tiene tipo de datos`.

- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Proyectos Relacionados](https://wiki.ead.pucv.cl/Property:Proyectos_Relacionados)
- [Páginas Relacionadas](https://wiki.ead.pucv.cl/Property:Páginas_Relacionadas)

### Query semantica de ejemplo

```
[[Category:Observación]]|?Palabras Clave|?Proyectos Relacionados|?Páginas Relacionadas|limit=20
```

## Página de Cuaderno

- **Plantilla:** [Plantilla:Página de Cuaderno](https://wiki.ead.pucv.cl/Plantilla:Página_de_Cuaderno)
- **Formulario:** [Form:Nueva Página de Cuaderno](https://wiki.ead.pucv.cl/Form:Nueva_Página_de_Cuaderno)
- **Categoria:** [Category:Página de Cuaderno](https://wiki.ead.pucv.cl/Category:Página_de_Cuaderno)

### Propiedades semanticas (9)

- [Actividad](https://wiki.ead.pucv.cl/Property:Actividad)
- [Carilla](https://wiki.ead.pucv.cl/Property:Carilla)
- [Ejercicio](https://wiki.ead.pucv.cl/Property:Ejercicio)
- [Estructuras](https://wiki.ead.pucv.cl/Property:Estructuras)
- [Lenguajes](https://wiki.ead.pucv.cl/Property:Lenguajes)
- [Número Correlativo](https://wiki.ead.pucv.cl/Property:Número_Correlativo)
- [Objeto Cuaderno](https://wiki.ead.pucv.cl/Property:Objeto_Cuaderno)
- [Parte](https://wiki.ead.pucv.cl/Property:Parte)
- [Título](https://wiki.ead.pucv.cl/Property:Título)

### Query semantica de ejemplo

```
[[Category:Página de Cuaderno]]|?Actividad|?Carilla|?Ejercicio|limit=20
```

## Persona

- **Plantilla:** [Plantilla:Persona](https://wiki.ead.pucv.cl/Plantilla:Persona)
- **Formulario:** [Form:Nueva Persona](https://wiki.ead.pucv.cl/Form:Nueva_Persona)
- **Categoria:** [Category:Persona](https://wiki.ead.pucv.cl/Category:Persona)

### Propiedades semanticas (12)

- [Apellido](https://wiki.ead.pucv.cl/Property:Apellido)
- [Año de Ingreso a la Escuela](https://wiki.ead.pucv.cl/Property:Año_de_Ingreso_a_la_Escuela)
- [Biografía](https://wiki.ead.pucv.cl/Property:Biografía)
- [Carreras Relacionadas](https://wiki.ead.pucv.cl/Property:Carreras_Relacionadas)
- [Ciudad](https://wiki.ead.pucv.cl/Property:Ciudad)
- [Email](https://wiki.ead.pucv.cl/Property:Email)
- [Grado Académico](https://wiki.ead.pucv.cl/Property:Grado_Académico)
- [Jerarquía Académica](https://wiki.ead.pucv.cl/Property:Jerarquía_Académica)
- [Nombre](https://wiki.ead.pucv.cl/Property:Nombre)
- [País](https://wiki.ead.pucv.cl/Property:País)
- [Página Web](https://wiki.ead.pucv.cl/Property:Página_Web)
- [Relación con la Escuela](https://wiki.ead.pucv.cl/Property:Relación_con_la_Escuela)

### Query semantica de ejemplo

```
[[Category:Persona]]|?Apellido|?Año de Ingreso a la Escuela|?Biografía|limit=20
```

## Presencia en la Sociedad

- **Plantilla:** [Plantilla:Presencia en la Sociedad](https://wiki.ead.pucv.cl/Plantilla:Presencia_en_la_Sociedad)
- **Formulario:** [Form:Nueva Presencia en la Sociedad](https://wiki.ead.pucv.cl/Form:Nueva_Presencia_en_la_Sociedad)
- **Categoria:** [Category:Presencia en la Sociedad](https://wiki.ead.pucv.cl/Category:Presencia_en_la_Sociedad)

### Propiedades semanticas (14)

- [Descripción](https://wiki.ead.pucv.cl/Property:Descripción)
- [Evento](https://wiki.ead.pucv.cl/Property:Evento)
- [Fecha](https://wiki.ead.pucv.cl/Property:Fecha)
- [Institución Contraparte](https://wiki.ead.pucv.cl/Property:Institución_Contraparte)
- [Lugar](https://wiki.ead.pucv.cl/Property:Lugar)
- [Modalidad](https://wiki.ead.pucv.cl/Property:Modalidad)
- [Otros Participantes](https://wiki.ead.pucv.cl/Property:Otros_Participantes)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Profesores](https://wiki.ead.pucv.cl/Property:Profesores)
- [Rol de la Contraparte](https://wiki.ead.pucv.cl/Property:Rol_de_la_Contraparte)
- [Rol de la Escuela](https://wiki.ead.pucv.cl/Property:Rol_de_la_Escuela)
- [Tipo de Presencia Académica](https://wiki.ead.pucv.cl/Property:Tipo_de_Presencia_Académica)
- [Título](https://wiki.ead.pucv.cl/Property:Título)
- [Url](https://wiki.ead.pucv.cl/Property:Url)

### Query semantica de ejemplo

```
[[Category:Presencia en la Sociedad]]|?Descripción|?Evento|?Fecha|limit=20
```

## Proyecto

- **Plantilla:** [Plantilla:Proyecto](https://wiki.ead.pucv.cl/Plantilla:Proyecto)
- **Formulario:** [Form:Nuevo Proyecto](https://wiki.ead.pucv.cl/Form:Nuevo_Proyecto)
- **Categoria:** [Category:Proyecto](https://wiki.ead.pucv.cl/Category:Proyecto)

### Propiedades semanticas (11)

- [Alumnos](https://wiki.ead.pucv.cl/Property:Alumnos)
- [Asignaturas Relacionadas](https://wiki.ead.pucv.cl/Property:Asignaturas_Relacionadas)
- [Año de Inicio](https://wiki.ead.pucv.cl/Property:Año_de_Inicio)
- [Año de Término](https://wiki.ead.pucv.cl/Property:Año_de_Término)
- [Carreras Relacionadas](https://wiki.ead.pucv.cl/Property:Carreras_Relacionadas)
- [Cursos Relacionados](https://wiki.ead.pucv.cl/Property:Cursos_Relacionados)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Profesor](https://wiki.ead.pucv.cl/Property:Profesor)
- [Tipo de Proyecto](https://wiki.ead.pucv.cl/Property:Tipo_de_Proyecto)
- [Título](https://wiki.ead.pucv.cl/Property:Título)
- [URL](https://wiki.ead.pucv.cl/Property:URL)

### Query semantica de ejemplo

```
[[Category:Proyecto]]|?Alumnos|?Asignaturas Relacionadas|?Año de Inicio|limit=20
```

## Proyecto de Investigación

- **Plantilla:** [Plantilla:Proyecto de Investigación](https://wiki.ead.pucv.cl/Plantilla:Proyecto_de_Investigación)
- **Formulario:** [Form:Nuevo Proyecto de Investigación](https://wiki.ead.pucv.cl/Form:Nuevo_Proyecto_de_Investigación)
- **Categoria:** [Category:Proyecto de Investigación](https://wiki.ead.pucv.cl/Category:Proyecto_de_Investigación)

### Propiedades semanticas (15)

- [Año de Inicio](https://wiki.ead.pucv.cl/Property:Año_de_Inicio)
- [Año de Término](https://wiki.ead.pucv.cl/Property:Año_de_Término)
- [Carreras Relacionadas](https://wiki.ead.pucv.cl/Property:Carreras_Relacionadas)
- [Coinvestigadores](https://wiki.ead.pucv.cl/Property:Coinvestigadores)
- [Código](https://wiki.ead.pucv.cl/Property:Código)
- [Fuente de Financiamiento](https://wiki.ead.pucv.cl/Property:Fuente_de_Financiamiento)
- [Investigador Responsable](https://wiki.ead.pucv.cl/Property:Investigador_Responsable)
- [Línea de Investigación](https://wiki.ead.pucv.cl/Property:Línea_de_Investigación)
- [Modalidad de Investigación](https://wiki.ead.pucv.cl/Property:Modalidad_de_Investigación)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Presupuesto](https://wiki.ead.pucv.cl/Property:Presupuesto)
- [Título](https://wiki.ead.pucv.cl/Property:Título)
- [URL](https://wiki.ead.pucv.cl/Property:URL)
- [Vinculación con el Medio](https://wiki.ead.pucv.cl/Property:Vinculación_con_el_Medio)
- [Área de Investigación](https://wiki.ead.pucv.cl/Property:Área_de_Investigación)

### Query semantica de ejemplo

```
[[Category:Proyecto de Investigación]]|?Año de Inicio|?Año de Término|?Carreras Relacionadas|limit=20
```

## Proyecto de Vinculación con el Medio

- **Plantilla:** [Plantilla:Proyecto de Vinculación con el Medio](https://wiki.ead.pucv.cl/Plantilla:Proyecto_de_Vinculación_con_el_Medio)
- **Formulario:** [Form:Nuevo Proyecto de Vinculación con el Medio](https://wiki.ead.pucv.cl/Form:Nuevo_Proyecto_de_Vinculación_con_el_Medio)
- **Categoria:** [Category:Proyecto de Vinculación con el Medio](https://wiki.ead.pucv.cl/Category:Proyecto_de_Vinculación_con_el_Medio)

### Propiedades semanticas (13)

- [Año de Inicio](https://wiki.ead.pucv.cl/Property:Año_de_Inicio)
- [Año de Término](https://wiki.ead.pucv.cl/Property:Año_de_Término)
- [Contraparte](https://wiki.ead.pucv.cl/Property:Contraparte)
- [Fuente de Financiamiento](https://wiki.ead.pucv.cl/Property:Fuente_de_Financiamiento)
- [PDF](https://wiki.ead.pucv.cl/Property:PDF)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Posición](https://wiki.ead.pucv.cl/Property:Posición)
- [Presupuesto](https://wiki.ead.pucv.cl/Property:Presupuesto)
- [Profesionales](https://wiki.ead.pucv.cl/Property:Profesionales)
- [Profesores](https://wiki.ead.pucv.cl/Property:Profesores)
- [Tipo de Vinculación](https://wiki.ead.pucv.cl/Property:Tipo_de_Vinculación)
- [Título](https://wiki.ead.pucv.cl/Property:Título)
- [URL](https://wiki.ead.pucv.cl/Property:URL)

### Query semantica de ejemplo

```
[[Category:Proyecto de Vinculación con el Medio]]|?Año de Inicio|?Año de Término|?Contraparte|limit=20
```

## Publicación

- **Plantilla:** [Plantilla:Publicación](https://wiki.ead.pucv.cl/Plantilla:Publicación)
- **Formulario:** [Form:Nueva Publicación](https://wiki.ead.pucv.cl/Form:Nueva_Publicación)
- **Categoria:** [Category:Publicación](https://wiki.ead.pucv.cl/Category:Publicación)

### Propiedades semanticas (23)

- [Autor](https://wiki.ead.pucv.cl/Property:Autor)
- [Año](https://wiki.ead.pucv.cl/Property:Año)
- [Carreras Relacionadas](https://wiki.ead.pucv.cl/Property:Carreras_Relacionadas)
- [Ciudad](https://wiki.ead.pucv.cl/Property:Ciudad)
- [Coautores](https://wiki.ead.pucv.cl/Property:Coautores)
- [Colección](https://wiki.ead.pucv.cl/Property:Colección)
- [Código](https://wiki.ead.pucv.cl/Property:Código)
- [Edición](https://wiki.ead.pucv.cl/Property:Edición)
- [Editorial](https://wiki.ead.pucv.cl/Property:Editorial)
- [Filiación](https://wiki.ead.pucv.cl/Property:Filiación)
- [Indexación](https://wiki.ead.pucv.cl/Property:Indexación)
- [Línea de Investigación](https://wiki.ead.pucv.cl/Property:Línea_de_Investigación)
- [Nota](https://wiki.ead.pucv.cl/Property:Nota)
- [Número](https://wiki.ead.pucv.cl/Property:Número)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [Profesor Guía](https://wiki.ead.pucv.cl/Property:Profesor_Guía)
- [Páginas](https://wiki.ead.pucv.cl/Property:Páginas)
- [Revista](https://wiki.ead.pucv.cl/Property:Revista)
- [Tipo de Publicación](https://wiki.ead.pucv.cl/Property:Tipo_de_Publicación)
- [Título](https://wiki.ead.pucv.cl/Property:Título)
- [URL](https://wiki.ead.pucv.cl/Property:URL)
- [Volumen](https://wiki.ead.pucv.cl/Property:Volumen)
- [Área de Investigación](https://wiki.ead.pucv.cl/Property:Área_de_Investigación)

### Query semantica de ejemplo

```
[[Category:Publicación]]|?Autor|?Año|?Carreras Relacionadas|limit=20
```

## Revista Académica

- **Plantilla:** [Plantilla:Revista Académica](https://wiki.ead.pucv.cl/Plantilla:Revista_Académica)
- **Formulario:** [Form:Nueva Revista Académica](https://wiki.ead.pucv.cl/Form:Nueva_Revista_Académica)
- **Categoria:** [Category:Revista Académica](https://wiki.ead.pucv.cl/Category:Revista_Académica)

### Propiedades semanticas (16)

- [Carreras Relacionadas](https://wiki.ead.pucv.cl/Property:Carreras_Relacionadas)
- [Código](https://wiki.ead.pucv.cl/Property:Código)
- [Descripción](https://wiki.ead.pucv.cl/Property:Descripción)
- [Dirección](https://wiki.ead.pucv.cl/Property:Dirección)
- [Editorial](https://wiki.ead.pucv.cl/Property:Editorial)
- [Email](https://wiki.ead.pucv.cl/Property:Email)
- [Filiación](https://wiki.ead.pucv.cl/Property:Filiación)
- [Idioma](https://wiki.ead.pucv.cl/Property:Idioma)
- [Indexación](https://wiki.ead.pucv.cl/Property:Indexación)
- [Nombre](https://wiki.ead.pucv.cl/Property:Nombre)
- [Números al Año](https://wiki.ead.pucv.cl/Property:Números_al_Año)
- [Palabras Clave](https://wiki.ead.pucv.cl/Property:Palabras_Clave)
- [País](https://wiki.ead.pucv.cl/Property:País)
- [Profesores que han Publicado](https://wiki.ead.pucv.cl/Property:Profesores_que_han_Publicado)
- [Suscripción Escuela](https://wiki.ead.pucv.cl/Property:Suscripción_Escuela)
- [URL](https://wiki.ead.pucv.cl/Property:URL)

### Query semantica de ejemplo

```
[[Category:Revista Académica]]|?Carreras Relacionadas|?Código|?Descripción|limit=20
```

## Tarea

- **Plantilla:** [Plantilla:Tarea](https://wiki.ead.pucv.cl/Plantilla:Tarea)
- **Formulario:** [Form:Nueva Tarea](https://wiki.ead.pucv.cl/Form:Nueva_Tarea)
- **Categoria:** [Category:Tarea](https://wiki.ead.pucv.cl/Category:Tarea)

### Propiedades semanticas (6)

- [Alumnos](https://wiki.ead.pucv.cl/Property:Alumnos)
- [Asignaturas Relacionadas](https://wiki.ead.pucv.cl/Property:Asignaturas_Relacionadas)
- [Carreras Relacionadas](https://wiki.ead.pucv.cl/Property:Carreras_Relacionadas)
- [Cursos Relacionados](https://wiki.ead.pucv.cl/Property:Cursos_Relacionados)
- [Sección](https://wiki.ead.pucv.cl/Property:Sección)
- [URL](https://wiki.ead.pucv.cl/Property:URL)

### Query semantica de ejemplo

```
[[Category:Tarea]]|?Alumnos|?Asignaturas Relacionadas|?Carreras Relacionadas|limit=20
```

## Trabajo en MADLAB

- **Plantilla:** [Plantilla:Trabajo en MADLAB](https://wiki.ead.pucv.cl/Plantilla:Trabajo_en_MADLAB)
- **Formulario:** [Form:Nuevo Trabajo en MADLAB](https://wiki.ead.pucv.cl/Form:Nuevo_Trabajo_en_MADLAB)
- **Categoria:** [Category:Trabajo en MADLAB](https://wiki.ead.pucv.cl/Category:Trabajo_en_MADLAB)

### Propiedades semanticas (7)

- [Archivo](https://wiki.ead.pucv.cl/Property:Archivo)
- [Asignaturas Relacionadas](https://wiki.ead.pucv.cl/Property:Asignaturas_Relacionadas)
- [Autor](https://wiki.ead.pucv.cl/Property:Autor)
- [Cursos Relacionados](https://wiki.ead.pucv.cl/Property:Cursos_Relacionados)
- [Fecha](https://wiki.ead.pucv.cl/Property:Fecha)
- [Máquina](https://wiki.ead.pucv.cl/Property:Máquina)
- [Software](https://wiki.ead.pucv.cl/Property:Software)

### Query semantica de ejemplo

```
[[Category:Trabajo en MADLAB]]|?Archivo|?Asignaturas Relacionadas|?Autor|limit=20
```

## Travesía

- **Plantilla:** [Plantilla:Travesía](https://wiki.ead.pucv.cl/Plantilla:Travesía)
- **Formulario:** [Form:Nueva Travesía](https://wiki.ead.pucv.cl/Form:Nueva_Travesía)
- **Categoria:** [Category:Travesía](https://wiki.ead.pucv.cl/Category:Travesía)

### Propiedades semanticas (12)

- [Alumnos](https://wiki.ead.pucv.cl/Property:Alumnos)
- [Ayudantes](https://wiki.ead.pucv.cl/Property:Ayudantes)
- [Año](https://wiki.ead.pucv.cl/Property:Año)
- [Cursos Relacionados](https://wiki.ead.pucv.cl/Property:Cursos_Relacionados)
- [Destino](https://wiki.ead.pucv.cl/Property:Destino)
- [Fecha de Inicio](https://wiki.ead.pucv.cl/Property:Fecha_de_Inicio)
- [Fecha de Término](https://wiki.ead.pucv.cl/Property:Fecha_de_Término)
- [Nombre](https://wiki.ead.pucv.cl/Property:Nombre)
- [Obra de Travesía](https://wiki.ead.pucv.cl/Property:Obra_de_Travesía)
- [Profesores](https://wiki.ead.pucv.cl/Property:Profesores)
- [Profesores Invitados](https://wiki.ead.pucv.cl/Property:Profesores_Invitados)
- [Talleres](https://wiki.ead.pucv.cl/Property:Talleres)

### Query semantica de ejemplo

```
[[Category:Travesía]]|?Alumnos|?Ayudantes|?Año|limit=20
```
