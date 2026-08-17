# Sistema de control presupuestario y KPIs financieros

Proyecto final del curso Data Analyst + IA. Simula el control de ejecución
presupuestaria de una empresa de telecomunicaciones: cruza presupuesto vs.
gasto real por departamento, categoría y mes, detecta desviaciones y las
presenta en un dashboard ejecutivo.

## Stack utilizado

- **SQL (SQLite)** — modelado relacional, joins, vistas de análisis
- **Python (pandas, requests)** — limpieza de datos, lógica de negocio, consumo de API externa
- **Power BI (DAX)** — dashboard interactivo con medidas calculadas
- **API externa** — [Frankfurter API](https://frankfurter.dev) (tipos de cambio EUR/USD del BCE, sin API key)

## Estructura del repositorio

```
├── data/
│   ├── raw/          # datos crudos: presupuesto, ejecución (sucia), tipo de cambio
│   ├── processed/    # datos limpios, exportados a Excel / JSON
│   └── sql/          # base de datos SQLite y dump .sql versionable
├── notebooks/        # notebooks de limpieza, análisis y consumo de API
├── src/              # scripts reutilizables (generación de datos, ETL, API)
├── powerbi/          # archivo .pbix y capturas del dashboard
└── requirements.txt
```

## Modelo de datos (esquema estrella)

Tres tablas de hechos (`presupuesto`, `ejecucion_real`, `ingresos`) conectadas
a las dimensiones `departamentos`, `categorias` y `periodos`, listas para
relacionarse en Power BI sin necesidad de tablas intermedias.

## Contexto de negocio

Cifras calibradas con datos reales del mercado español (INE, salario medio
bruto 2024: 2.385,6€/mes; coste Seguridad Social empresa: +30%). La nómina de
cada departamento se calcula como plantilla × salario medio del rol × 1.30,
no como una cifra inventada.

Los ingresos se modelan en 3 líneas de negocio ligadas a los departamentos
que las generan (Ventas B2B, Atención al Cliente, Tecnología/TI), con una
tendencia de crecimiento realista (~18% interanual, impulsado sobre todo por
servicios de valor añadido/cloud) y estacionalidad de agosto típica del
mercado español. La ejecución del presupuesto se mantiene mayormente
controlada, con sobreejecución moderada en Marketing y Tecnología —
coherente con la inversión que sostiene ese crecimiento.

## Cómo reproducir

```bash
pip install -r requirements.txt
python src/generar_datos.py          # genera el dataset sintético 2025
python src/obtener_tipo_cambio.py    # consume la API vía GET
python src/calcular_forecast_2026.py # calcula el forecast 2026 a partir de los datos 2025
python src/exportar_formatos.py      # exporta todo a Excel, JSON y SQL
```

## Metodología del forecast 2026

Parte únicamente de los datos reales de 2025 ya construidos en el proyecto — no usa fuentes externas:

- **Ingresos**: proyección estadística (tendencia lineal + índice estacional), con intervalo de confianza del 95% sobre los residuos de la regresión.
- **Presupuesto**: decisión de planificación (+6% Marketing/Tecnología, +3% resto), preservando la variación mensual real de 2025.
- **Gasto esperado**: ratio histórico de ejecución mensual (no el promedio anual) aplicado sobre el nuevo presupuesto — refleja el patrón real de cada mes.
- **Se crea una v2 del forecast porque la v1 tenía presupuesto/gasto con el mismo monto todos los meses, y v2 preserva la variación mensual real de 2025.

## Autor

Maikol — Data Analyst + IA (2026)
