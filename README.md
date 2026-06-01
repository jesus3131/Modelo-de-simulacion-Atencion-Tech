# TechClassUC — Simulación M/M/c

Sistema de simulación de atención al cliente para **TechClassUC** usando SimPy (eventos discretos) y Montecarlo.

## Estructura

| Archivo | Descripción |
|---|---|
| `cliente.py` | Clase Cliente |
| `servidor.py` | Recurso SimPy |
| `simulacion_des.py` | Simulación DES |
| `montecarlo.py` | Réplicas Montecarlo |
| `analitico.py` | Fórmulas M/M/c |
| `sensibilidad.py` | Análisis de sensibilidad |
| `visualizacion.py` | Gráficas Matplotlib |
| `app.py` | API Flask |
| `index.html` | Frontend web |
| `main.py` | Ejecución por consola |

## Ejecución local

```bash
pip install -r requirements.txt
python main.py --lam 10 --mu 4 --c 3 --N 30
```

## Web (local)

```bash
python app.py
# Abrir http://localhost:5050
```

## Deploy en Render

Conectar repositorio a Render como **Web Service**, el `render.yaml` configurará automáticamente el servicio.
