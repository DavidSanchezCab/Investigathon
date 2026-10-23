# Sincronización PC, GitHub y GPU

[Seguro] El repositorio común es [DavidSanchezCab/Investigathon](https://github.com/DavidSanchezCab/Investigathon). El helper manual `scripts/sync-gpu.ps1` sincroniza la rama `main` de esta PC, GitHub y `~/investigathon` en la GPU; solo incorpora commits mediante avance directo (*fast-forward*).

## Uso

1. [Seguro] Terminá una unidad de trabajo en la PC o en la GPU, revisá los archivos y hacé **commit en ese mismo equipo**. El helper no crea commits.
2. [Seguro] Dejá ambos árboles sin cambios pendientes. Los modelos, entornos, resultados, logs y `.gpu-private` se mantienen fuera de Git.
3. [Seguro] Ejecutá desde la PC:

   ```powershell
   .\scripts\sync-gpu.ps1
   ```

   [Seguro] El script encuentra el proyecto a partir de su propia ubicación; también se puede ejecutar mediante su ruta absoluta desde otra carpeta.

4. [Seguro] La confirmación final muestra un mismo commit para PC, `origin/main` de GitHub y GPU, con ambos árboles limpios.

[Seguro] Si Claude trabaja en la GPU, debe hacer sus commits allí. Después corrés el helper desde Windows: baja un **bundle de commits**, los incorpora en la PC, hace el push con la autenticación de GitHub ya configurada en Windows y actualiza la GPU desde el repositorio público. La GPU no necesita credenciales de escritura en GitHub; no se copian tokens ni se crean cuentas.

## Qué comprueba y qué hacer si se detiene

[Seguro] Antes de mover `main`, el helper verifica las raíces Git, el `origin` esperado, la rama, árboles limpios y que alguno de los tres commits contenga a los otros dos en su historia. Recibe el bundle privado en `.gpu-private/gpu-sync.bundle` y deja la referencia local `gpu/main` para inspeccionar los commits remotos.

[Seguro] Si las historias divergen, se detiene antes de mover `main`: **no se perdió nada**. Revisá `main`, `origin/main` y `gpu/main`, reconciliá los commits manualmente y repetí el comando. El helper no hace reset, stash ni push forzado. Si detecta cambios concurrentes o falla la red después de algún avance, conserva los commits ya incorporados y publicados; revisá el estado antes de repetirlo.

[Seguro] SSH usa la misma clave y `known_hosts` privados que `scripts/gpu.ps1`, con verificación estricta de la identidad del servidor. Un error de huella requiere comprobar la identidad; no se desactiva la verificación.

[Seguro] Esta sincronización mueve código y documentación versionados, **no el modelo de aproximadamente 20 GB** ni el resto de los archivos ignorados. Para descargar los resultados de inferencia, usá `scripts/gpu.ps1 download`. No es una sincronización automática permanente: hay que hacer commit y ejecutar el helper al cambiar de equipo.
