"""
Exporta las tablas de la base de datos SQLite a multiples formatos:
- Excel (.xlsx) -> un libro con una hoja por tabla
- JSON (.json)  -> un archivo por tabla
- SQL (.sql)    -> script de creacion + insercion, ideal para versionar en Git
                   (un .db binario no se puede revisar en un diff de GitHub,
                   un .sql de texto plano si)
"""
import sqlite3
import pandas as pd
import json
import os

BASE = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE, "..", "data", "sql", "control_presupuestario.db")
PROCESSED_DIR = os.path.join(BASE, "..", "data", "processed")
SQL_DIR = os.path.join(BASE, "..", "data", "sql")
os.makedirs(PROCESSED_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

tablas = ["departamentos", "categorias", "periodos", "presupuesto", "ejecucion_real_raw", "ejecucion_real_limpia",
          "ingresos", "kpi_presupuesto_detallado", "resumen_financiero_mensual",
          "ingresos_forecast_2026", "presupuesto_2026", "gasto_esperado_2026"]

# ---------------------------------------------------------
# 1. EXCEL - un libro, una hoja por tabla
# ---------------------------------------------------------
excel_path = os.path.join(PROCESSED_DIR, "control_presupuestario.xlsx")
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    for tabla in tablas:
        df = pd.read_sql(f"SELECT * FROM {tabla}", conn)
        df.to_excel(writer, sheet_name=tabla, index=False)
print(f"Excel generado: {excel_path}")

# ---------------------------------------------------------
# 2. JSON - un archivo por tabla
# ---------------------------------------------------------
for tabla in tablas:
    df = pd.read_sql(f"SELECT * FROM {tabla}", conn)
    json_path = os.path.join(PROCESSED_DIR, f"{tabla}.json")
    df.to_json(json_path, orient="records", indent=2, force_ascii=False)
print(f"JSON generado para {len(tablas)} tablas en {PROCESSED_DIR}")

# ---------------------------------------------------------
# 3. SQL DUMP - script de texto plano (CREATE + INSERT)
#    Esto es lo que se sube a GitHub como "version SQL" del dataset
# ---------------------------------------------------------
sql_path = os.path.join(SQL_DIR, "schema_and_data.sql")
with open(sql_path, "w", encoding="utf-8") as f:
    for linea in conn.iterdump():
        f.write(f"{linea}\n")
print(f"Dump SQL generado: {sql_path}")

conn.close()
