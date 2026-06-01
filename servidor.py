import simpy


class ServidorTracker:
    def __init__(self, env, c, capacidad_individual=1):
        self.env = env
        self.c = c
        self.recurso = simpy.Resource(env, capacity=c)
        self.clientes_atendidos = 0
        self.tiempo_acumulado = 0.0
        self._ultimo_cambio = 0.0

    @property
    def ocupados(self):
        return self.recurso.count

    @property
    def en_cola(self):
        return len(self.recurso.queue)

    @property
    def utilizacion_instantanea(self):
        return self.ocupados / self.c if self.c > 0 else 0.0
