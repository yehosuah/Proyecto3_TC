# Proyecto 3: simulador de máquinas de Turing

Yehosua Hercules y Miguel Rosas · Teoría de la Computación · Universidad del Valle de Guatemala.

El programa lee una máquina de Turing de una cinta desde un archivo YAML y ejecuta las cadenas incluidas en él. Por cada entrada muestra todas las descripciones instantáneas, la cinta final y el resultado. Las transiciones se obtienen del archivo; el motor es el mismo para las dos máquinas.

## Instalación y ejecución

Se necesita Python 3.9 o posterior y PyYAML 6.0.3. Desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py maquinas/reconocedora.yaml
python main.py maquinas/copiadora.yaml
```

En Windows, los dos primeros comandos son:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
```

Después de activar el entorno, los comandos que comienzan con `python` son iguales. También se puede usar directamente `.venv\Scripts\python.exe` en Windows o `.venv/bin/python` en macOS y Linux, sin activar el entorno.

Para guardar las trazas y reproducir los archivos de resultados incluidos:

```bash
python main.py maquinas/reconocedora.yaml --salida resultados/reconocedora.txt
python main.py maquinas/copiadora.yaml --salida resultados/copiadora.txt
```

Cada entrada tiene un límite predeterminado de 10,000 transiciones. Se puede cambiar:

```bash
python main.py maquinas/copiadora.yaml --max-pasos 20000
```

El límite debe ser un entero no negativo. Si se alcanza y todavía hay una transición aplicable, el resultado es `INTERRUMPIDA POR LÍMITE`. Esa interrupción no determina aceptación ni rechazo. Llegar al estado final o quedarse sin transición tiene prioridad sobre el límite.

La consola devuelve código 0 si todas las entradas terminaron, aceptadas o rechazadas; 3 si alguna quedó interrumpida por el límite; y 2 ante errores de archivo, configuración o argumentos. `--salida` reemplaza el archivo de resultados indicado y no permite sobrescribir el YAML de entrada.

## Configuración YAML

Cada archivo define una máquina y una lista de entradas. Los dos archivos de `maquinas/` sirven como ejemplos completos.

| Campo | Significado |
| --- | --- |
| `q_states.q_list` | Lista de estados, escritos como texto. |
| `q_states.initial` | Estado inicial. |
| `q_states.final` | Estado de aceptación; la máquina se detiene al alcanzarlo. |
| `alphabet` | Símbolos que pueden aparecer en las entradas. |
| `tape_alphabet` | Símbolos de cinta; incluye todo `alphabet` y el blanco. |
| `delta` | Lista de transiciones. |
| `simulation_strings` | Cadenas que se ejecutan, en el orden escrito. |

Cada símbolo de cinta ocupa un carácter. El blanco es `null`; también puede escribirse como un valor vacío de YAML. La cadena vacía se escribe `""`. Una `B` literal sigue siendo una letra y no representa un blanco.

Una transición de la reconocedora:

```yaml
- params: {initial_state: q0, mem_cache_value: null, tape_input: a}
  output: {final_state: q1, mem_cache_value: a, tape_output: null, tape_displacement: R}
```

Si el estado es `q0`, la memoria está en blanco y se lee `a`, la regla cambia al estado `q1`, guarda `a` en memoria, borra esa celda y mueve el cabezal a la derecha. Los desplazamientos son `L` (izquierda), `R` (derecha) y `S` (sin desplazamiento).

La memoria admite `null` o texto no vacío. Se compara exactamente con `params.mem_cache_value` y se reemplaza por `output.mem_cache_value`. En estas dos máquinas solo toma los valores `null`, `a` y `b`.

Usar comillas en estados numéricos, símbolos numéricos, `"#"` y valores que YAML podría interpretar como booleanos. Todas las cadenas de demostración están entre comillas. El lector comprueba los campos, las referencias a estados y alfabetos, y rechaza claves repetidas o más de una transición para la misma combinación de estado, memoria y símbolo leído. Una entrada con símbolos fuera de `alphabet` es un error de configuración.

## Cinta y descripciones instantáneas

La cinta se extiende en ambas direcciones. La entrada comienza en la posición 0 y el cabezal comienza sobre esa posición. Para una entrada vacía, allí se lee un blanco. El estado inicial viene del YAML y la memoria comienza en blanco. Cada entrada se simula desde una configuración nueva.

En las descripciones instantáneas, `□` representa un blanco y `[estado,memoria]` se inserta inmediatamente antes de la celda que lee el cabezal. Por ejemplo:

```text
0  □[q0,□]ab#ab□  cabezal=0
1  □[q1,a]b#ab□   cabezal=1
```

En la segunda descripción se borró la primera `a`, quedó guardada en memoria y el cabezal avanzó a la `b`. La ventana de impresión conserva las celdas no blancas, el cabezal y un blanco de margen a cada lado. La posición numérica permite seguir el cabezal aunque esa ventana cambie.

La traza contiene la configuración inicial y una configuración por cada transición. Por eso siempre hay una descripción más que transiciones ejecutadas. Los caracteres que puedan confundirse con la notación, como un `□` literal o un corchete, aparecen entre comillas.

## Estructura del programa

| Archivo | Responsabilidad |
| --- | --- |
| `main.py` | Argumentos de consola, ejecución de las entradas y exportación de resultados. |
| `turing/lector.py` | Lectura del YAML y comprobación de su estructura. |
| `turing/modelo.py` | Representaciones de la máquina, transiciones, configuraciones y resultados. |
| `turing/simulador.py` | Aplicación de una transición por paso y condiciones de parada. |
| `turing/salida.py` | Impresión de las descripciones instantáneas y de la cinta final. |
| `maquinas/` | Definiciones de las dos máquinas y sus ocho entradas de demostración. |
| `tests/` | Pruebas del lector, el motor, las máquinas y la consola. |
| `resultados/` | Trazas completas de las ocho ejecuciones. |

La cinta es un diccionario de posiciones enteras a símbolos. Las posiciones ausentes son blancas; escribir un blanco elimina esa posición del diccionario. Esto permite crecer hacia la izquierda y la derecha sin reservar una cinta de tamaño fijo.

Las transiciones se buscan con la clave `(estado, memoria, símbolo_leído)`. Cada configuración de la traza guarda una copia inmutable de las celdas no blancas. Así, una escritura posterior no modifica los pasos anteriores. Conservar todas las configuraciones consume memoria proporcional al tamaño de las cintas guardadas; para entradas grandes puede ser necesario ajustar el límite de pasos.

## Máquina reconocedora

Reconoce el lenguaje `{w#w | w ∈ {a,b}*}`. Las dos partes deben tener la misma longitud y los mismos símbolos en el mismo orden, con un único separador. `#` se acepta porque `w` puede ser vacía; la entrada vacía sin separador se rechaza.

La definición adapta la máquina M del Laboratorio 10. Tiene seis estados y veinte transiciones.

| Estado | Función |
| --- | --- |
| `q0` | Borrar y recordar el siguiente símbolo de la primera copia, o pasar a la revisión final al leer `#`. |
| `q1` | Llegar al separador conservando el símbolo recordado. |
| `q2` | Saltar las `X` y comparar con el siguiente símbolo de la segunda copia. |
| `q3` | Volver al blanco dejado en la primera copia y avanzar a su siguiente símbolo. |
| `q4` | Comprobar que después del separador solo queden `X`. |
| `q5` | Aceptar. |

Después de cada vuelta completa se ha borrado un símbolo de la primera parte y se ha marcado con `X` su pareja en la segunda. Solo se puede completar esa vuelta si ambos símbolos coinciden. Cuando se agota la primera parte, `q4` impide aceptar si sobra algún símbolo en la segunda. Una diferencia, un separador adicional o una copia incompleta dejan a la máquina sin transición y producen rechazo.

## Máquina copiadora

Calcula `f(w) = w#w`, para `w ∈ {a,b}*`. Conserva la entrada, inserta el separador y escribe una copia idéntica. Para la entrada vacía produce `#`. Tiene seis estados y veinticinco transiciones.

| Estado | Función |
| --- | --- |
| `q0` | Ir al final del original y escribir `#`. |
| `q1` | Regresar al inicio del original. |
| `q2` | Marcar con `X` el símbolo que toca copiar y guardarlo en memoria; aceptar si se llegó al separador. |
| `q3` | Llegar al primer blanco de la derecha y escribir el símbolo recordado. |
| `q4` | Regresar a la única `X`, restaurar su símbolo y avanzar una posición. |
| `q5` | Aceptar. |

Al comenzar cada vuelta, el original está restaurado y a la derecha del separador está la copia del prefijo ya procesado. La `X` señala la posición exacta a la que hay que regresar, y la memoria conserva el símbolo que se transporta. Cada vuelta añade un símbolo y avanza una posición en el original. Al llegar a `#` se han copiado todos los símbolos y ya no queda ninguna `X`.

Ambas máquinas realizan recorridos repetidos sobre una sola cinta. Para una palabra `w` de longitud `n`, sus ejecuciones aceptadas requieren tiempo del orden de `n²`. La dificultad de la copia está en conservar el original y la posición de trabajo mientras se escribe lejos del cabezal inicial.

## Casos de la demostración

Estos resultados se obtuvieron ejecutando los dos YAML con el simulador. Los archivos de `resultados/` contienen cada paso.

| Máquina | Entrada | Longitud | Resultado | Transiciones | Cinta final |
| --- | --- | ---: | --- | ---: | --- |
| Reconocedora | `ab#ab` | 5 | Aceptada | 18 | `#XX` |
| Reconocedora | `aab#aab` | 7 | Aceptada | 32 | `#XXX` |
| Reconocedora | `ab#ba` | 5 | Rechazada | 3 | `b#ba` |
| Reconocedora | `ab#aba` | 6 | Rechazada | 17 | `#XXa` |
| Copiadora | `abaab` | 5 | Aceptada | 78 | `abaab#abaab` |
| Copiadora | `bbaaba` | 6 | Aceptada | 105 | `bbaaba#bbaaba` |
| Copiadora | `aaaaa` | 5 | Aceptada | 78 | `aaaaa#aaaaa` |
| Copiadora | `bbbbb` | 5 | Aceptada | 78 | `bbbbb#bbbbb` |

La reconocedora modifica su cinta durante las comparaciones. Su aceptación se refiere a la entrada original. La copiadora, en cambio, debe dejar exactamente la transformación especificada.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Las 26 pruebas pasaron en Python 3.9.6. Incluyen:

- Las 29,524 cadenas de longitud 0 a 9 sobre `{a,b,#}`, comparando la decisión de la reconocedora con la igualdad de las dos partes y la presencia de un único separador.
- Las 511 cadenas de longitud 0 a 8 sobre `{a,b}`, comprobando la cinta completa de la copiadora y pasando cada salida a la reconocedora.
- Cadenas adicionales de longitud 10, 25 y 50 para la copia y el reconocimiento de su resultado.
- Los ocho casos del video, lectura de blancos, validación del YAML, movimientos `L`, `R` y `S`, memoria, reinicio entre entradas y conservación de las configuraciones anteriores.
- Aceptación y rechazo en el último paso permitido, interrupción de un bucle, exportación de trazas y errores de consola.

Las pruebas exhaustivas cubren los rangos indicados. La explicación de los recorridos anteriores establece por qué el procedimiento continúa funcionando al aumentar la longitud.

## Referencias

- Consigna del Proyecto No. 3 y máquina M del Laboratorio No. 10 de Teoría de la Computación, UVG.
- Pramod Ganapathi, [Turing Machines](https://www3.cs.stonybrook.edu/~pramod.ganapathi/doc/theory-of-computation/TuringMachines.pdf), páginas 23 a 27: copia de cadenas mediante recorridos y marcadores. Aquí el símbolo que se copia se conserva en `mem_cache_value`.
- [Documentación de PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation).
