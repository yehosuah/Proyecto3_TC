from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional, Tuple


Simbolo = Optional[str]
Clave = Tuple[str, Simbolo, Simbolo]


@dataclass(frozen=True)
class Transicion:
    estado: str
    memoria: Simbolo
    escritura: Simbolo
    movimiento: int


@dataclass(frozen=True)
class Maquina:
    estados: FrozenSet[str]
    inicial: str
    final: str
    alfabeto: FrozenSet[str]
    alfabeto_cinta: FrozenSet[Simbolo]
    transiciones: Dict[Clave, Transicion]
    cadenas: Tuple[str, ...]


@dataclass(frozen=True)
class Configuracion:
    paso: int
    estado: str
    memoria: Simbolo
    cabezal: int
    # Una tupla conserva la cinta de este paso aunque la simulación continúe.
    cinta: Tuple[Tuple[int, str], ...]


@dataclass(frozen=True)
class Resultado:
    entrada: str
    estado: str
    traza: Tuple[Configuracion, ...]

    @property
    def final(self) -> Configuracion:
        return self.traza[-1]

    @property
    def pasos(self) -> int:
        return self.final.paso

