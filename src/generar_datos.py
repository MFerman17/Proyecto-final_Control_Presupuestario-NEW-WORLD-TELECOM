"""
Generador de dataset sintetico para el proyecto final:
Sistema de Control Presupuestario y KPIs Financieros - Empresa de Telecomunicaciones (España)

Calibrado con datos reales del mercado español:
- Salario medio bruto mensual España (INE, EPA 2024): 2.385,6 EUR
- Coste de Seguridad Social a cargo de la empresa: ~30% adicional sobre el bruto
- Los salarios por rol se ajustan por encima/debajo de la media segun el sector
  (IT y ventas por encima de la media; atencion al cliente y logistica en linea
  con la media; fuente: informes sectoriales Adecco/Michael Page 2025)
"""
import random
import sqlite3
import csv
import os
from datetime import date

random.seed(42)

# ---------------------------------------------------------
# 1. DIMENSIONES MAESTRAS
# ---------------------------------------------------------
departamentos = [
    (1, "Atencion al Cliente"),
    (2, "Ventas B2B"),
    (3, "Operaciones y Logistica"),
    (4, "Marketing"),
    (5, "Tecnologia y TI"),
    (6, "Administracion y Finanzas"),
]

categorias = [
    (1, "Nomina y Personal"),
    (2, "Gastos Operativos"),
    (3, "Marketing y Publicidad"),
    (4, "Tecnologia e Infraestructura"),
    (5, "Capacitacion y Desarrollo"),
]

meses = [
    (1, 2025, 1), (2, 2025, 2), (3, 2025, 3), (4, 2025, 4),
    (5, 2025, 5), (6, 2025, 6), (7, 2025, 7), (8, 2025, 8),
    (9, 2025, 9), (10, 2025, 10), (11, 2025, 11), (12, 2025, 12),
]  # (id_periodo, anio, mes)

dept_lookup = {nombre: idd for idd, nombre in departamentos}
cat_lookup = {nombre: idd for idd, nombre in categorias}

# ---------------------------------------------------------
# 2. NOMINA: calculada como plantilla x salario medio del rol x 1.30 (coste SS)
#    en vez de un numero inventado -> trazable y defendible ante el profesor
# ---------------------------------------------------------
COSTE_SS = 1.30  # coste empresa = salario bruto x 1.30 (cotizacion Seguridad Social)

plantilla_nomina = {
    # departamento: (num_empleados, salario_bruto_medio_mensual)
    "Atencion al Cliente": (15, 2200),   # en linea con la media INE
    "Ventas B2B": (9, 2900),             # por encima de la media (comercial + variable)
    "Operaciones y Logistica": (17, 2150),
    "Marketing": (7, 2500),
    "Tecnologia y TI": (11, 3200),       # sector con salarios mas altos
    "Administracion y Finanzas": (8, 2450),
}

base_presupuesto = {}
for dept, (n_emp, salario) in plantilla_nomina.items():
    base_presupuesto[(dept, "Nomina y Personal")] = round(n_emp * salario * COSTE_SS, 2)

# Resto de categorias de gasto (operativos, marketing, tech, formacion) por departamento
otros_gastos = {
    ("Atencion al Cliente", "Gastos Operativos"): 8000,
    ("Atencion al Cliente", "Tecnologia e Infraestructura"): 5000,
    ("Atencion al Cliente", "Capacitacion y Desarrollo"): 2500,

    ("Ventas B2B", "Gastos Operativos"): 6000,
    ("Ventas B2B", "Marketing y Publicidad"): 4000,
    ("Ventas B2B", "Capacitacion y Desarrollo"): 3000,

    ("Operaciones y Logistica", "Gastos Operativos"): 22000,
    ("Operaciones y Logistica", "Tecnologia e Infraestructura"): 9000,

    ("Marketing", "Marketing y Publicidad"): 35000,
    ("Marketing", "Gastos Operativos"): 4000,

    ("Tecnologia y TI", "Tecnologia e Infraestructura"): 28000,
    ("Tecnologia y TI", "Capacitacion y Desarrollo"): 4000,

    ("Administracion y Finanzas", "Gastos Operativos"): 7000,
    ("Administracion y Finanzas", "Tecnologia e Infraestructura"): 3000,
}
base_presupuesto.update(otros_gastos)

# ---------------------------------------------------------
# 3. GENERAR PRESUPUESTO (limpio, con variacion mensual leve)
# ---------------------------------------------------------
presupuesto_rows = []
pid = 1
for (dept_nombre, cat_nombre), monto_base in base_presupuesto.items():
    for periodo_id, anio, mes in meses:
        variacion = random.uniform(-0.02, 0.02)
        monto = round(monto_base * (1 + variacion), 2)
        presupuesto_rows.append([
            pid, dept_lookup[dept_nombre], cat_lookup[cat_nombre], periodo_id, monto
        ])
        pid += 1

# ---------------------------------------------------------
# 4. GENERAR EJECUCION REAL (desviaciones moderadas y defendibles + suciedad)
#    Marketing y Tecnologia sobreejecutan levemente porque estan invirtiendo
#    en el crecimiento de ingresos digitales (ver tabla de ingresos abajo).
#    El resto se mantiene controlado, acorde al presupuesto planteado.
# ---------------------------------------------------------
perfil_desviacion = {
    "Atencion al Cliente": (0.97, 1.03),
    "Ventas B2B": (0.96, 1.06),
    "Operaciones y Logistica": (0.97, 1.08),
    "Marketing": (0.98, 1.12),
    "Tecnologia y TI": (0.99, 1.14),
    "Administracion y Finanzas": (0.96, 1.02),
}

variantes_nombre = {
    "Atencion al Cliente": ["Atencion al Cliente", "ATENCION AL CLIENTE", "atencion cliente", "At. Cliente"],
    "Ventas B2B": ["Ventas B2B", "VENTAS B2B", "ventas b2b ", "Ventas Corporativas B2B"],
    "Operaciones y Logistica": ["Operaciones y Logistica", "OPERACIONES Y LOGISTICA", "Operaciones/Logistica", "operaciones y logistica"],
    "Marketing": ["Marketing", "MARKETING", "marketing ", "Mercadeo"],
    "Tecnologia y TI": ["Tecnologia y TI", "TECNOLOGIA Y TI", "TI", "Tecnologia/TI"],
    "Administracion y Finanzas": ["Administracion y Finanzas", "ADMINISTRACION Y FINANZAS", "Admin y Finanzas", "administracion y finanzas"],
}

ejecucion_rows = []
eid = 1
for (dept_nombre, cat_nombre), monto_base in base_presupuesto.items():
    lo, hi = perfil_desviacion[dept_nombre]
    for periodo_id, anio, mes in meses:
        factor = random.uniform(lo, hi)
        monto = round(monto_base * factor, 2)

        nombre_usado = dept_nombre
        if random.random() < 0.30:
            nombre_usado = random.choice(variantes_nombre[dept_nombre])

        monto_sucio = monto
        r = random.random()
        if r < 0.03:
            monto_sucio = ""
        elif r < 0.06:
            monto_sucio = "N/D"
        elif r < 0.08:
            monto_sucio = f"{monto:,.2f} EUR"
        elif r < 0.10:
            monto_sucio = str(monto).replace(".", ",")
        elif r < 0.12:
            monto_sucio = -abs(monto)

        fecha_registro = date(anio, mes, min(28, random.randint(1, 28)))

        ejecucion_rows.append([eid, nombre_usado, cat_nombre, anio, mes, monto_sucio, str(fecha_registro)])
        eid += 1

        if random.random() < 0.02:
            ejecucion_rows.append([eid, nombre_usado, cat_nombre, anio, mes, monto_sucio, str(fecha_registro)])
            eid += 1

# ---------------------------------------------------------
# 5. GENERAR INGRESOS (nuevo) - 3 lineas de negocio con crecimiento real
#    Vinculadas a departamentos existentes -> se integra al esquema estrella
#    sin crear dimensiones nuevas.
# ---------------------------------------------------------
lineas_ingreso = {
    # (departamento, concepto): (monto_base_enero, crecimiento_mensual_compuesto)
    ("Ventas B2B", "Servicios B2B Corporativos"): (258000, 0.0119),          # ~15% anual
    ("Atencion al Cliente", "Servicios Residenciales"): (150000, 0.0041),     # ~5% anual
    ("Tecnologia y TI", "Servicios de Valor Añadido (Cloud/Digital)"): (68000, 0.0260),  # ~35% anual
}

# Factor estacional: caida en agosto (vacaciones en España), repunte cierre de año
estacionalidad = {1: 1.00, 2: 1.00, 3: 1.01, 4: 1.01, 5: 1.02, 6: 1.00,
                  7: 0.97, 8: 0.90, 9: 1.03, 10: 1.02, 11: 1.02, 12: 1.04}

ingresos_rows = []
iid = 1
for (dept_nombre, concepto), (monto_base, crecimiento) in lineas_ingreso.items():
    for idx, (periodo_id, anio, mes) in enumerate(meses):
        monto_tendencia = monto_base * ((1 + crecimiento) ** idx)
        monto_estacional = monto_tendencia * estacionalidad[mes]
        ruido = random.uniform(-0.015, 0.015)
        monto = round(monto_estacional * (1 + ruido), 2)
        ingresos_rows.append([iid, dept_lookup[dept_nombre], concepto, periodo_id, monto])
        iid += 1

# ---------------------------------------------------------
# 6. GUARDAR CSVs
# ---------------------------------------------------------
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
SQL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sql")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(SQL_DIR, exist_ok=True)

with open(os.path.join(RAW_DIR, "presupuesto.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id_presupuesto", "departamento_id", "categoria_id", "periodo_id", "monto_presupuestado"])
    w.writerows(presupuesto_rows)

with open(os.path.join(RAW_DIR, "ejecucion_real_raw.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id_ejecucion", "departamento", "categoria", "anio", "mes", "monto_ejecutado", "fecha_registro"])
    w.writerows(ejecucion_rows)

with open(os.path.join(RAW_DIR, "ingresos.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id_ingreso", "departamento_id", "concepto", "periodo_id", "monto_ingresos"])
    w.writerows(ingresos_rows)

with open(os.path.join(RAW_DIR, "departamentos.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["departamento_id", "nombre"])
    w.writerows(departamentos)

with open(os.path.join(RAW_DIR, "categorias.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["categoria_id", "nombre"])
    w.writerows(categorias)

with open(os.path.join(RAW_DIR, "periodos.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["periodo_id", "anio", "mes"])
    w.writerows(meses)

# ---------------------------------------------------------
# 7. CONSTRUIR BASE DE DATOS SQLite
# ---------------------------------------------------------
conn = sqlite3.connect(os.path.join(SQL_DIR, "control_presupuestario.db"))
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS departamentos")
cur.execute("CREATE TABLE departamentos (departamento_id INTEGER PRIMARY KEY, nombre TEXT)")
cur.executemany("INSERT INTO departamentos VALUES (?,?)", departamentos)

cur.execute("DROP TABLE IF EXISTS categorias")
cur.execute("CREATE TABLE categorias (categoria_id INTEGER PRIMARY KEY, nombre TEXT)")
cur.executemany("INSERT INTO categorias VALUES (?,?)", categorias)

cur.execute("DROP TABLE IF EXISTS periodos")
cur.execute("CREATE TABLE periodos (periodo_id INTEGER PRIMARY KEY, anio INTEGER, mes INTEGER)")
cur.executemany("INSERT INTO periodos VALUES (?,?,?)", meses)

cur.execute("DROP TABLE IF EXISTS presupuesto")
cur.execute("""CREATE TABLE presupuesto (
    id_presupuesto INTEGER PRIMARY KEY, departamento_id INTEGER, categoria_id INTEGER,
    periodo_id INTEGER, monto_presupuestado REAL,
    FOREIGN KEY (departamento_id) REFERENCES departamentos(departamento_id),
    FOREIGN KEY (categoria_id) REFERENCES categorias(categoria_id),
    FOREIGN KEY (periodo_id) REFERENCES periodos(periodo_id)
)""")
cur.executemany("INSERT INTO presupuesto VALUES (?,?,?,?,?)", presupuesto_rows)

cur.execute("DROP TABLE IF EXISTS ejecucion_real_raw")
cur.execute("""CREATE TABLE ejecucion_real_raw (
    id_ejecucion INTEGER PRIMARY KEY, departamento TEXT, categoria TEXT,
    anio INTEGER, mes INTEGER, monto_ejecutado TEXT, fecha_registro TEXT
)""")
cur.executemany("INSERT INTO ejecucion_real_raw VALUES (?,?,?,?,?,?,?)", ejecucion_rows)

cur.execute("DROP TABLE IF EXISTS ingresos")
cur.execute("""CREATE TABLE ingresos (
    id_ingreso INTEGER PRIMARY KEY, departamento_id INTEGER, concepto TEXT,
    periodo_id INTEGER, monto_ingresos REAL,
    FOREIGN KEY (departamento_id) REFERENCES departamentos(departamento_id),
    FOREIGN KEY (periodo_id) REFERENCES periodos(periodo_id)
)""")
cur.executemany("INSERT INTO ingresos VALUES (?,?,?,?,?)", ingresos_rows)

conn.commit()
conn.close()

# ---------------------------------------------------------
# 8. RESUMEN
# ---------------------------------------------------------
total_presupuesto_anual = sum(r[4] for r in presupuesto_rows)
total_ingresos_anual = sum(r[4] for r in ingresos_rows)
ingresos_enero = sum(r[4] for r in ingresos_rows if meses[[m[0] for m in meses].index(r[3])][2] == 1)
ingresos_diciembre = sum(r[4] for r in ingresos_rows if meses[[m[0] for m in meses].index(r[3])][2] == 12)
crecimiento = (ingresos_diciembre / ingresos_enero - 1) * 100

print(f"Presupuesto: {len(presupuesto_rows)} filas | Total anual: {total_presupuesto_anual:,.0f} EUR")
print(f"Ejecucion real (raw, sucia): {len(ejecucion_rows)} filas")
print(f"Ingresos: {len(ingresos_rows)} filas | Total anual: {total_ingresos_anual:,.0f} EUR")
print(f"Crecimiento ingresos enero -> diciembre: {crecimiento:.1f}%")
print(f"Margen operativo anual aprox: {(1 - total_presupuesto_anual/total_ingresos_anual)*100:.1f}%")
