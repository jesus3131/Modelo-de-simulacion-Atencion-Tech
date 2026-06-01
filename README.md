# TechClassUC — Simulación M/M/c

Sistema de simulación de atención al cliente para **TechClassUC** usando **SimPy** (eventos discretos) y análisis **Montecarlo**. Modela un sistema de colas M/M/c donde `c` técnicos atienden solicitudes que llegan con tasa λ y se procesan con tasa μ por servidor.

---

## Requisitos

- Python 3.9+
- Dependencias (se instalan con `pip`):
  ```
  simpy, numpy, matplotlib, flask, flask-cors, scipy, gunicorn
  ```

Instalación rápida:

```bash
pip install -r requirements.txt
```

---

## Ejecución por Consola (main.py)

El punto de entrada principal para ejecutar la simulación desde terminal:

```bash
python main.py [opciones]
```

### Parámetros disponibles

| Argumento | Tipo | Default | Descripción |
|---|---|---|---|
| `--lam` | float | 10.0 | Tasa de llegada λ (clientes/hora) |
| `--mu` | float | 4.0 | Tasa de servicio μ (clientes/hora/técnico) |
| `--c` | int | 3 | Número de técnicos (servidores) |
| `--t-sim` | float | 480.0 | Duración de la simulación (minutos) |
| `--t-warm` | float | 60.0 | Período de calentamiento a descartar (minutos) |
| `--N` | int | 30 | Número de réplicas Montecarlo |
| `--semilla` | int | 42 | Semilla base para números aleatorios |
| `--umbral-wq` | float | 10.0 | Umbral de Wq para búsqueda de c óptimo (minutos) |
| `--prioridad` | flag | — | Activa cola con prioridad (urgentes > normales) |
| `--no-graficas` | flag | — | Omite la generación de gráficas |
| `--output-dir` | str | "graficas" | Directorio donde guardar las gráficas |

### Ejemplos de uso

```bash
# Valores base (λ=10, μ=4, c=3, N=30)
python main.py

# Escenario con mayor carga y más réplicas
python main.py --lam 12 --mu 4 --c 4 --N 50

# Buscar c óptimo con umbral de 5 min
python main.py --lam 10 --mu 4 --N 20 --umbral-wq 5

# Con cola prioritaria y simulación de 2 horas
python main.py --lam 8 --mu 3 --c 2 --t-sim 120 --t-warm 20 --prioridad

# Solo validación rápida (pocas réplicas, sin gráficas)
python main.py --lam 10 --mu 4 --c 3 --N 5 --no-graficas
```

### Salida esperada

La consola muestra:
1. **Réplica representativa** — una corrida individual con evolución temporal
2. **Montecarlo** — medias, desviaciones e intervalos de confianza al 95% de Wq, Ws, Lq, ρ
3. **Validación analítica** — comparación contra fórmulas M/M/c con error porcentual
4. **Análisis de sensibilidad** — barrido de combinaciones c × λ
5. **c óptimo** — mínimo número de técnicos que cumple Wq ≤ umbral
6. **Gráficas** — 7 archivos PNG guardados en `--output-dir`

---

## Ejecución Web (app.py + index.html)

Interfaz gráfica con panel de control y visualización de resultados.

### Iniciar el servidor

```bash
python app.py
```

Esto levanta el servidor en `http://localhost:5050`. Abre `index.html` en el navegador (o directamente la URL si usas Render).

### Panel de parámetros

| Control | Descripción |
|---|---|
| **λ — llegadas/hora** | Tasa de llegada de clientes (0.1–50) |
| **μ — servicio/técnico/h** | Capacidad de servicio por técnico |
| **c — técnicos** | Número de servidores en paralelo |
| **N — réplicas** | Cantidad de corridas Montecarlo (5–100) |
| **T_sim (min)** | Duración de la simulación |
| **T_warm (min)** | Período de calentamiento |
| **Umbral Wq (min)** | Tiempo de espera máximo deseado |
| **Semilla** | Semilla base para reproducibilidad |
| **Cola con prioridad** | Activa prioridad para clientes urgentes |
| **Modo rápido** | Reduce combinaciones en sensibilidad |

El indicador **ρ** (utilización) se actualiza en vivo:
- Verde: estable (ρ < 0.85)
- Amarillo: alta carga (ρ 0.85–0.99)
- Rojo: inestable (ρ ≥ 1.0)

### Resultados

Después de ejecutar, la interfaz muestra:

- **KPIs**: Wq, ρ, Lq, Ws con intervalo de confianza al 95%
- **c óptimo**: recomendación de técnicos necesarios
- **N mínimo**: réplicas requeridas para error relativo ≤ 5%
- **Validación analítica**: tabla comparativa simulación vs M/M/c
- **7 gráficas interactivas** (navegación por pestañas):
  1. Evolución temporal N(t)
  2. Histograma de tiempos de espera Wq
  3. Curva Wq vs número de técnicos
  4. Utilización ρ vs tasa de llegada λ
  5. Verificación del Teorema Central del Límite
  6. Heatmap de Wq (c × λ)
  7. Heatmap de ρ (c × λ)
- **Tabla de sensibilidad**: todas las combinaciones c × λ evaluadas

---

## Despliegue en Render

Incluye configuración lista para Render:

| Archivo | Propósito |
|---|---|
| `requirements.txt` | Dependencias Python |
| `Procfile` | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| `render.yaml` | Configuración automatizada como Web Service |
| `runtime.txt` | Python 3.11 |

### Pasos

1. Subir el repositorio a GitHub
2. En [dashboard.render.com](https://dashboard.render.com), crear **New Web Service**
3. Conectar el repositorio
4. Render detecta automáticamente `requirements.txt` y `Procfile`
5. Colocar en **Start Command**:
   ```
   gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 300
   ```
6. Hacer clic en **Deploy**

---

## Estructura del Proyecto

| Archivo | Descripción |
|---|---|
| `cliente.py` | Clase `Cliente` con atributos (id, tipo, prioridad, tiempos) |
| `servidor.py` | `ServidorTracker`: envoltura de `simpy.Resource` con estadísticas |
| `simulacion_des.py` | Motor DES con SimPy: `correr_una_replica()` |
| `montecarlo.py` | Ejecución de N réplicas: `correr_replicas()`, IC 95%, N mínimo |
| `analitico.py` | Fórmulas cerradas M/M/c: `calcular_mmc()`, `comparar_con_simulacion()` |
| `sensibilidad.py` | Barrido paramétrico c×λ: `analisis_sensibilidad()`, `encontrar_c_optimo()` |
| `visualizacion.py` | 7 gráficas Matplotlib exportadas a PNG |
| `app.py` | API Flask con endpoints `/api/simular` y `/api/health` |
| `index.html` | Frontend web con panel de control y visualización |
| `main.py` | Punto de entrada por consola con argparse |

---

## Interpretación de Métricas

| Métrica | Descripción | Fórmula |
|---|---|---|
| **ρ** | Fracción de tiempo que los servidores están ocupados | λ / (c·μ) |
| **Wq** | Tiempo promedio que un cliente espera en cola | Lq / λ |
| **Ws** | Tiempo total desde que llega hasta que termina | Wq + 1/μ |
| **Lq** | Número promedio de clientes en cola | — |
| **L** | Número promedio de clientes en el sistema | Lq + λ/μ |
| **IC 95%** | Intervalo de confianza al 95% para la media estimada | — |
| **N mínimo** | Réplicas necesarias para error relativo ≤ 5% | — |

### Condición de estabilidad

El sistema es estable si **ρ < 1**. Si ρ ≥ 1 la cola crece indefinidamente y la simulación se rechaza.

---

## Ejemplo: λ=10, μ=4, c=3 (base)

```
ρ = 10 / (3 × 4) = 0.8333  → Estable pero con alta carga

Resultados típicos:
  Wq ≈ 21 min  (analítico)
  ρ  ≈ 0.83
  Lq ≈ 3.5 clientes
  c óptimo ≈ 4 técnicos (para Wq ≤ 10 min)
```

---

## Licencia

Proyecto académico — Modelos de Simulación 2025.
