# TP Compiladores

Trabajo Práctico de **Diseño de Compiladores I – Compiladores e Intérpretes**.

## Descripción

Implementación de un analizador léxico y sintáctico para el lenguaje definido por la cátedra, utilizando **Python** y **SLY**.

El proyecto integra el analizador léxico desarrollado en el TP1 con el analizador sintáctico del TP2.

## Requisitos

* Python 3
* SLY

## Ejecución

Activar el entorno virtual e iniciar el analizador indicando el archivo de entrada:

```bash
source venv/bin/activate
python3 main.py archivo.txt
```

Las dependencias pueden instalarse mediante:

```bash
pip install -r requirements.txt
```

## Estructura

* `lexer.py` — Analizador léxico.
* `parser.py` — Analizador sintáctico.
* `main.py` — Punto de entrada del programa.
* `requirements.txt` — Dependencias del proyecto.
* (Otros archivos)`.txt` — Casos de prueba.
