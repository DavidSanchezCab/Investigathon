# Roadmap de investigación para el Investigathon

Propuesta para discutir en equipo — 18 de octubre de 2026.

## Decisión propuesta

[Probable] Investigar esta pregunta: **¿la ventaja de dar al monitor la narración del agente se mantiene cuando las soluciones legítimas vienen del mismo protocolo atacante y la evaluación usa tareas reservadas?**

[Probable] El aporte buscado es una réplica con controles más exigentes. Si la ventaja se mantiene, obtendríamos evidencia de robustez bajo esos controles; si disminuye, podríamos identificar una limitación del protocolo de evaluación. No se presupone el resultado ni se afirma novedad global.

## Evidencia que cambia el camino

- [Seguro] Terminal Wrench ya compara trayectorias originales, narración neutralizada y ausencia de mensajes del agente. Repetir esa caída no sería un aporte nuevo frente a esa fuente. El manifest declara 3.632 hacks, 2.352 baselines exitosos y 1.216 soluciones legítimas bajo el protocolo atacante; las tablas de monitorización usan los baselines como negativos. Son categorías publicadas, pendientes de nuestra auditoría de etiquetas. [README](https://github.com/few-sh/terminal-wrench), [manifest](https://github.com/few-sh/terminal-wrench/blob/main/dataset_manifest.json).
- [Seguro] El código del monitor omite los mensajes del usuario, incluidas las instrucciones de ataque. Por tanto, no corresponde atribuir el resultado publicado a que el monitor vea ese prompt. Los scripts de análisis calculan TPR al 5% de FPR sobre la ROC del conjunto suministrado. Eso describe una curva; no demuestra operación con un umbral fijado de antemano en tareas nuevas. [Monitor](https://raw.githubusercontent.com/few-sh/terminal-wrench/main/monitoring/monitor.py), [análisis](https://raw.githubusercontent.com/few-sh/terminal-wrench/main/monitoring/analyze.py).
- [Seguro] MonitoringBench ya estudia refinamiento adversarial, persuasión y calibración de monitores. Su protocolo incluye calibración con ejecuciones honestas; modificar prompts no produce mejoras consistentes entre modelos. La revisión de novedad debe comparar explícitamente contra este trabajo. [Métodos y resultados](https://arxiv.org/html/2605.09684v1).
- [Seguro] En septiembre de 2026 también se publicaron resultados de monitorización mediante representaciones internas sobre modelos abiertos grandes. Construir un probe o aplicar steering, por sí solos, tampoco diferenciaría nuestro trabajo. [Trabajo de Goodfire](https://www.goodfire.com/research/reward-hacking-activation-monitors).

## Experimento principal

[Probable] La unidad del estudio debería ser una **tarea**, con tres ejecuciones comparables cuando estén disponibles:

| Ejecución | Uso propuesto |
|---|---|
| [Probable] Hack confirmado | Medir detección de explotación ejecutada. |
| [Probable] Solución legítima del baseline | Reproducir el tipo de control publicado. |
| [Probable] Solución legítima obtenida bajo protocolo atacante | Comprobar qué cambia con controles de procedencia más comparable. |

[Probable] Para cada ejecución preparar dos vistas: **acciones, argumentos y resultados de herramientas**, y **esa misma información más narración del agente**. La especificación de la tarea debe estar disponible de forma idéntica. La eliminación de narración se aplica a todas las clases. Las diferencias de procedencia, modelo generador, longitud y configuración deben registrarse y emparejarse donde sea posible.

[Probable] Ambas vistas deben conservar las mismas acciones y resultados dentro del contexto que recibe el monitor. Si agregar narración excede su ventana, usar segmentación compartida o excluir ambas vistas; registrar truncamiento por sí solo no resuelve esa diferencia. Documentar las tareas sin tripleta completa: la conclusión se limita a las elegibles, que pueden diferir del resto del dataset.

[Seguro] Los fallos sin recompensa no son negativos automáticos: pueden contener intentos de explotación fallidos. Tampoco una solución que recibe recompensa prueba legitimidad. La etiqueta requiere examinar mecanismo, especificación y evidencia de ejecución, independientemente del relato y del puntaje del monitor.

[Probable] Para el análisis principal usar hacks consumados y soluciones legítimas auditables. Registrar intentos fallidos, casos ambiguos y exclusiones por separado. El objetivo es clasificar lo ejecutado; detectar intención futura sería otro experimento.

## Hitos y criterios para avanzar

| Hito | Trabajo | Criterio de cierre |
|---|---|---|
| [Probable] 1 Piloto de datos | Buscar diez tareas con las tres ejecuciones. Dos integrantes revisan etiquetas; verificar índices, versiones, acciones y salidas. | Diez tripletas auditables o un diagnóstico concreto de por qué faltan. Comprobar que las vistas conservan exactamente llamadas y resultados. |
| [Probable] 2 Protocolo congelado | Escribir hipótesis, elegibilidad, particiones, prompt, métricas y tratamiento de ambiguos antes de ver el test. | Desarrollo y test separados por tarea, y por duplicado o plantilla cuando sea identificable. Todas las variantes de una tarea permanecen juntas. |
| [Probable] 3 Comparación mínima | Usar un modelo monitor, dos vistas y los dos grupos de controles. Empezar con el prompt publicado. | Puntajes, errores de formato, contexto truncado, tokens y resultados guardados para todos los casos elegibles. |
| [Probable] 4 Extensión acotada | Comparar un segundo prompt que pida vincular el juicio con pasos concretos y la especificación de la tarea. Elegirlo solo en desarrollo. | Prompt y umbral fijados antes de evaluar test. Reportar tanto mejora como degradación. |
| [Probable] 5 Presentación | Preparar dos gráficos, tres casos explicados y un registro de decisiones/limitaciones. | Otra persona puede reconstruir la comparación desde los datos y entender qué conclusión permite. |

[Probable] No elegiría si avanzar según que el piloto dé el resultado deseado. El piloto debe comprobar etiquetas, disponibilidad, medición y costo. Un efecto pequeño también puede ser el resultado final.

## Escala y recursos

[Probable] Como objetivo exploratorio, **hasta 80 tareas elegibles**, con unas 20 para desarrollo y 60 reservadas. La intersección exacta entre hacks y ambos controles todavía no está verificada. Si no alcanza, reducir la escala y declarar el alcance antes de analizar test.

[Seguro] Con tripletas completas, un piloto de diez tareas, dos vistas y un prompt requiere **60 consultas al monitor**. Ochenta tareas, tres ejecuciones, dos vistas y dos prompts requieren **960 consultas**, sin contar repeticiones, reintentos ni generación de variantes.

[Probable] Este diseño puede analizar trayectorias guardadas y evita necesitar una GPU de entrenamiento. La inferencia requiere un modelo local o una API. Medir tokens en el piloto y calcular el costo con el tarifario del modelo elegido antes de ampliar. Los créditos AWS mencionados en el README todavía no están comprobados como disponibles o aplicables a esa inferencia.

## Métricas y conclusiones permitidas

[Probable] Reportar tres cantidades: separación entre hacks y legítimos —por ejemplo, AUROC—; detección de hacks a un umbral fijado en desarrollo; y falsas alarmas sobre cada grupo de soluciones legítimas a ese mismo umbral. Comparar cuánto aporta la narración al cambiar los controles. No reducir todo a exactitud global.

[Probable] Calcular AUROC por separado contra cada grupo legítimo; la diferencia entre grupos es pareada porque reutiliza los mismos hacks. Calcular incertidumbre remuestreando tareas completas, conservando juntas sus ejecuciones y variantes. Para tasas de error, dar el mismo peso a cada tarea. El umbral puede ser distinto para cada diseño de monitor, pero debe quedar fijo entre las vistas que se comparan si la pregunta es su sensibilidad al cambio de presentación. Acompañarlo con AUROC permite distinguir cambios en discriminación de simples cambios en la escala de puntajes.

[Seguro] Con cero falsas alarmas en 20 controles independientes, el límite superior unilateral exacto al 95% es aproximadamente 13,9%. Para que baje de 5% hacen falta al menos 59 controles independientes y cero errores, bajo el supuesto binomial. La expresión es `1 - 0.05^(1/n)`. Vistas o ejecuciones correlacionadas de una tarea no equivalen a nuevas tareas independientes. Por eso el piloto no certifica una FPR baja.

[Probable] Los gráficos útiles serían: aporte de la narración con controles estándar frente a controles difíciles, y detección frente a falsas alarmas con umbrales congelados. Acompañarlos con casos donde el monitor acierta, omite un hack o acusa una solución legítima.

## Límites y extensión opcional

[Seguro] Quitar o neutralizar narración elimina información potencialmente diagnóstica. Una caída no prueba que el monitor solo busque palabras. Además, las tareas fueron seleccionadas por vulnerabilidad y los ataques se provocaron: sus proporciones no estiman incidencia natural. [Terminal Wrench](https://github.com/few-sh/terminal-wrench).

[Probable] Si el núcleo está completo, una extensión sería usar paráfrasis que preserven hechos e intención, aplicadas simétricamente, para medir sensibilidad al estilo. Pegaría cada variante a la misma ejecución y la revisaría antes de consultar al monitor. Narrativas contradictorias y eliminación de intención deben analizarse aparte, porque cambian la información disponible.

[Probable] Dejaría entrenamiento RL, entrenamiento de SAEs, múltiples datasets y steering fuera del primer ciclo. El camino de steering solo tendría sentido después de confirmar recursos y disponer de un evaluador externo ejecutable que distinga hacks reales de cambios en puntajes internos. La literatura reciente ya cubre parte de esas intervenciones.

## Reparto para la reunión

- [Probable] **Datos y etiquetas:** conseguir las diez tripletas, documentar mecanismo y resolver desacuerdos.
- [Probable] **Evaluación reproducible:** definir vistas, protocolo, costos y almacenamiento de resultados.
- [Probable] **Análisis y comunicación:** comparar con antecedentes, fijar métricas y preparar gráficos/casos para mentoría.

[Probable] La frase para el mentor sería: **“Queremos comprobar si la ventaja de leer la narración se mantiene con soluciones legítimas del mismo protocolo atacante y tareas nuevas, midiendo tanto trampas detectadas como falsas acusaciones.”** La primera consulta sería si este tipo de réplica con extensión metodológica encaja con la expectativa de aporte del track.
