"""
Forecast 2026 - Sistema de Control Presupuestario TeleConecta
================================================================
Este script parte UNICAMENTE de los datos reales de 2025 ya construidos
en el proyecto (presupuesto, ejecucion_real_limpia, ingresos, kpi calculados)
y calcula tres proyecciones para 2026, cada una con la metodologia que le
corresponde segun su naturaleza de negocio:

1. INGRESOS -> proyeccion estadistica (tendencia + estacionalidad),
   con intervalo de confianza del 95%, porque depende del mercado.
2. PRESUPUESTO -> decision de planificacion (incremento planificado),
   preservando la variacion mensual real de 2025 (no un promedio plano).
3. GASTO ESPERADO -> ratio historico de ejecucion MENSUAL (no anual)
   aplicado sobre el nuevo presupuesto, para reflejar el patron real
   de cada mes (ej. si Tecnologia sobreejecuta mas en Q4, eso se traslada).

Requiere que existan previamente en la base de datos:
    departamentos, categorias, periodos (12 filas de 2025),
    presupuesto, ejecucion_real_limpia, ingresos, kpi_presupuesto_detallado

Es re-ejecutable de forma segura (idempotente): si los periodos de 2026
ya existen, no los duplica.
"""
import sqlite3
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE, "..", "data", "sql", "control_presupuestario.db")
PROCESSED_DIR = os.path.join(BASE, "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Departamentos que en 2025 invirtieron por encima del presupuesto para
# sostener el crecimiento digital -> formalizan ese esfuerzo como incremento
# planificado mayor en el presupuesto 2026.
DEPARTAMENTOS_CRECIMIENTO = ["Marketing", "Tecnologia y TI"]
INCREMENTO_CRECIMIENTO = 1.06   # +6%
INCREMENTO_ESTANDAR = 1.03      # +3%
NIVEL_CONFIANZA_Z = 1.96        # ~95%


def cargar_datos_base(conn):
    return {
        "departamentos": pd.read_sql("SELECT * FROM departamentos", conn),
        "categorias": pd.read_sql("SELECT * FROM categorias", conn),
        "periodos": pd.read_sql("SELECT * FROM periodos", conn),
        "presupuesto": pd.read_sql("SELECT * FROM presupuesto", conn),
        "ejecucion": pd.read_sql("SELECT * FROM ejecucion_real_limpia", conn),
        "ingresos": pd.read_sql("SELECT * FROM ingresos", conn),
        "kpi": pd.read_sql("SELECT * FROM kpi_presupuesto_detallado", conn),
    }


def extender_periodos_2026(conn, df_periodos):
    """Agrega 12 filas para 2026 (periodo_id 13-24) si aun no existen."""
    if (df_periodos["anio"] == 2026).any():
        return pd.read_sql("SELECT * FROM periodos", conn)  # ya existe, no duplicar

    max_id = int(df_periodos["periodo_id"].max())
    nuevos = [(max_id + i, 2026, i) for i in range(1, 13)]
    conn.executemany("INSERT INTO periodos VALUES (?,?,?)", nuevos)
    conn.commit()
    return pd.read_sql("SELECT * FROM periodos", conn)


def forecast_ingresos(df_ingresos, df_periodos, mapa_periodo_2026):
    """Tendencia lineal + indice estacional + intervalo de confianza 95%."""
    p2025 = df_periodos[df_periodos["anio"] == 2025]
    por_linea = (df_ingresos.merge(p2025, on="periodo_id")
                 .groupby(["departamento_id", "concepto", "mes"])["monto_ingresos"]
                 .sum().reset_index())

    filas = []
    for (dept_id, concepto), grupo in por_linea.groupby(["departamento_id", "concepto"]):
        grupo = grupo.sort_values("mes")
        x, y = grupo["mes"].values, grupo["monto_ingresos"].values

        pendiente, intercepto = np.polyfit(x, y, 1)
        tendencia = pendiente * x + intercepto
        indice_estacional = y / tendencia
        error_estandar = np.std(y - tendencia, ddof=2)
        margen = NIVEL_CONFIANZA_Z * error_estandar

        x_2026 = np.arange(13, 25)
        forecast_vals = (pendiente * x_2026 + intercepto) * indice_estacional

        for mes, monto in zip(range(1, 13), forecast_vals):
            filas.append([dept_id, concepto, mapa_periodo_2026[mes],
                          round(monto, 2), round(monto - margen, 2), round(monto + margen, 2)])

    df = pd.DataFrame(filas, columns=["departamento_id", "concepto", "periodo_id",
                                       "monto_ingresos_forecast", "monto_min", "monto_max"])
    df.insert(0, "id_forecast", range(1, len(df) + 1))
    return df


def presupuesto_2026(df_presupuesto, df_periodos, df_departamentos, mapa_periodo_2026):
    """Preserva la variacion mensual real de 2025, escalada por el incremento planificado."""
    ids_crecimiento = df_departamentos[
        df_departamentos["nombre"].isin(DEPARTAMENTOS_CRECIMIENTO)]["departamento_id"].tolist()

    p2025 = df_periodos[df_periodos["anio"] == 2025]
    base = (df_presupuesto.merge(p2025, on="periodo_id")
            [["departamento_id", "categoria_id", "mes", "monto_presupuestado"]])

    filas = []
    for _, row in base.iterrows():
        factor = INCREMENTO_CRECIMIENTO if row["departamento_id"] in ids_crecimiento else INCREMENTO_ESTANDAR
        monto = round(row["monto_presupuestado"] * factor, 2)
        filas.append([row["departamento_id"], row["categoria_id"],
                      mapa_periodo_2026[row["mes"]], monto])

    df = pd.DataFrame(filas, columns=["departamento_id", "categoria_id", "periodo_id",
                                       "monto_presupuestado_2026"])
    df.insert(0, "id_presupuesto", range(1, len(df) + 1))
    return df


def gasto_esperado_2026(df_presupuesto_2026, df_kpi, df_periodos):
    """Aplica el ratio de ejecucion historico POR MES (no el promedio anual)."""
    p2025 = df_periodos[df_periodos["anio"] == 2025]
    ratio_mensual = (df_kpi.merge(p2025, on="periodo_id")
                     [["departamento_id", "categoria_id", "mes", "pct_ejecucion"]])

    p2026 = df_periodos[df_periodos["anio"] == 2026]
    base = df_presupuesto_2026.merge(p2026, on="periodo_id")
    base = base.merge(ratio_mensual, on=["departamento_id", "categoria_id", "mes"], how="left")
    base["pct_ejecucion"] = base["pct_ejecucion"].fillna(1.0)
    base["monto_gasto_esperado"] = round(base["monto_presupuestado_2026"] * base["pct_ejecucion"], 2)

    df = base[["departamento_id", "categoria_id", "periodo_id", "monto_gasto_esperado"]].copy()
    df.insert(0, "id_gasto", range(1, len(df) + 1))
    return df


def guardar(conn, nombre_tabla, df):
    df.to_sql(nombre_tabla, conn, if_exists="replace", index=False)
    df.to_csv(os.path.join(PROCESSED_DIR, f"{nombre_tabla}.csv"), index=False)


def main():
    conn = sqlite3.connect(DB_PATH)
    datos = cargar_datos_base(conn)

    df_periodos = extender_periodos_2026(conn, datos["periodos"])
    mapa_periodo_2026 = {row["mes"]: row["periodo_id"]
                          for _, row in df_periodos[df_periodos["anio"] == 2026].iterrows()}

    df_ing_fc = forecast_ingresos(datos["ingresos"], df_periodos, mapa_periodo_2026)
    df_pres_fc = presupuesto_2026(datos["presupuesto"], df_periodos, datos["departamentos"], mapa_periodo_2026)
    df_gasto_fc = gasto_esperado_2026(df_pres_fc, datos["kpi"], df_periodos)

    guardar(conn, "ingresos_forecast_2026", df_ing_fc)
    guardar(conn, "presupuesto_2026", df_pres_fc)
    guardar(conn, "gasto_esperado_2026", df_gasto_fc)
    conn.commit()

    # ---- Verificacion de resultados ----
    total_ing_2025 = datos["ingresos"]["monto_ingresos"].sum()
    total_ing_2026 = df_ing_fc["monto_ingresos_forecast"].sum()
    total_pres_2025 = datos["presupuesto"]["monto_presupuestado"].sum()
    total_pres_2026 = df_pres_fc["monto_presupuestado_2026"].sum()
    total_gasto_2026 = df_gasto_fc["monto_gasto_esperado"].sum()

    print("=" * 60)
    print("FORECAST 2026 - RESUMEN")
    print("=" * 60)
    print(f"Ingresos      2025: {total_ing_2025:>14,.0f} EUR")
    print(f"Ingresos      2026: {total_ing_2026:>14,.0f} EUR  ({(total_ing_2026/total_ing_2025-1)*100:+.1f}%)")
    print(f"Presupuesto   2025: {total_pres_2025:>14,.0f} EUR")
    print(f"Presupuesto   2026: {total_pres_2026:>14,.0f} EUR  ({(total_pres_2026/total_pres_2025-1)*100:+.1f}%)")
    print(f"Gasto esperado 2026: {total_gasto_2026:>13,.0f} EUR")
    print(f"Margen operativo esperado 2026: {(1 - total_gasto_2026/total_ing_2026)*100:.1f}%")
    print("=" * 60)
    print("Tablas guardadas en SQLite y en data/processed/:")
    print("  - ingresos_forecast_2026.csv (incluye monto_min / monto_max, IC 95%)")
    print("  - presupuesto_2026.csv (variacion mensual preservada)")
    print("  - gasto_esperado_2026.csv (ratio de ejecucion mensual aplicado)")

    conn.close()


if __name__ == "__main__":
    main()
