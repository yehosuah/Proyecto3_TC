from dataclasses import replace
import unittest

from turing.modelo import Configuracion, Maquina, Transicion
from turing.simulador import simular
from turing.salida import descripcion, mostrar_resultado, simbolo


def maquina(reglas, inicial="q0", final="qf"):
    return Maquina(frozenset(["q0", "q1", "q2", "q3", "qf"]), inicial, final,
                   frozenset("abB"), frozenset(["a", "b", "B", None]), reglas, ())


class PruebasSimulador(unittest.TestCase):
    def test_escritura_borrado_movimientos_y_cinta_izquierda(self):
        m = maquina({
            ("q0", None, None): Transicion("q1", "a", "a", -1),
            ("q1", "a", None): Transicion("q2", None, "b", 0),
            ("q2", None, "b"): Transicion("q3", None, None, 1),
            ("q3", None, "a"): Transicion("qf", None, "a", 0),
        })
        r = simular(m, "")
        esperada = [
            ("q0", None, 0, ()),
            ("q1", "a", -1, ((0, "a"),)),
            ("q2", None, -1, ((-1, "b"), (0, "a"))),
            ("q3", None, 0, ((0, "a"),)),
            ("qf", None, 0, ((0, "a"),)),
        ]
        self.assertEqual(r.estado, "aceptada")
        self.assertEqual([(c.estado, c.memoria, c.cabezal, c.cinta) for c in r.traza], esperada)
        self.assertEqual([c.paso for c in r.traza], list(range(5)))

    def test_la_memoria_decide_la_transicion(self):
        m = maquina({
            ("q0", None, "a"): Transicion("q0", "a", "a", 0),
            ("q0", "a", "a"): Transicion("qf", None, "b", 0),
        })
        r = simular(m, "a")
        self.assertEqual((r.estado, r.pasos, r.final.cinta), ("aceptada", 2, ((0, "b"),)))

    def test_blanco_y_letra_b_mayuscula_son_distintos(self):
        m = maquina({("q0", None, "B"): Transicion("qf", None, "B", 0)})
        self.assertEqual(simular(m, "B").estado, "aceptada")
        self.assertEqual(simular(m, "").estado, "rechazada")

    def test_aceptacion_inicial_y_falta_de_transicion(self):
        self.assertEqual(simular(maquina({}, inicial="qf"), "", 0).estado, "aceptada")
        r = simular(maquina({}), "a", 0)
        self.assertEqual((r.estado, r.pasos, len(r.traza)), ("rechazada", 0, 1))

    def test_aceptacion_y_rechazo_en_el_ultimo_paso_permitido(self):
        for siguiente, esperado in [("qf", "aceptada"), ("q1", "rechazada")]:
            m = maquina({("q0", None, "a"): Transicion(siguiente, None, "a", 0)})
            with self.subTest(siguiente=siguiente):
                self.assertEqual(simular(m, "a", 1).estado, esperado)

    def test_un_bucle_se_interrumpe_sin_declarar_rechazo(self):
        m = maquina({("q0", None, "a"): Transicion("q0", None, "a", 0)})
        for limite in [0, 1, 7]:
            with self.subTest(limite=limite):
                r = simular(m, "a", limite)
                self.assertEqual((r.estado, r.pasos, len(r.traza)), ("limite", limite, limite + 1))
                texto = mostrar_resultado(r)
                self.assertIn("INTERRUMPIDA POR LÍMITE", texto)
                self.assertNotIn("Resultado: RECHAZADA", texto)

    def test_cada_entrada_comienza_de_nuevo(self):
        m = maquina({("q0", None, "a"): Transicion("qf", "b", "b", 1)})
        primero = simular(m, "a")
        segundo = simular(m, "a")
        tercero = simular(m, "")
        self.assertEqual(primero, segundo)
        self.assertEqual(primero.traza[0].cinta, ((0, "a"),))
        self.assertEqual(tercero.traza[0], Configuracion(0, "q0", None, 0, ()))

    def test_entradas_y_limites_invalidos(self):
        for entrada in ["z", None]:
            with self.subTest(entrada=entrada), self.assertRaises(ValueError):
                simular(maquina({}), entrada)
        for limite in [-1, 1.5, True, "10"]:
            with self.subTest(limite=limite), self.assertRaises(ValueError):
                simular(maquina({}), "", limite)

    def test_descripcion_coloca_el_estado_antes_de_la_celda_leida(self):
        c = Configuracion(0, "q0", None, 0, ((0, "a"), (1, "b")))
        self.assertEqual(descripcion(c), "□[q0,□]ab□")
        self.assertIn("a[q1,a]b", descripcion(replace(c, estado="q1", memoria="a", cabezal=1)))
        self.assertEqual(simbolo(None), "□")
        self.assertEqual(simbolo("□"), '"□"')
        self.assertEqual(simbolo("B"), "B")


if __name__ == "__main__":
    unittest.main()

