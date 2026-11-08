from itertools import product
from pathlib import Path
import unittest

from turing.lector import leer_maquina
from turing.simulador import simular


RAIZ = Path(__file__).resolve().parents[1]


class PruebasMaquinas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reconocedora = leer_maquina(RAIZ / "maquinas/reconocedora.yaml")
        cls.copiadora = leer_maquina(RAIZ / "maquinas/copiadora.yaml")

    def test_los_ocho_casos_del_video(self):
        self.assertEqual(self.reconocedora.cadenas, ("ab#ab", "aab#aab", "ab#ba", "ab#aba"))
        self.assertEqual(self.copiadora.cadenas, ("abaab", "bbaaba", "aaaaa", "bbbbb"))
        for cadena, estado in zip(self.reconocedora.cadenas,
                                   ["aceptada", "aceptada", "rechazada", "rechazada"]):
            with self.subTest(cadena=cadena):
                self.assertGreaterEqual(len(cadena), 5)
                self.assertEqual(simular(self.reconocedora, cadena).estado, estado)
        for cadena in self.copiadora.cadenas:
            with self.subTest(cadena=cadena):
                self.assertGreaterEqual(len(cadena), 5)
                self.comprobar_copia(cadena)

    def test_reconocedora_exhaustiva_hasta_longitud_9(self):
        cantidad = 0
        for n in range(10):
            for letras in product("ab#", repeat=n):
                cadena = "".join(letras)
                partes = cadena.split("#")
                acepta = len(partes) == 2 and partes[0] == partes[1]
                r = simular(self.reconocedora, cadena)
                self.assertEqual(r.estado, "aceptada" if acepta else "rechazada", cadena)
                self.assertEqual(len(r.traza), r.pasos + 1)
                cantidad += 1
        self.assertEqual(cantidad, 29524)

    def comprobar_copia(self, cadena):
        r = simular(self.copiadora, cadena)
        esperada = cadena + "#" + cadena
        self.assertEqual(r.estado, "aceptada", cadena)
        self.assertEqual(dict(r.final.cinta), dict(enumerate(esperada)), cadena)
        self.assertEqual(len(r.traza), r.pasos + 1)
        self.assertEqual(simular(self.reconocedora, esperada).estado, "aceptada", cadena)

    def test_copiadora_exhaustiva_y_composicion_hasta_longitud_8(self):
        cantidad = 0
        for n in range(9):
            for letras in product("ab", repeat=n):
                self.comprobar_copia("".join(letras))
                cantidad += 1
        self.assertEqual(cantidad, 511)

    def test_entradas_mas_largas(self):
        for n in [10, 25, 50]:
            cadena = ("abba" * n)[:n]
            with self.subTest(n=n):
                self.comprobar_copia(cadena)

    def test_casos_vacios_y_separadores(self):
        for cadena in ["", "##", "a#", "#a", "ab##ab", "aba"]:
            with self.subTest(cadena=cadena):
                self.assertEqual(simular(self.reconocedora, cadena).estado, "rechazada")
        self.assertEqual(simular(self.reconocedora, "#").estado, "aceptada")
        self.comprobar_copia("")


if __name__ == "__main__":
    unittest.main()

