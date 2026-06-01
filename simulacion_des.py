import simpy
import random
from cliente import Cliente


def correr_una_replica(lam, mu, c, t_sim, t_warm, semilla, usar_prioridad=False):
    random.seed(semilla)

    env = simpy.Environment()

    if usar_prioridad:
        recurso = simpy.PriorityResource(env, capacity=c)
    else:
        recurso = simpy.Resource(env, capacity=c)

    wq_list = []
    ws_list = []
    evolucion_temporal = []
    lq_records = []
    rho_records = []
    n_atendidos = 0

    _lam = lam / 60.0
    _mu = mu / 60.0

    def proceso_cliente(cliente):
        nonlocal n_atendidos
        if usar_prioridad:
            prioridad = 0 if cliente.prioridad == "urgente" else 1
            with recurso.request(priority=prioridad) as req:
                yield req
                cliente.tiempo_inicio_atencion = env.now
                yield env.timeout(random.expovariate(_mu))
                cliente.tiempo_fin_atencion = env.now
        else:
            with recurso.request() as req:
                yield req
                cliente.tiempo_inicio_atencion = env.now
                yield env.timeout(random.expovariate(_mu))
                cliente.tiempo_fin_atencion = env.now

        wq = cliente.wq
        ws = cliente.ws
        if env.now >= t_warm:
            wq_list.append(wq)
            ws_list.append(ws)
            n_atendidos += 1

    def generar_clientes(env):
        cliente_id = 0
        while True:
            t_entre = random.expovariate(_lam)
            yield env.timeout(t_entre)

            if env.now > t_sim:
                break

            cliente_id += 1
            tipo = random.choice(Cliente._tipos)
            prioridad = "urgente" if (usar_prioridad and random.random() < 0.2) else "normal"
            cliente = Cliente(
                id=cliente_id,
                tipo=tipo,
                prioridad=prioridad,
                tiempo_llegada=env.now,
            )
            env.process(proceso_cliente(cliente))

    def monitorear(env):
        while True:
            n_sistema = recurso.count + len(recurso.queue)
            evolucion_temporal.append((env.now, n_sistema))
            lq_records.append((env.now, len(recurso.queue)))
            rho_records.append((env.now, recurso.count / c))
            yield env.timeout(0.5)

    env.process(monitorear(env))
    env.process(generar_clientes(env))
    env.run(until=t_sim)

    lq_promedio = _promedio_temporal(lq_records, t_warm)
    rho_promedio = _promedio_temporal(rho_records, t_warm)

    return {
        "wq_list": wq_list,
        "ws_list": ws_list,
        "lq_promedio": lq_promedio,
        "rho_promedio": rho_promedio,
        "evolucion_temporal": evolucion_temporal,
        "lq_records": lq_records,
        "rho_records": rho_records,
        "n_atendidos": n_atendidos,
    }


def _promedio_temporal(records, t_warm):
    records_filtrados = [(t, v) for t, v in records if t >= t_warm]
    if not records_filtrados:
        return 0.0
    suma = 0.0
    for i in range(len(records_filtrados) - 1):
        t_actual, v_actual = records_filtrados[i]
        t_sig = records_filtrados[i + 1][0]
        suma += v_actual * (t_sig - t_actual)
    return suma / (records_filtrados[-1][0] - records_filtrados[0][0])
