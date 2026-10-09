import os
import pandas as pd
import psycopg2

# Configuración de conexión a PostgreSQL local
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "solarbi_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")  
DB_PORT = os.getenv("DB_PORT", "5432")

def ejecutar_etapa_silver_gold():
    print("Iniciando procesamiento ETL (Capas Silver y Gold)...")
    
    # 1. Leer el archivo Bronze con pandas
    ruta_bronze = "data/bronze/telemetria.csv"
    if not os.path.exists(ruta_bronze):
        print("¡Error! No se encuentra el archivo telemetria.csv. Ejecuta primero el simulador.py")
        return

    df = pd.read_csv(ruta_bronze)
    filas_leidas = len(df)

    # 2. Aplicar Reglas de Calidad.
    # Regla A: Datos faltantes / nulos en columnas clave
    antes_nulos = len(df)
    df = df.dropna(subset=["ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"])
    rechazadas_nulos = antes_nulos - len(df)

    # Regla B: Rango físico válido (potencia e irradiancia no pueden ser negativas)
    antes_rango = len(df)
    df = df[(df["p_ac_kw"] >= 0) & (df["irradiancia_wm2"] >= 0)]
    rechazadas_rango = antes_rango - len(df)

    # Regla C: Duplicados exactos
    antes_dup = len(df)
    df = df.drop_duplicates()
    duplicados = antes_dup - len(df)

    # Cálculo final de métricas de calidad
    filas_validas = len(df)
    pct_datos_validos = (filas_validas / filas_leidas) * 100 if filas_leidas > 0 else 0

    # Imprimir el reporte en consola (¡Esta será tu evidencia!)
    print("\n========================================")
    print("       REPORTE DE CALIDAD (SILVER)      ")
    print("========================================")
    print(f"• Filas leídas inicialmente: {filas_leidas}")
    print(f"• Rechazadas por datos faltantes: {rechazadas_nulos}")
    print(f"• Rechazadas por rango físico inválido: {rechazadas_rango}")
    print(f"• Filas duplicadas descartadas: {duplicados}")
    print(f"• Filas válidas finales: {filas_validas}")
    print(f"• Porcentaje de datos válidos: {pct_datos_validos:.2f}%")
    print("========================================\n")

    # 3. Conexión y carga en PostgreSQL (Capa Silver y Gold)
    try:
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT
        )
        cur = conn.cursor()

        # Crear esquemas y tablas
        cur.execute("CREATE SCHEMA IF NOT EXISTS silver;")
        cur.execute("CREATE SCHEMA IF NOT EXISTS dwh;")
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS silver.lectura_5min (
                ts TIMESTAMP,
                dispositivo_id INT,
                p_ac_kw DECIMAL(10,3),
                irradiancia_wm2 DECIMAL(10,1),
                temp_modulo_c DECIMAL(5,1),
                PRIMARY KEY (ts, dispositivo_id)
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS dwh.fact_energia_dia (
                fecha_key DATE,
                dispositivo_key INT,
                energia_kwh DECIMAL(12,3),
                pct_datos_validos DECIMAL(5,2),
                PRIMARY KEY (fecha_key, dispositivo_key)
            );
        """)

        # Insertar registros limpios en Silver
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO silver.lectura_5min (ts, dispositivo_id, p_ac_kw, irradiancia_wm2, temp_modulo_c)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (ts, dispositivo_id) DO UPDATE 
                SET p_ac_kw = EXCLUDED.p_ac_kw,
                    irradiancia_wm2 = EXCLUDED.irradiancia_wm2,
                    temp_modulo_c = EXCLUDED.temp_modulo_c;
            """, (row["ts"], row["dispositivo_id"], row["p_ac_kw"], row["irradiancia_wm2"], row["temp_modulo_c"]))

        # Calcular agregados diarios (Gold: energia = potencia * 5/60 horas) y guardar en fact_energia_dia
        df['ts'] = pd.to_datetime(df['ts'])
        df['fecha_key'] = df['ts'].dt.date
        df['energia_intervalo'] = df['p_ac_kw'] * (5.0 / 60.0)
        
        resumen_diario = df.groupby(['fecha_key', 'dispositivo_id'])['energia_intervalo'].sum().reset_index()

        for _, row in resumen_diario.iterrows():
            cur.execute("""
                INSERT INTO dwh.fact_energia_dia (fecha_key, dispositivo_key, energia_kwh, pct_datos_validos)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (fecha_key, dispositivo_key) DO UPDATE
                SET energia_kwh = EXCLUDED.energia_kwh,
                    pct_datos_validos = EXCLUDED.pct_datos_validos;
            """, (row['fecha_key'], row['dispositivo_id'], row['energia_intervalo'], pct_datos_validos))

        conn.commit()
        cur.close()
        conn.close()
        print("¡Datos limpios cargados exitosamente en PostgreSQL (Capas Silver y Gold) de forma idempotente!")

    except Exception as e:
        print(f"Nota: Los datos se limpiaron con Pandas, pero hubo un error conectando a PostgreSQL: {e}")
        print("Asegúrate de crear tu base de datos local en PostgreSQL o ajustar tus credenciales.")

if __name__ == "__main__":
    ejecutar_etapa_silver_gold()