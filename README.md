# TP Compiladores

Trabajo Práctico de **Diseño de Compiladores I – Compiladores e Intérpretes**.

## Descripción

Implementación de un analizador léxico y sintáctico para el lenguaje definido por la cátedra, utilizando **Python** y **SLY**.

El proyecto integra el analizador léxico desarrollado en el TP1 con el analizador sintáctico del TP2.

## Requisitos

* Python 3
* SLY 0.5

## Instalación

python3 -m pip install sly==0.5

## Ejecución

Activar el entorno virtual e iniciar el analizador indicando el archivo de entrada:

```
source venv/bin/activate
python3 analizador_sintactico.py prueba.txt
```


## Estructura

* `analizador_lexico.py` — Analizador léxico.
* `analizador_sintactico.py` — Analizador sintáctico.
* `tabla_simbolos.py`
* `prueba.txt` — Casos de prueba.
