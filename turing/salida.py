import json
from typing import Optional

from .modelo import Configuracion, Resultado


def simbolo(valor: Optional[str]) -> str:
    if valor is None:
        return "□"
    if any(not c.isprintable() or c.isspace() or c in '[]□,\\"' for c in valor):
        return json.dumps(valor, ensure_ascii=False)
    return valor


def descripcion(config: Configuracion) -> str:
    cinta = dict(config.cinta)
    posiciones = [config.cabezal, *cinta]
    izquierda, derecha = min(posiciones) - 1, max(posiciones) + 1
    partes = []
    for posicion in range(izquierda, derecha + 1):
        if posicion == config.cabezal:
            partes.append(f"[{simbolo(config.estado)},{simbolo(config.memoria)}]")
        partes.append(simbolo(cinta.get(posicion)))
    return "".join(partes)


def contenido(config: Configuracion) -> str:
    cinta = dict(config.cinta)
    if not cinta:
        return "□ (cinta vacía)"
    return "".join(simbolo(cinta.get(i)) for i in range(min(cinta), max(cinta) + 1))


def mostrar_resultado(resultado: Resultado) -> str:
    entrada = json.dumps(resultado.entrada, ensure_ascii=False)
    lineas = [f"Entrada: {entrada} (longitud {len(resultado.entrada)})", ""]
    ancho = len(str(resultado.pasos))
    for config in resultado.traza:
        lineas.append(f"{config.paso:>{ancho}}  {descripcion(config)}  cabezal={config.cabezal}")
    etiqueta = {
        "aceptada": "ACEPTADA",
        "rechazada": "RECHAZADA",
        "limite": "INTERRUMPIDA POR LÍMITE",
    }[resultado.estado]
    lineas.extend(["", f"Resultado: {etiqueta}", f"Pasos: {resultado.pasos}",
                   f"Cinta final: {contenido(resultado.final)}"])
    if resultado.estado == "rechazada":
        c = resultado.final
        lee = dict(c.cinta).get(c.cabezal)
        lineas.append(f"Sin transición para estado={simbolo(c.estado)}, "
                      f"memoria={simbolo(c.memoria)}, símbolo={simbolo(lee)}.")
    elif resultado.estado == "limite":
        lineas.append("Se alcanzó el límite de pasos; la aceptación o el rechazo no se han determinado.")
    return "\n".join(lineas)

