from pathlib import Path
from typing import Any, Dict, Optional, Set

import yaml

from .modelo import Maquina, Transicion


class ErrorConfiguracion(ValueError):
    pass


class LectorYAML(yaml.SafeLoader):
    pass


def _mapa_sin_repetidos(lector, nodo, deep=False):
    lector.flatten_mapping(nodo)
    mapa = {}
    for nodo_clave, nodo_valor in nodo.value:
        clave = lector.construct_object(nodo_clave, deep=deep)
        try:
            repetida = clave in mapa
        except TypeError as exc:
            raise ErrorConfiguracion("Las claves del YAML deben ser valores simples.") from exc
        if repetida:
            linea = nodo_clave.start_mark.line + 1
            raise ErrorConfiguracion(f"Clave repetida {clave!r} en la línea {linea}.")
        mapa[clave] = lector.construct_object(nodo_valor, deep=deep)
    return mapa


LectorYAML.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapa_sin_repetidos
)


def _mapa(valor: Any, campos: Set[str], lugar: str) -> Dict[str, Any]:
    if not isinstance(valor, dict) or any(not isinstance(k, str) for k in valor):
        raise ErrorConfiguracion(f"{lugar}: se esperaba un objeto con claves de texto.")
    faltan = campos - valor.keys()
    sobran = valor.keys() - campos
    if faltan:
        raise ErrorConfiguracion(f"{lugar}: faltan campos: {', '.join(sorted(faltan))}.")
    if sobran:
        raise ErrorConfiguracion(f"{lugar}: campos desconocidos: {', '.join(sorted(sobran))}.")
    return valor


def _lista(valor: Any, lugar: str) -> list:
    if not isinstance(valor, list):
        raise ErrorConfiguracion(f"{lugar}: se esperaba una lista.")
    return valor


def _texto(valor: Any, lugar: str) -> str:
    if not isinstance(valor, str) or not valor:
        raise ErrorConfiguracion(f"{lugar}: se esperaba texto no vacío; usa comillas para números.")
    return valor


def _simbolo(valor: Any, lugar: str, permite_blanco: bool) -> Optional[str]:
    if valor is None and permite_blanco:
        return None
    if not isinstance(valor, str) or len(valor) != 1:
        detalle = "un carácter o null" if permite_blanco else "un carácter"
        raise ErrorConfiguracion(f"{lugar}: se esperaba {detalle}.")
    return valor


def _memoria(valor: Any, lugar: str) -> Optional[str]:
    if valor is None:
        return None
    return _texto(valor, lugar)


def _conjunto_simbolos(valor: Any, lugar: str, permite_blanco: bool) -> frozenset:
    elementos = [_simbolo(s, lugar, permite_blanco) for s in _lista(valor, lugar)]
    if len(set(elementos)) != len(elementos):
        raise ErrorConfiguracion(f"{lugar}: hay símbolos repetidos.")
    return frozenset(elementos)


def leer_maquina(ruta: Path) -> Maquina:
    try:
        contenido = Path(ruta).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ErrorConfiguracion(f"No se pudo leer {ruta}: {exc}") from exc
    try:
        datos = yaml.load(contenido, Loader=LectorYAML)
    except yaml.YAMLError as exc:
        marca = getattr(exc, "problem_mark", None)
        donde = f" en la línea {marca.line + 1}" if marca else ""
        raise ErrorConfiguracion(f"YAML inválido{donde}.") from exc
    return interpretar_maquina(datos)


def interpretar_maquina(datos: Any) -> Maquina:
    datos = _mapa(datos, {
        "q_states", "alphabet", "tape_alphabet", "delta", "simulation_strings"
    }, "configuración")
    q = _mapa(datos["q_states"], {"q_list", "initial", "final"}, "q_states")
    estados = [_texto(s, "q_states.q_list") for s in _lista(q["q_list"], "q_states.q_list")]
    if not estados or len(set(estados)) != len(estados):
        raise ErrorConfiguracion("q_states.q_list debe contener estados distintos y no estar vacía.")
    inicial = _texto(q["initial"], "q_states.initial")
    final = _texto(q["final"], "q_states.final")
    if inicial not in estados or final not in estados:
        raise ErrorConfiguracion("El estado inicial y el final deben pertenecer a q_states.q_list.")

    alfabeto = _conjunto_simbolos(datos["alphabet"], "alphabet", False)
    cinta = _conjunto_simbolos(datos["tape_alphabet"], "tape_alphabet", True)
    if not alfabeto <= cinta:
        raise ErrorConfiguracion("tape_alphabet debe contener todos los símbolos de alphabet.")
    if None not in cinta:
        raise ErrorConfiguracion("tape_alphabet debe incluir el blanco como null.")

    transiciones = {}
    movimientos = {"L": -1, "R": 1, "S": 0}
    for i, regla in enumerate(_lista(datos["delta"], "delta")):
        lugar = f"delta[{i}]"
        regla = _mapa(regla, {"params", "output"}, lugar)
        p = _mapa(regla["params"], {
            "initial_state", "mem_cache_value", "tape_input"
        }, f"{lugar}.params")
        o = _mapa(regla["output"], {
            "final_state", "mem_cache_value", "tape_output", "tape_displacement"
        }, f"{lugar}.output")
        origen = _texto(p["initial_state"], f"{lugar}.params.initial_state")
        destino = _texto(o["final_state"], f"{lugar}.output.final_state")
        if origen not in estados or destino not in estados:
            raise ErrorConfiguracion(f"{lugar}: la transición menciona un estado inexistente.")
        lee = _simbolo(p["tape_input"], f"{lugar}.params.tape_input", True)
        escribe = _simbolo(o["tape_output"], f"{lugar}.output.tape_output", True)
        if lee not in cinta or escribe not in cinta:
            raise ErrorConfiguracion(f"{lugar}: el símbolo leído o escrito no pertenece a tape_alphabet.")
        memoria_antes = _memoria(p["mem_cache_value"], f"{lugar}.params.mem_cache_value")
        memoria_despues = _memoria(o["mem_cache_value"], f"{lugar}.output.mem_cache_value")
        direccion = o["tape_displacement"]
        if not isinstance(direccion, str) or direccion not in movimientos:
            raise ErrorConfiguracion(f"{lugar}: tape_displacement debe ser L, R o S.")
        clave = (origen, memoria_antes, lee)
        if clave in transiciones:
            raise ErrorConfiguracion(f"{lugar}: hay más de una transición para {clave!r}.")
        transiciones[clave] = Transicion(destino, memoria_despues, escribe, movimientos[direccion])

    cadenas = _lista(datos["simulation_strings"], "simulation_strings")
    for i, cadena in enumerate(cadenas):
        if not isinstance(cadena, str):
            raise ErrorConfiguracion(f"simulation_strings[{i}]: se esperaba una cadena de texto.")
        if any(s not in alfabeto for s in cadena):
            raise ErrorConfiguracion(f"simulation_strings[{i}]: contiene símbolos fuera de alphabet.")
    return Maquina(frozenset(estados), inicial, final, alfabeto, cinta, transiciones, tuple(cadenas))

