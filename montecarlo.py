import math
import numpy as np
from simulacion_des import correr_una_replica


def correr_replicas(N, lam, mu, c, t_sim, t_warm, semilla_base, usar_prioridad=False, verbose=True):
    if verbose:
        print(f"Ejecutando {N} réplicas de Montecarlo...")

    wq_por_replica = []
    ws_por_replica = []
    lq_por_replica = []
    rho_por_replica = []
    wq_todas = []
    ws_todas = []

    for i in range(N):
        semilla = semilla_base + i
        res = correr_una_replica(
            lam=lam, mu=mu, c=c,
            t_sim=t_sim, t_warm=t_warm,
            semilla=semilla, usar_prioridad=usar_prioridad,
        )

        if res["wq_list"]:
            media_wq = float(np.mean(res["wq_list"]))
            media_ws = float(np.mean(res["ws_list"]))
        else:
            media_wq = 0.0
            media_ws = 0.0

        wq_por_replica.append(media_wq)
        ws_por_replica.append(media_ws)
        lq_por_replica.append(res["lq_promedio"])
        rho_por_replica.append(res["rho_promedio"])
        wq_todas.extend(res["wq_list"])
        ws_todas.extend(res["ws_list"])

        if verbose and (i + 1) % max(1, N // 5) == 0:
            print(f"  Réplica {i + 1}/{N} completada — Wq={media_wq:.3f} min")

    arr_wq = np.array(wq_por_replica)
    arr_ws = np.array(ws_por_replica)
    arr_lq = np.array(lq_por_replica)
    arr_rho = np.array(rho_por_replica)

    wq_media = float(np.mean(arr_wq))
    wq_std = float(np.std(arr_wq, ddof=1))
    ws_media = float(np.mean(arr_ws))
    ws_std = float(np.std(arr_ws, ddof=1))
    lq_media = float(np.mean(arr_lq))
    rho_media = float(np.mean(arr_rho))

    wq_ic95 = _intervalo_confianza(wq_media, wq_std, N)
    ws_ic95 = _intervalo_confianza(ws_media, ws_std, N)
    lq_ic95 = _intervalo_confianza(lq_media, float(np.std(arr_lq, ddof=1)), N)
    rho_ic95 = _intervalo_confianza(rho_media, float(np.std(arr_rho, ddof=1)), N)

    n_minimo = _n_minimo_replicas(wq_std, wq_media, 0.05)

    if verbose:
        print(f"\nResultados Montecarlo ({N} réplicas):")
        print(f"  Wq = {wq_media:.4f} min  IC95% = [{wq_ic95[0]:.4f}, {wq_ic95[1]:.4f}]")
        print(f"  Ws = {ws_media:.4f} min  IC95% = [{ws_ic95[0]:.4f}, {ws_ic95[1]:.4f}]")
        print(f"  Lq = {lq_media:.4f}")
        print(f"  ρ  = {rho_media:.4f}")
        print(f"  N mínimo para ε≤5% = {n_minimo}")

    return {
        "wq_media": wq_media,
        "wq_std": wq_std,
        "wq_ic95": wq_ic95,
        "ws_media": ws_media,
        "ws_std": ws_std,
        "ws_ic95": ws_ic95,
        "lq_media": lq_media,
        "lq_ic95": lq_ic95,
        "rho_media": rho_media,
        "rho_ic95": rho_ic95,
        "wq_todas": wq_todas,
        "ws_todas": ws_todas,
        "wq_medias_replicas": wq_por_replica,
        "ws_medias_replicas": ws_por_replica,
        "n_minimo_replicas": n_minimo,
        "N": N,
    }


def _intervalo_confianza(media, std, n, alpha=0.05):
    if n < 2 or std == 0:
        return (media, media)
    z = 1.96
    margen = z * std / math.sqrt(n)
    return (media - margen, media + margen)


def _n_minimo_replicas(std, media, error_relativo):
    if media == 0 or std == 0:
        return 2
    z = 1.96
    n_est = (z * std / (error_relativo * media)) ** 2
    return max(2, math.ceil(n_est))
