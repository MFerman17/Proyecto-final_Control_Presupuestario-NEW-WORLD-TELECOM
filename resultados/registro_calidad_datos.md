# Registro de calidad de datos — Ejecucion Real

Evidencia del proceso de limpieza aplicado a `ejecucion_real_raw` (241 filas originales).

| Verificacion | Resultado |
|---|---|
| Nombres de departamento normalizados | 6 departamentos, variantes unificadas (mayusculas, abreviaturas, espacios) |
| Valores nulos / no numericos detectados | 10 filas (4.1%) — excluidas, documentadas |
| Valores negativos detectados | 5 filas (2.1%) — corregidas con valor absoluto, flag conservado |
| Filas duplicadas detectadas | 1 fila (0.4%) — eliminada, se conservo la primera aparicion |
| Filas en dataset final limpio | 230 de 241 (95.4%) |

Fuente del proceso: notebooks/01_analisis_presupuesto.ipynb, secciones 2.1-2.4.
Salida: ejecucion_real_limpia.csv (230 filas, columnas: id_ejecucion, departamento_id, categoria_id, periodo_id, monto_ejecutado, fue_corregido_signo)
