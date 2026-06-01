import random


class Cliente:
    _tipos = ("soporte", "mantenimiento", "reclamo")
    _prioridades = ("normal", "urgente")

    def __init__(self, id, tipo, prioridad, tiempo_llegada):
        self.id = id
        self.tipo = tipo if tipo in self._tipos else random.choice(self._tipos)
        self.prioridad = prioridad if prioridad in self._prioridades else "normal"
        self.tiempo_llegada = tiempo_llegada
        self.tiempo_inicio_atencion = None
        self.tiempo_fin_atencion = None

    @property
    def wq(self):
        if self.tiempo_inicio_atencion is None or self.tiempo_llegada is None:
            return None
        return self.tiempo_inicio_atencion - self.tiempo_llegada

    @property
    def ws(self):
        if self.tiempo_fin_atencion is None or self.tiempo_llegada is None:
            return None
        return self.tiempo_fin_atencion - self.tiempo_llegada

    def __repr__(self):
        return (f"Cliente(id={self.id}, tipo={self.tipo}, "
                f"prioridad={self.prioridad}, llegada={self.tiempo_llegada:.2f})")
