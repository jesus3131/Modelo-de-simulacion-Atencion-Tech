"""
app.py
------
Servidor Flask que expone la simulación TechClassUC como API REST.
Permite ejecutar la simulación desde una interfaz web.
"""

import sys
import os
import math
import base64
import io

# Asegurar que los módulos del proyecto estén en el path
sys.path.insert(0, os.path.dirname(__file__))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from analitico import calcular_mmc, comparar_con_simulacion
from montecarlo import correr_replicas
from simulacion_des import correr_una_replica
from sensibilidad import analisis_sensibilidad, encontrar_c_optimo
from visualizacion import (
    grafica_evolucion_temporal,
    grafica_histograma_wq,
    grafica_wq_vs_c,
    grafica_rho_vs_lam,
    grafica_distribucion_medias_wq,
    grafica_heatmap_wq,
    grafica_heatmap_rho,
)

app = Flask(__name__)
CORS(app)

GRAFICAS_DIR = os.path.join(os.path.dirname(__file__), "graficas_web")
os.makedirs(GRAFICAS_DIR, exist_ok=True)


@app.route("/")
def index():
    return send_from_directory(os.path.dirname(__file__), "index.html")


def fig_to_base64(fig):
    """Convierte una figura matplotlib a base64 PNG."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode("utf-8")


def grafica_evolucion_b64(evolucion, t_warm):
    tiempos = [p[0] for p in evolucion]
    n_clientes = [p[1] for p in evolucion]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.step(tiempos, n_clientes, where="post", color="#2563EB", linewidth=1.2, label="Clientes en sistema")
    ax.axvline(t_warm, color="#DC2626", linestyle="--", linewidth=1.5, label=f"Fin calentamiento ({t_warm} min)")
    ax.set_xlabel("Tiempo de simulación (minutos)")
    ax.set_ylabel("Número de clientes N(t)")
    ax.set_title("Evolución temporal del sistema")
    ax.legend()
    ax.grid(alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig_to_base64(fig)


def grafica_histograma_b64(wq_todos, wq_media, wq_ic95):
    arr = np.array(wq_todos)
    arr = arr[arr >= 0]
    fig, ax = plt.subplots(figsize=(8, 5))
    n_bins = min(50, max(10, len(arr) // 50))
    ax.hist(arr, bins=n_bins, color="#3B82F6", edgecolor="white", alpha=0.85, density=True)
    ax.axvline(wq_media, color="#DC2626", linewidth=1.8, label=f"Media = {wq_media:.2f} min")
    ax.axvline(wq_ic95[0], color="#F59E0B", linestyle=":", linewidth=1.4,
               label=f"IC 95% = [{wq_ic95[0]:.2f}, {wq_ic95[1]:.2f}]")
    ax.axvline(wq_ic95[1], color="#F59E0B", linestyle=":", linewidth=1.4)
    ax.set_xlabel("Tiempo de espera en cola Wq (minutos)")
    ax.set_ylabel("Densidad")
    ax.set_title("Distribución de tiempos de espera Wq")
    ax.legend()
    ax.grid(alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig_to_base64(fig)


def grafica_wq_vs_c_b64(sens, lam_base, umbral_wq):
    lista_c = sens["lista_c"]
    lista_lam = sens["lista_lam"]
    heatmap = sens["heatmap_wq"]
    idx_lam = int(np.argmin(np.abs(np.array(lista_lam) - lam_base)))
    wq_por_c = heatmap[idx_lam, :]
    fig, ax = plt.subplots(figsize=(8, 5))
    c_validos = [c for c, w in zip(lista_c, wq_por_c) if not np.isnan(w)]
    wq_validos = [w for w in wq_por_c if not np.isnan(w)]
    ax.plot(c_validos, wq_validos, marker="o", color="#7C3AED", linewidth=2, markersize=7,
            label=f"Wq vs c  (λ={lista_lam[idx_lam]:.1f})")
    ax.axhline(umbral_wq, color="#DC2626", linestyle="--", linewidth=1.5, label=f"Umbral = {umbral_wq} min")
    ax.set_xlabel("Número de servidores c")
    ax.set_ylabel("Wq promedio (minutos)")
    ax.set_title("Curva de capacidad: Wq vs. número de técnicos")
    ax.legend()
    ax.grid(alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig_to_base64(fig)


def grafica_rho_vs_lam_b64(sens):
    lista_c = sens["lista_c"]
    lista_lam = sens["lista_lam"]
    curva = sens["curva_rho_vs_lam"]
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(lista_c)))
    fig, ax = plt.subplots(figsize=(9, 5))
    for c, color in zip(lista_c, colors):
        rhos = curva[c]
        lam_validos = [l for l, r in zip(lista_lam, rhos) if r is not None and not np.isnan(r)]
        rho_validos = [r for r in rhos if r is not None and not np.isnan(r)]
        ax.plot(lam_validos, rho_validos, marker="s", linewidth=2, color=color, markersize=6, label=f"c = {c}")
    ax.axhline(1.0, color="#DC2626", linestyle="--", linewidth=1.5, label="ρ = 1 (límite)")
    ax.set_xlabel("Tasa de llegada λ (clientes/hora)")
    ax.set_ylabel("Utilización ρ")
    ax.set_title("Utilización del sistema ρ vs. tasa de llegada λ")
    ax.set_ylim(0, 1.15)
    ax.legend(loc="upper left")
    ax.grid(alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig_to_base64(fig)


def grafica_tcl_b64(wq_medias):
    from scipy import stats
    arr = np.array(wq_medias)
    media = float(np.mean(arr))
    std = float(np.std(arr, ddof=1))
    fig, ax = plt.subplots(figsize=(8, 5))
    n_bins = max(8, len(arr) // 5)
    ax.hist(arr, bins=n_bins, color="#10B981", edgecolor="white", alpha=0.75, density=True, label="Medias réplicas")
    x = np.linspace(arr.min() - std, arr.max() + std, 300)
    ax.plot(x, stats.norm.pdf(x, loc=media, scale=std), color="#1D4ED8", linewidth=2.5,
            label=f"N(μ={media:.2f}, σ={std:.2f})")
    ax.axvline(media, color="#DC2626", linestyle="--", linewidth=1.5, label="Media")
    ax.set_xlabel("Media de Wq por réplica (minutos)")
    ax.set_ylabel("Densidad")
    ax.set_title("Distribución de medias de Wq — verificación TCL")
    ax.legend()
    ax.grid(alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig_to_base64(fig)


def grafica_heatmap_wq_b64(sens):
    lista_c = sens["lista_c"]
    lista_lam = sens["lista_lam"]
    matrix = sens["heatmap_wq"]
    fig, ax = plt.subplots(figsize=(9, 6))
    valid = matrix[~np.isnan(matrix)]
    vmax = np.nanpercentile(valid, 95) if len(valid) > 0 else 1
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd", vmin=np.nanmin(matrix) if len(valid) > 0 else 0, vmax=vmax)
    ax.set_xticks(range(len(lista_c)))
    ax.set_xticklabels([str(c) for c in lista_c])
    ax.set_yticks(range(len(lista_lam)))
    ax.set_yticklabels([f"{l:.0f}" for l in lista_lam])
    ax.set_xlabel("Número de servidores c")
    ax.set_ylabel("Tasa de llegada λ (clientes/hora)")
    ax.set_title("Heatmap: Wq promedio (min)")
    for i in range(len(lista_lam)):
        for j in range(len(lista_c)):
            val = matrix[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=8,
                        color="black" if val < np.nanmedian(matrix) else "white")
            else:
                ax.text(j, i, "N/A", ha="center", va="center", fontsize=8, color="gray")
    plt.colorbar(im, ax=ax, label="Wq (minutos)")
    fig.tight_layout()
    return fig_to_base64(fig)


def grafica_heatmap_rho_b64(sens):
    lista_c = sens["lista_c"]
    lista_lam = sens["lista_lam"]
    matrix = sens["heatmap_rho"]
    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn_r", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(lista_c)))
    ax.set_xticklabels([str(c) for c in lista_c])
    ax.set_yticks(range(len(lista_lam)))
    ax.set_yticklabels([f"{l:.0f}" for l in lista_lam])
    ax.set_xlabel("Número de servidores c")
    ax.set_ylabel("Tasa de llegada λ (clientes/hora)")
    ax.set_title("Heatmap: Utilización ρ")
    for i in range(len(lista_lam)):
        for j in range(len(lista_c)):
            val = matrix[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8,
                        color="black" if val < 0.75 else "white")
            else:
                ax.text(j, i, "N/A", ha="center", va="center", fontsize=8, color="gray")
    plt.colorbar(im, ax=ax, label="Utilización ρ")
    fig.tight_layout()
    return fig_to_base64(fig)


@app.route("/api/simular", methods=["POST"])
def simular():
    """Endpoint principal: ejecuta la simulación completa y devuelve resultados + gráficas."""
    data = request.get_json()

    lam = float(data.get("lam", 10.0))
    mu = float(data.get("mu", 4.0))
    c = int(data.get("c", 3))
    t_sim = float(data.get("t_sim", 480.0))
    t_warm = float(data.get("t_warm", 60.0))
    N = int(data.get("N", 20))
    semilla_base = int(data.get("semilla", 42))
    umbral_wq = float(data.get("umbral_wq", 10.0))
    usar_prioridad = bool(data.get("prioridad", False))
    modo_rapido = bool(data.get("rapido", True))

    # Validar estabilidad
    rho = lam / (c * mu)
    if rho >= 1.0:
        c_min = math.ceil(lam / mu)
        return jsonify({
            "error": True,
            "mensaje": f"Sistema INESTABLE — ρ = {rho:.4f} ≥ 1. Se necesita c ≥ {c_min} técnicos.",
            "rho": rho,
            "c_min": c_min,
        }), 400

    try:
        # 1. Réplica representativa
        replica_base = correr_una_replica(
            lam=lam, mu=mu, c=c, t_sim=t_sim, t_warm=t_warm,
            semilla=semilla_base, usar_prioridad=usar_prioridad,
        )

        # 2. Montecarlo
        res_mc = correr_replicas(
            N=N, lam=lam, mu=mu, c=c,
            t_sim=t_sim, t_warm=t_warm,
            semilla_base=semilla_base,
            usar_prioridad=usar_prioridad,
        )

        # 3. Analítico
        analitico = calcular_mmc(lam, mu, c)
        comparacion = comparar_con_simulacion(analitico, res_mc)

        # 4. Sensibilidad (reducida)
        if modo_rapido:
            lista_c_s = [2, 3, 4, 5]
            lista_lam_s = [8.0, 10.0, 12.0, 14.0]
            N_sens = max(5, N // 4)
        else:
            lista_c_s = [1, 2, 3, 4, 5]
            lista_lam_s = [6.0, 8.0, 10.0, 12.0, 14.0, 16.0]
            N_sens = N

        sens = analisis_sensibilidad(
            mu=mu, t_sim=t_sim, t_warm=t_warm,
            N_replicas=N_sens, semilla_base=semilla_base,
            lista_c=lista_c_s, lista_lam=lista_lam_s,
        )

        # 5. c óptimo
        opt = encontrar_c_optimo(
            lam=lam, mu=mu, t_sim=t_sim, t_warm=t_warm,
            N_replicas=max(5, N // 4), semilla_base=semilla_base,
            umbral_wq=umbral_wq,
        )

        # 6. Gráficas → base64
        graficas = {
            "evolucion": grafica_evolucion_b64(replica_base["evolucion_temporal"], t_warm),
            "histograma_wq": grafica_histograma_b64(res_mc["wq_todas"], res_mc["wq_media"], res_mc["wq_ic95"]),
            "wq_vs_c": grafica_wq_vs_c_b64(sens, lam, umbral_wq),
            "rho_vs_lam": grafica_rho_vs_lam_b64(sens),
            "tcl": grafica_tcl_b64(res_mc["wq_medias_replicas"]),
            "heatmap_wq": grafica_heatmap_wq_b64(sens),
            "heatmap_rho": grafica_heatmap_rho_b64(sens),
        }

        # Serializar sens para JSON (convertir numpy arrays)
        sens_json = {
            "tabla": sens["tabla"],
            "lista_c": sens["lista_c"],
            "lista_lam": sens["lista_lam"],
        }

        return jsonify({
            "error": False,
            "parametros": {"lam": lam, "mu": mu, "c": c, "t_sim": t_sim, "t_warm": t_warm, "N": N},
            "montecarlo": {
                "wq_media": res_mc["wq_media"],
                "wq_std": res_mc["wq_std"],
                "wq_ic95": list(res_mc["wq_ic95"]),
                "ws_media": res_mc["ws_media"],
                "ws_ic95": list(res_mc["ws_ic95"]),
                "lq_media": res_mc["lq_media"],
                "lq_ic95": list(res_mc["lq_ic95"]),
                "rho_media": res_mc["rho_media"],
                "rho_ic95": list(res_mc["rho_ic95"]),
                "n_minimo_replicas": res_mc["n_minimo_replicas"],
                "N": res_mc["N"],
            },
            "analitico": {
                "rho": analitico["rho"],
                "P0": analitico["P0"],
                "Lq": analitico["Lq"],
                "Wq": analitico["Wq"],
                "L": analitico["L"],
                "W": analitico["W"],
            },
            "comparacion": comparacion,
            "c_optimo": {
                "valor": opt["c_optimo"],
                "wq_logrado": opt["wq_logrado"],
                "umbral": umbral_wq,
            },
            "graficas": graficas,
            "sensibilidad": sens_json,
        })

    except Exception as e:
        import traceback
        return jsonify({"error": True, "mensaje": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "TechClassUC v1.0"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(debug=False, port=port, host="0.0.0.0")
