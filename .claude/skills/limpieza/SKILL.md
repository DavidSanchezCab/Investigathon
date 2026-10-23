---
name: limpieza
description: Ordena y limpia carpetas personales o Google Drive (fuera de un repo de código) — duplicados, carpetas vacías, archivos corruptos o vacíos, nombres poco informativos, cosas obsoletas — y clasifica en carpetas con sentido. Propone la lista primero y borra o mueve sólo con el ok. Usar siempre que el usuario diga "hacé limpieza general", "ordename el drive", "ordename la carpeta de descargas/de la facu", "hay duplicados", "clasificá estos archivos", "borrá lo que no sirve", o "seguí con lo del drive". Para docs o basura dentro de un repo, /ordenar.
---

# /limpieza — ordenar sin perder nada

Argumentos: `$ARGUMENTS` — qué carpeta o qué parte del Drive.

**Borrar es irreversible** (en Drive, vaciar la papelera también): el usuario decide qué se va. Lo que
no se puede identificar se pregunta, no se adivina. Pasó el 03/10: un archivo que parecía descartable
era "una captura de un chiste que hizo un amigo muy bueno, no se borra".

## 1. Relevar, sin tocar

- **Inventario:** ruta, tamaño, fecha y tipo de cada archivo.
- **Buscá:**
  - duplicados, por hash y no por nombre;
  - archivos vacíos (0 bytes) o corruptos (que no abren);
  - carpetas vacías;
  - nombres que no dicen nada (`IMG_1234`, `nuevo documento`, `hola.txt`).
- **Drive:** con el conector de Google Drive si está disponible; si no, sobre la carpeta sincronizada
  local o un export.
- **Lo sensible** (credenciales, documentos personales) va en una lista aparte y se pregunta. No lo
  abras más de lo necesario para clasificarlo.

## 2. Proponer

- Una tabla: archivo → qué es (o "no sé") → propuesta (borrar / mover a X / renombrar a Y /
  preguntar).
- Primero lo seguro (duplicados exactos, vacíos), después lo dudoso.
- Una estructura de carpetas corta: por año, materia o tema.

## 3. Ejecutar, con el ok

- **Mover antes que borrar:** a una carpeta `_para_borrar_<fecha>`, para poder deshacer.
- **Renombrar con un patrón consistente:** fecha, tema, detalle.
- **Al final, el resumen:** qué se movió, borró o renombró, y dónde quedó cada cosa.

Si la tarea es larga, dejá el avance en un archivo de progreso dentro de la misma carpeta, así se
sigue en otra sesión. Pasó el 02/10: "alcancé el largo máximo de chat".
