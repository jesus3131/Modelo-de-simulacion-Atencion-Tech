import math


def calcular_mmc(lam, mu, c):
    _lam = lam / 60.0
    _mu = mu / 60.0
    rho = _lam / (c * _mu)
    if rho >= 1:
        return {
            "rho": rho,
            "P0": 0.0,
            "Lq": float("inf"),
            "Wq": float("inf"),
            "L": float("inf"),
            "W": float("inf"),
            "estable": False,
        }

    suma = 0.0
    for n in range(c):
        suma += (_lam / _mu) ** n / math.factorial(n)
    term = (_lam / _mu) ** c / (math.factorial(c) * (1 - rho))
    P0 = 1.0 / (suma + term)

    Lq = P0 * (_lam / _mu) ** c * rho / (math.factorial(c) * (1 - rho) ** 2)
    Wq = Lq / _lam
    W = Wq + 1.0 / _mu
    L = Lq + _lam / _mu

    return {
        "rho": rho,
        "P0": P0,
        "Lq": Lq,
        "Wq": Wq,
        "L": L,
        "W": W,
        "estable": True,
    }


def comparar_con_simulacion(analitico, res_mc):
    metricas = {
        "Wq": (analitico["Wq"], res_mc["wq_media"]),
        "Lq": (analitico["Lq"], res_mc["lq_media"]),
        "W": (analitico["W"], res_mc["ws_media"]),
        "rho": (analitico["rho"], res_mc["rho_media"]),
    }

    comparacion = {}
    for nombre, (analitico_val, simulado_val) in metricas.items():
        if analitico_val == 0:
            error_pct = 0.0
        elif analitico_val == float("inf"):
            error_pct = float("inf")
        else:
            error_pct = abs(simulado_val - analitico_val) / analitico_val * 100

        comparacion[nombre] = {
            "analitico": analitico_val,
            "simulado": simulado_val,
            "error_pct": error_pct,
        }

    return comparacion
