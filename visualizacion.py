import os
import numpy as np
import matplotlib.pyplot as plt


def grafica_evolucion_temporal(evolucion, t_warm, output_dir="graficas"):
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
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "evolucion_temporal.png")
    fig.savefig(path, bbox_inches="tight", dpi=120)
    plt.close(fig)
    return path


def grafica_histograma_wq(wq_todos, wq_media, wq_ic95, output_dir="graficas"):
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
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "histograma_wq.png")
    fig.savefig(path, bbox_inches="tight", dpi=120)
    plt.close(fig)
    return path


def grafica_wq_vs_c(sens, lam_base, umbral_wq, output_dir="graficas"):
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
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "wq_vs_c.png")
    fig.savefig(path, bbox_inches="tight", dpi=120)
    plt.close(fig)
    return path


def grafica_rho_vs_lam(sens, output_dir="graficas"):
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
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "rho_vs_lam.png")
    fig.savefig(path, bbox_inches="tight", dpi=120)
    plt.close(fig)
    return path


def grafica_distribucion_medias_wq(wq_medias, output_dir="graficas"):
    from scipy import stats
    arr = np.array(wq_medias)
    media = float(np.mean(arr))
    std = float(np.std(arr, ddof=1))
    fig, ax = plt.subplots(figsize=(8, 5))
    n_bins = max(8, len(arr) // 5)
    ax.hist(arr, bins=n_bins, color="#10B981", edgecolor="white", alpha=0.75, density=True, label="Medias réplicas")
    x = np.linspace(max(0, arr.min() - std), arr.max() + std, 300)
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
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "distribucion_medias_wq.png")
    fig.savefig(path, bbox_inches="tight", dpi=120)
    plt.close(fig)
    return path


def grafica_heatmap_wq(sens, output_dir="graficas"):
    lista_c = sens["lista_c"]
    lista_lam = sens["lista_lam"]
    matrix = sens["heatmap_wq"]
    fig, ax = plt.subplots(figsize=(9, 6))
    valid = matrix[~np.isnan(matrix)]
    vmax = np.nanpercentile(valid, 95) if len(valid) > 0 else 1
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd",
                   vmin=np.nanmin(matrix) if len(valid) > 0 else 0, vmax=vmax)
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
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "heatmap_wq.png")
    fig.savefig(path, bbox_inches="tight", dpi=120)
    plt.close(fig)
    return path


def grafica_heatmap_rho(sens, output_dir="graficas"):
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
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "heatmap_rho.png")
    fig.savefig(path, bbox_inches="tight", dpi=120)
    plt.close(fig)
    return path


def generar_todas_las_graficas(replica, res_mc, analitico, sens, lam, umbral_wq, output_dir="graficas"):
    paths = {}
    paths["evolucion"] = grafica_evolucion_temporal(replica["evolucion_temporal"], 60, output_dir)
    paths["histograma"] = grafica_histograma_wq(res_mc["wq_todas"], res_mc["wq_media"], res_mc["wq_ic95"], output_dir)
    paths["wq_vs_c"] = grafica_wq_vs_c(sens, lam, umbral_wq, output_dir)
    paths["rho_vs_lam"] = grafica_rho_vs_lam(sens, output_dir)
    paths["tcl"] = grafica_distribucion_medias_wq(res_mc["wq_medias_replicas"], output_dir)
    paths["heatmap_wq"] = grafica_heatmap_wq(sens, output_dir)
    paths["heatmap_rho"] = grafica_heatmap_rho(sens, output_dir)
    return paths
