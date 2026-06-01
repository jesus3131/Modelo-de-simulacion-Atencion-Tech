import math
import numpy as np
from montecarlo import correr_replicas


def analisis_sensibilidad(mu, t_sim, t_warm, N_replicas, semilla_base,
                           lista_c=None, lista_lam=None, usar_prioridad=False, verbose=True):
    if lista_c is None:
        lista_c = [1, 2, 3, 4, 5, 6]
    if lista_lam is None:
        lista_lam = [6.0, 8.0, 10.0, 12.0, 14.0, 16.0]

    if verbose:
        print(f"\nAnálisis de sensibilidad:")
        print(f"  c = {lista_c}")
        print(f"  λ = {lista_lam}")
        print(f"  Réplicas por combo: {N_replicas}")

    heatmap_wq = np.full((len(lista_lam), len(lista_c)), np.nan)
    heatmap_rho = np.full((len(lista_lam), len(lista_c)), np.nan)
    curva_rho_vs_lam = {}
    tabla = []

    for j, c_val in enumerate(lista_c):
        curva_rho_vs_lam[c_val] = []
        for i, lam_val in enumerate(lista_lam):
            rho_teorico = lam_val / (c_val * mu)

            if rho_teorico >= 1:
                wq_combo = None
                rho_combo = None
                lq_combo = None
                if verbose:
                    print(f"  (c={c_val}, λ={lam_val}) — ρ={rho_teorico:.3f} — INESTABLE (omitido)")
            else:
                res = correr_replicas(
                    N=N_replicas, lam=lam_val, mu=mu, c=c_val,
                    t_sim=t_sim, t_warm=t_warm,
                    semilla_base=semilla_base + (i + j * len(lista_lam)),
                    usar_prioridad=usar_prioridad, verbose=False,
                )
                wq_combo = res["wq_media"]
                rho_combo = res["rho_media"]
                lq_combo = res["lq_media"]
                if verbose:
                    print(f"  (c={c_val}, λ={lam_val}) — ρ={rho_combo:.3f}, Wq={wq_combo:.3f} min")

            heatmap_wq[i, j] = wq_combo if wq_combo is not None else np.nan
            heatmap_rho[i, j] = rho_combo if rho_combo is not None else np.nan
            curva_rho_vs_lam[c_val].append(rho_combo if rho_combo is not None else None)

            tabla.append({
                "c": c_val,
                "lam": lam_val,
                "rho": rho_combo,
                "wq": wq_combo,
                "lq": lq_combo,
            })

    return {
        "tabla": tabla,
        "lista_c": lista_c,
        "lista_lam": lista_lam,
        "heatmap_wq": heatmap_wq,
        "heatmap_rho": heatmap_rho,
        "curva_rho_vs_lam": curva_rho_vs_lam,
    }


def encontrar_c_optimo(lam, mu, t_sim, t_warm, N_replicas, semilla_base,
                        umbral_wq=10.0, usar_prioridad=False, max_servidores=20, verbose=True):
    if verbose:
        print(f"\nBuscando c óptimo (Wq ≤ {umbral_wq} min)...")

    for c in range(1, max_servidores + 1):
        rho = lam / (c * mu)
        if rho >= 1:
            continue

        res = correr_replicas(
            N=N_replicas, lam=lam, mu=mu, c=c,
            t_sim=t_sim, t_warm=t_warm,
            semilla_base=semilla_base + c,
            usar_prioridad=usar_prioridad, verbose=False,
        )

        wq = res["wq_media"]
        if verbose:
            print(f"  c={c}: Wq={wq:.3f} min")

        if wq <= umbral_wq:
            if verbose:
                print(f"  → c óptimo = {c} técnicos (Wq={wq:.3f} min ≤ {umbral_wq} min)")
            return {"c_optimo": c, "wq_logrado": wq}

    if verbose:
        print(f"  No se encontró c óptimo en {max_servidores} servidores")
    return {"c_optimo": None, "wq_logrado": None}
