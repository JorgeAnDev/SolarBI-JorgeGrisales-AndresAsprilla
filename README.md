# Proyecto SolarBI: Pipeline de Datos Solares

## 📋 Descripción del Trabajo
Este repositorio contiene el desarrollo del taller de ingeniería de datos para el sistema **SolarBI**. El proyecto implementa una arquitectura por capas (**Bronze**, **Silver** y **Gold/DWH**) para la ingesta, limpieza de datos, almacenamiento idempotente en PostgreSQL, y visualización ejecutiva mediante Power BI y Grafana OSS.

## 👥 Integrantes y Datos del Curso
* **Curso:** Inteligencia de negocios BI
* **Grupo:** 01
* **Integrantes:**
  * Jorge Andres Grisales Herrera
  * Andrés  Felipe Asprilla Pedroza

## 🛠️ Estructura del Repositorio
* `docs/`: Documentación formal y entregable en PDF.
* `data/`: Archivos de datos divididos en capas Bronze y Silver.
* `etl/`: Scripts en Python para la simulación de telemetría y ejecución del flujo ETL.
* `sql/`: Scripts DDL y consultas de estructuración en PostgreSQL.
* `powerbi/`: Archivos del modelo y reporte en Power BI (`.pbix`).
* `grafana/`: Exportación del tablero en formato JSON (`solarbi_dashboard.json`).

## 🚀 Pasos para Reproducir la Práctica
1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/solarbi-grisales-herrera.git](https://github.com/tu-usuario/solarbi-grisales-herrera.git)
   cd solarbi-grisales-herrera