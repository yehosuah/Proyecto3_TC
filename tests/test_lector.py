from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from turing.lector import ErrorConfiguracion, interpretar_maquina, leer_maquina


def definicion():
    return {
        "q_states": {"q_list": ["q0", "qf"], "initial": "q0", "final": "qf"},
        "alphabet": ["a"],
        "tape_alphabet": ["a", None],
        "delta": [{
            "params": {"initial_state": "q0", "mem_cache_value": None, "tape_input": "a"},
            "output": {"final_state": "qf", "mem_cache_value": "a", "tape_output": "a",
                       "tape_displacement": "S"},
        }],
        "simulation_strings": ["a", ""],
    }


class PruebasLector(unittest.TestCase):
    def test_lee_el_contrato_del_pdf(self):
        m = interpretar_maquina(definicion())
        regla = m.transiciones[("q0", None, "a")]
        self.assertEqual((m.inicial, m.final, m.cadenas), ("q0", "qf", ("a", "")))
        self.assertEqual((regla.estado, regla.memoria, regla.movimiento), ("qf", "a", 0))

    def test_rechaza_configuraciones_inconsistentes(self):
        cambios = [
            (("q_states", "initial"), "otro"),
            (("q_states", "final"), "otro"),
            (("q_states", "q_list"), []),
            (("q_states", "q_list"), ["q0", "qf", "q0"]),
            (("q_states", "initial"), 0),
            (("alphabet",), [None]),
            (("alphabet",), ["ab"]),
            (("alphabet",), ["a", "a"]),
            (("tape_alphabet",), [None]),
            (("tape_alphabet",), ["a"]),
            (("delta",), {}),
            (("delta", 0, "params", "initial_state"), "otro"),
            (("delta", 0, "output", "final_state"), "otro"),
            (("delta", 0, "params", "tape_input"), "z"),
            (("delta", 0, "output", "tape_output"), "z"),
            (("delta", 0, "params", "mem_cache_value"), []),
            (("delta", 0, "output", "mem_cache_value"), False),
            (("delta", 0, "output", "tape_displacement"), "D"),
            (("delta", 0, "output", "tape_displacement"), []),
            (("simulation_strings",), [1]),
            (("simulation_strings",), ["b"]),
            (("simulation_strings",), "a"),
        ]
        for ruta, valor in cambios:
            with self.subTest(ruta=ruta, valor=valor):
                datos = definicion()
                destino = datos
                for campo in ruta[:-1]:
                    destino = destino[campo]
                destino[ruta[-1]] = valor
                with self.assertRaises(ErrorConfiguracion):
                    interpretar_maquina(datos)

    def test_campos_ausentes_y_desconocidos(self):
        for datos in [None, [], {}, {**definicion(), "alfabeto": ["a"]}]:
            with self.subTest(datos=datos), self.assertRaises(ErrorConfiguracion):
                interpretar_maquina(datos)
        datos = definicion()
        del datos["delta"][0]["params"]["mem_cache_value"]
        with self.assertRaisesRegex(ErrorConfiguracion, "mem_cache_value"):
            interpretar_maquina(datos)

    def test_transicion_repetida_o_ambigua(self):
        for cambiar in [False, True]:
            datos = definicion()
            segunda = deepcopy(datos["delta"][0])
            if cambiar:
                segunda["output"]["tape_output"] = None
            datos["delta"].append(segunda)
            with self.subTest(cambiar=cambiar), self.assertRaisesRegex(ErrorConfiguracion, "más de una"):
                interpretar_maquina(datos)

    def test_yaml_invalido_y_claves_repetidas(self):
        for texto in ["q_states: [", "alphabet: [a]\nalphabet: [b]\n", "---\na: b\n---\nc: d\n"]:
            with TemporaryDirectory() as tmp, self.subTest(texto=texto):
                ruta = Path(tmp) / "maquina.yaml"
                ruta.write_text(texto, encoding="utf-8")
                with self.assertRaises(ErrorConfiguracion):
                    leer_maquina(ruta)

    def test_los_valores_vacios_del_yaml_son_blancos(self):
        texto = """q_states:
  q_list: ['0', '1']
  initial: '0'
  final: '1'
alphabet: [a]
tape_alphabet:
  - a
  -
delta:
  - params: {initial_state: '0', mem_cache_value: , tape_input: }
    output: {final_state: '1', mem_cache_value: , tape_output: a, tape_displacement: S}
simulation_strings: ['']
"""
        with TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "blancos.yaml"
            ruta.write_text(texto, encoding="utf-8")
            m = leer_maquina(ruta)
        self.assertIn(("0", None, None), m.transiciones)
        self.assertIn(None, m.alfabeto_cinta)

    def test_error_de_archivo(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ErrorConfiguracion, "No se pudo leer"):
                leer_maquina(Path(tmp) / "ausente.yaml")


if __name__ == "__main__":
    unittest.main()

