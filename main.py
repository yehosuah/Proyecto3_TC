import argparse
from pathlib import Path
import sys

from turing.lector import ErrorConfiguracion, leer_maquina
from turing.simulador import simular
from turing.salida import mostrar_resultado


def entero_no_negativo(texto: str) -> int:
    try:
        valor = int(texto)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Se esperaba un número entero.") from exc
    if valor < 0:
        raise argparse.ArgumentTypeError("El límite no puede ser negativo.")
    return valor


def main() -> int:
    parser = argparse.ArgumentParser(description="Simula una máquina de Turing de una cinta definida en YAML.")
    parser.add_argument("archivo", type=Path, help="Archivo YAML de la máquina y sus entradas.")
    parser.add_argument("--max-pasos", type=entero_no_negativo, default=10000,
                        help="Máximo de transiciones por entrada (por defecto: 10000).")
    parser.add_argument("--salida", type=Path, help="Guarda también las trazas completas en un archivo de texto.")
    args = parser.parse_args()
    try:
        maquina = leer_maquina(args.archivo)
        if args.salida is not None:
            mismo_archivo = args.salida.resolve() == args.archivo.resolve()
            if args.salida.exists():
                mismo_archivo = mismo_archivo or args.salida.samefile(args.archivo)
            if mismo_archivo:
                raise ValueError("El archivo de salida no puede reemplazar el YAML de entrada.")

        resultados = [simular(maquina, cadena, args.max_pasos) for cadena in maquina.cadenas]
        texto = "\n\n".join(mostrar_resultado(r) for r in resultados)
        if not resultados:
            texto = "El archivo no contiene cadenas para simular."
        texto += "\n"
        if args.salida is not None:
            args.salida.parent.mkdir(parents=True, exist_ok=True)
            args.salida.write_text(texto, encoding="utf-8")
        sys.stdout.write(texto)
        return 3 if any(r.estado == "limite" for r in resultados) else 0
    except (ErrorConfiguracion, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

