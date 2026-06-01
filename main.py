"""
main.py
-------
Punto de entrada por consola para la simulación TechClassUC.
Ejecuta el modelo DES, Montecarlo, validación analítica,
análisis de sensibilidad y genera gráficas.
"""

import sys
import math
import argparse

from analitico import calcular_mmc, comparar_con_simulacion
from montecarlo import correr_replicas
from simulacion_des import correr_una_replica
from sensibilidad import analisis_sensibilidad, encontrar_c_optimo
from visualizacion import generar_todas_las_graficas


def main():
    parser = argparse.ArgumentParser(
        description="TechClassUC — Simulación M/M/c con SimPy y Montecarlo"
    )
    parser.add_argument("--lam", type=float, default=10.0, help="Tasa de llegada (clientes/hora)")
    parser.add_argument("--mu", type=float, default=4.0, help="Tasa de servicio (clientes/hora/técnico)")
    parser.add_argument("--c", type=int, default=3, help="Número de técnicos")
    parser.add_argument("--t-sim", type=float, default=480.0, help="Duración simulación (minutos)")
    parser.add_argument("--t-warm", type=float, default=60.0, help="Período de calentamiento (minutos)")
    parser.add_argument("--N", type=int, default=30, help="Número de réplicas Montecarlo")
    parser.add_argument("--semilla", type=int, default=42, help="Semilla base")
    parser.add_argument("--umbral-wq", type=float, default=10.0, help="Umbral Wq para c óptimo (minutos)")
    parser.add_argument("--prioridad", action="store_true", help="Usar cola con prioridad")
    parser.add_argument("--output-dir", type=str, default="graficas", help="Directorio para gráficas")
    parser.add_argument("--no-graficas", action="store_true", help="No generar gráficas")

    args = parser.parse_args()

    lam = args.lam
    mu = args.mu
    c = args.c
    t_sim = args.t_sim
    t_warm = args.t_warm
    N = args.N
    semilla_base = args.semilla
    umbral_wq = args.umbral_wq
    usar_prioridad = args.prioridad

    print("=" * 65)
    print("  TechClassUC — Simulación del Sistema de Atención al Cliente")
    print("  Modelo M/M/c con SimPy y Análisis de Montecarlo")
    print("=" * 65)

    rho = lam / (c * mu)
    print(f"\nParámetros:")
    print(f"  λ = {lam:.1f} clientes/hora")
    print(f"  μ = {mu:.1f} clientes/hora/técnico")
    print(f"  c = {c} técnicos")
    print(f"  ρ = {rho:.4f}" + ("  ✓ ESTABLE" if rho < 1 else "  ✗ INESTABLE"))

    if rho >= 1:
        c_min = math.ceil(lam / mu)
        print(f"\nERROR: Sistema inestable (ρ = {rho:.4f} ≥ 1).")
        print(f"Se necesita c ≥ {c_min} técnicos.")
        sys.exit(1)

    print(f"\n{'-' * 65}")
    print("1. RÉPLICA REPRESENTATIVA (estado transitorio)")
    print(f"{'-' * 65}")
    replica = correr_una_replica(
        lam=lam, mu=mu, c=c, t_sim=t_sim, t_warm=t_warm,
        semilla=semilla_base, usar_prioridad=usar_prioridad,
    )
    print(f"  Clientes atendidos: {replica['n_atendidos']}")
    if replica['wq_list']:
        import numpy as np
        print(f"  Wq promedio: {np.mean(replica['wq_list']):.4f} min")
    print(f"  Puntos de evolución temporal: {len(replica['evolucion_temporal'])}")

    print(f"\n{'-' * 65}")
    print("2. SIMULACIÓN DE MONTECARLO")
    print(f"{'-' * 65}")
    res_mc = correr_replicas(
        N=N, lam=lam, mu=mu, c=c,
        t_sim=t_sim, t_warm=t_warm,
        semilla_base=semilla_base,
        usar_prioridad=usar_prioridad,
        verbose=True,
    )

    print(f"\n{'-' * 65}")
    print("3. VALIDACIÓN ANALÍTICA (M/M/c)")
    print(f"{'-' * 65}")
    analitico = calcular_mmc(lam, mu, c)
    print(f"  ρ  = {analitico['rho']:.4f}")
    print(f"  P₀ = {analitico['P0']:.6f}")
    print(f"  Lq = {analitico['Lq']:.4f}")
    print(f"  Wq = {analitico['Wq']:.4f} min")
    print(f"  L  = {analitico['L']:.4f}")
    print(f"  W  = {analitico['W']:.4f} min")

    comparacion = comparar_con_simulacion(analitico, res_mc)
    print(f"\n  {'Métrica':<8} {'Analítico':<12} {'Simulado':<12} {'Error %':<10}")
    print(f"  {'-'*8} {'-'*12} {'-'*12} {'-'*10}")
    for nombre, vals in comparacion.items():
        print(f"  {nombre:<8} {vals['analitico']:<12.4f} {vals['simulado']:<12.4f} {vals['error_pct']:<10.2f}")

    print(f"\n{'-' * 65}")
    print("4. ANÁLISIS DE SENSIBILIDAD")
    print(f"{'-' * 65}")
    sens = analisis_sensibilidad(
        mu=mu, t_sim=t_sim, t_warm=t_warm,
        N_replicas=max(5, N // 2), semilla_base=semilla_base,
        usar_prioridad=usar_prioridad, verbose=True,
    )

    print(f"\n  Tabla de sensibilidad (c × λ):")
    print(f"  {'c':<4} {'λ':<8} {'ρ sim':<8} {'Wq (min)':<10} {'Lq':<8}")
    print(f"  {'-'*4} {'-'*8} {'-'*8} {'-'*10} {'-'*8}")
    for row in sens["tabla"]:
        rho_str = f"{row['rho']:.4f}" if row['rho'] is not None else "—"
        wq_str = f"{row['wq']:.3f}" if row['wq'] is not None else "—"
        lq_str = f"{row['lq']:.3f}" if row['lq'] is not None else "—"
        print(f"  {row['c']:<4} {row['lam']:<8.1f} {rho_str:<8} {wq_str:<10} {lq_str:<8}")

    print(f"\n  Búsqueda de c óptimo (Wq ≤ {umbral_wq} min)...")
    opt = encontrar_c_optimo(
        lam=lam, mu=mu, t_sim=t_sim, t_warm=t_warm,
        N_replicas=max(5, N // 2), semilla_base=semilla_base,
        umbral_wq=umbral_wq, usar_prioridad=usar_prioridad, verbose=True,
    )
    if opt["c_optimo"] is not None:
        print(f"  → RECOMENDACIÓN: c = {opt['c_optimo']} técnicos → Wq = {opt['wq_logrado']:.3f} min")
    else:
        print(f"  → No se encontró c óptimo")

    if not args.no_graficas:
        print(f"\n{'-' * 65}")
        print("5. GENERANDO GRÁFICAS")
        print(f"{'-' * 65}")
        paths = generar_todas_las_graficas(replica, res_mc, analitico, sens, lam, umbral_wq, args.output_dir)
        for nombre, path in paths.items():
            print(f"  ✓ {nombre}: {path}")

    print(f"\n{'=' * 65}")
    print("  SIMULACIÓN COMPLETADA EXITOSAMENTE")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
