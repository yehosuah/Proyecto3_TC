from .modelo import Configuracion, Maquina, Resultado


def simular(maquina: Maquina, cadena: str, max_pasos: int = 10000) -> Resultado:
    if not isinstance(cadena, str) or any(s not in maquina.alfabeto for s in cadena):
        raise ValueError("La entrada debe ser una cadena sobre el alfabeto de la máquina.")
    if type(max_pasos) is not int or max_pasos < 0:
        raise ValueError("El límite de pasos debe ser un entero no negativo.")

    # Las posiciones ausentes son blancas; los índices negativos extienden la cinta a la izquierda.
    cinta = dict(enumerate(cadena))
    estado, memoria, cabezal, paso = maquina.inicial, None, 0, 0
    traza = []
    while True:
        traza.append(Configuracion(paso, estado, memoria, cabezal, tuple(sorted(cinta.items()))))
        if estado == maquina.final:
            return Resultado(cadena, "aceptada", tuple(traza))

        regla = maquina.transiciones.get((estado, memoria, cinta.get(cabezal)))
        if regla is None:
            return Resultado(cadena, "rechazada", tuple(traza))
        # Una parada real tiene prioridad sobre el límite, incluso después del último paso permitido.
        if paso >= max_pasos:
            return Resultado(cadena, "limite", tuple(traza))

        if regla.escritura is None:
            cinta.pop(cabezal, None)
        else:
            cinta[cabezal] = regla.escritura
        estado, memoria = regla.estado, regla.memoria
        cabezal += regla.movimiento
        paso += 1

