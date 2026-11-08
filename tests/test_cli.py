from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


RAIZ = Path(__file__).resolve().parents[1]


def ejecutar(*argumentos):
    return subprocess.run([sys.executable, "-B", str(RAIZ / "main.py"), *map(str, argumentos)],
                          cwd=RAIZ, capture_output=True, encoding="utf-8")


class PruebasConsola(unittest.TestCase):
    def test_ejecuta_el_lote_y_guarda_la_misma_salida(self):
        with TemporaryDirectory() as tmp:
            salida = Path(tmp) / "trazas" / "reconocedora.txt"
            r = ejecutar("maquinas/reconocedora.yaml", "--salida", salida)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.count("Resultado: ACEPTADA"), 2)
            self.assertEqual(r.stdout.count("Resultado: RECHAZADA"), 2)
            self.assertEqual(salida.read_text(encoding="utf-8"), r.stdout)

    def test_la_salida_no_puede_sobrescribir_el_yaml(self):
        with TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "maquina.yaml"
            original = (RAIZ / "maquinas/reconocedora.yaml").read_bytes()
            ruta.write_bytes(original)
            r = ejecutar(ruta, "--salida", ruta)
            self.assertEqual(r.returncode, 2)
            self.assertEqual(ruta.read_bytes(), original)
            self.assertIn("no puede reemplazar", r.stderr)

    def test_error_de_archivo_sin_traza_de_python(self):
        with TemporaryDirectory() as tmp:
            r = ejecutar(Path(tmp) / "ausente.yaml")
            self.assertEqual(r.returncode, 2)
            self.assertIn("Error:", r.stderr)
            self.assertNotIn("Traceback", r.stderr)

    def test_limite_y_codigo_de_salida(self):
        r = ejecutar("maquinas/copiadora.yaml", "--max-pasos", "1")
        self.assertEqual(r.returncode, 3)
        self.assertEqual(r.stdout.count("Resultado: INTERRUMPIDA POR LÍMITE"), 4)
        self.assertNotIn("Resultado: RECHAZADA", r.stdout)

    def test_argumentos_invalidos(self):
        for limite in ["-1", "abc"]:
            with self.subTest(limite=limite):
                r = ejecutar("maquinas/copiadora.yaml", "--max-pasos", limite)
                self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()

