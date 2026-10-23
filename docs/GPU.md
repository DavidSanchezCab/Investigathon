# GPU del Investigathón

[Seguro] Estado verificado el **23 de octubre de 2026**: se pudo entrar por SSH a la máquina provista por la organización. Tiene NVIDIA T4 de **15.360 MiB de VRAM**, **16 GiB de RAM**, Ubuntu 22.04, Python 3.10.12 y driver NVIDIA 595.91.07. Había aproximadamente **48 GB de disco libre al inicio**; instalaciones y modelos consumen ese espacio.

## Acceso y archivos privados

[Seguro] Los adjuntos del correo se guardaron en `.gpu-private/investigathon-gpu.key`, `.gpu-private/known_hosts` y `.gpu-private/instructivo-gpu.md`. Están excluidos de Git y sus permisos de Windows están restringidos al usuario. El instructivo privado contiene los datos de conexión.

[Seguro] La conexión usa estrictamente la huella del servidor incluida en el `known_hosts` recibido. **No omitir la verificación de identidad SSH** ni sustituir ese archivo por una clave aceptada automáticamente. Si cambia la huella, comprobar el cambio con la organización antes de conectarse.

[Seguro] La base GGUF y los dos adapters están descargados con hashes verificados. Los adapters están convertidos a FP16 y pasaron la comparación exacta de sus 896 tensores cada uno contra los originales convertidos a esa precisión. La compilación CUDA y la inferencia siguen pendientes de validación. La interfaz desde PowerShell, en la raíz de este proyecto, es:

```powershell
.\scripts\gpu.ps1 check       # Conexión, GPU, RAM y disco
.\scripts\gpu.ps1 ssh         # Terminal remota
.\scripts\gpu.ps1 upload      # Copiar los scripts de gpu/
.\scripts\gpu.ps1 bootstrap   # Preparar entorno y dependencias
.\scripts\gpu.ps1 smoke       # Intentar una primera inferencia
.\scripts\gpu.ps1 download    # Traer resultados a la computadora
```

[Seguro] Las rutas son `~/investigathon` para el trabajo remoto, `~/investigathon/results` para resultados y `~/investigathon/cache/huggingface` para la caché. `models-manifest.json` registra revisiones y hashes; `results/adapter-validation.json` registra la validación íntegra de los adapters. El registro de paquetes se guardará en `~/investigathon/requirements.lock.txt`.

[Seguro] El código local de conexión y ejecución se prepara en `scripts/gpu.ps1` y `gpu/`. La clave privada queda en esta computadora: no es parte del código que se sube.

## Plan con los recursos disponibles

[Seguro] El recurso disponible es esta máquina; no se solicitará una ampliación. [llama.cpp admite inferencia híbrida CPU+GPU](https://github.com/ggml-org/llama.cpp#description), con parte del modelo fuera de VRAM.

[Seguro] Se descargó `unsloth/Qwen3-32B-GGUF/Qwen3-32B-Q4_K_M.gguf` (19.762.150.048 bytes). [Probable] La siguiente prueba es cargarlo con 40 capas en GPU y el resto en RAM, primero base y después con cada LoRA convertido. **Aún no está probado** que la carga y la generación entren en los recursos disponibles ni que rindan lo suficiente para el experimento.

[Seguro] La [colección publicada por los autores](https://huggingface.co/collections/thejaminator/school-of-reward-hacks) contiene organismos y controles **Qwen3-32B**. El [adaptador inspeccionado](https://huggingface.co/thejaminator/1e-4-hacker_qwen3_32b-20250808_101141-3epoch/blob/main/adapter_config.json) declara `unsloth/Qwen3-32B` como modelo progenitor. La comparación debe conservar esa procedencia y registrar checkpoint, revisión, adaptador y cuantización.

[Seguro] El [benchmark oficial de Qwen con Transformers](https://qwen.readthedocs.io/en/latest/getting_started/speed_benchmark.html#qwen3-32b-transformers) reporta **19.109 MB** para Qwen3-32B en AWQ de 4 bits, con entrada de un token y generación de 2.048. Esa configuración no cabe íntegramente en esta VRAM. **No es una medición de GGUF con offload parcial** y no demuestra su inviabilidad en esta máquina.

[Probable] Para decidir si el camino funciona hay que medir disco disponible, RAM y VRAM máximas, capas enviadas a GPU, contexto y velocidad de generación. Si carga, se compararán progenitor y adaptador con la misma cuantización y configuración; esa evaluación cuantizada tiene que declararse como tal.

[Seguro] Es un **piloto cuantizado Qwen3-32B Q4_K_M con adapters School of Reward Hacks FP16**. La validación de los adapters no demuestra equivalencia con la ejecución BF16 del paper. Los repositorios BF16 de Qwen y Unsloth usan distinto sharding, por lo que aquí tampoco se declara igualdad numérica entre ambas distribuciones completas.

[Seguro] Python tiene Torch CPU para convertir y verificar archivos; la inferencia GPU la hará llama.cpp compilado con CUDA 12.8 para SM75. No se entrena el modelo. La [guía de VS Code y Claude Code](MIS_PASOS_VSCODE.md) explica cómo conectarse y abrir el CLI ya instalado para `ubuntu`.

## Alcance científico y operación

[Seguro] El documento [Paper](../Paper), incorporado por el equipo en GitHub, define School of Reward Hacks como marco y la detección de patrones de reward hacking como objetivo; su hipótesis todavía está vacía. El [roadmap anterior](ROADMAP.md) desarrollaba otra propuesta con Terminal Wrench y requiere reconciliarse con este marco antes de ejecutar un estudio. La preparación de infraestructura no fija una hipótesis experimental.

[Probable] El caso de 51 sirve para probar el circuito. Un experimento defendible requeriría familias de errores reservadas, verificadores independientes y separación entre intentos de explotación, hacks consumados y soluciones legítimas, además de medir falsas acusaciones del monitor. Guardar el texto `thinking` no certifica fidelidad a los estados internos.

[Seguro] Se usa el recurso ya asignado por la organización; este procedimiento no crea nuevas instancias ni envía comunicaciones. **Salir de SSH no apaga la máquina.** La coordinación de apagado y ventana de uso sigue pendiente.
