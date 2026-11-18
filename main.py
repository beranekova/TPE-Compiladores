import sys
import os
import argparse
from wasmtime import Engine, Store, Module, Instance, Func, FuncType, ValType, Limits, Memory, MemoryType

from analizador_lexico import analizador_lexico
from analizador_sintactico import analizador_sintactico
from generador_assembler import generador_assembler

def ejecutar_modulo_wasm(ruta_wat: str, ruta_wasm: str):
    engine = Engine()
    store = Store(engine)

    modulo = Module.from_file(engine, ruta_wat)
    with open(ruta_wasm, "wb") as f_bin:
        f_bin.write(modulo.serialize())

    memoria = Memory(store, MemoryType(Limits(1, None)))

    def log_str(offset: int, length: int):
        datos = memoria.read(store, offset, offset + length)
        print(datos.decode("utf-8"))

    def log_i32(val: int):
        print(val)

    def log_f64(val: float):
        print(val)

    func_log     = Func(store, FuncType([ValType.i32(), ValType.i32()], []), log_str)
    func_log_i32 = Func(store, FuncType([ValType.i32()], []), log_i32)
    func_log_f64 = Func(store, FuncType([ValType.f64()], []), log_f64)

    instancia = Instance(store, modulo, [func_log, func_log_i32, func_log_f64, memoria])
    main_func = instancia.exports(store)["main"]

    print("\n=== EJECUCIÓN EN WEBASSEMBLY ===")
    try:
        main_func(store)
        print("=== EJECUCIÓN FINALIZADA SIN ERRORES ===")
    except Exception as e:
        print(f"=== EJECUCIÓN ABORTADA (TRAP): {e} ===")


def main():
    arg_parser = argparse.ArgumentParser(description="Compilador WebAssembly")
    arg_parser.add_argument("archivo", help="Ruta al archivo de código fuente a compilar")
    arg_parser.add_argument("--ast", action="store_true", help="Muestra la Tabla de Símbolos y el AST")
    arg_parser.add_argument("--solo-compilar", action="store_true", help="Genera .wat/.wasm sin ejecutar")
    args = arg_parser.parse_args()

    if not os.path.exists(args.archivo):
        print(f"Error: No se encontró el archivo '{args.archivo}'.")
        sys.exit(1)

    with open(args.archivo, "r", encoding="utf-8") as f:
        codigo_fuente = f.read()

    lexer = analizador_lexico()
    parser = analizador_sintactico()

    tokens = lexer.tokenize(codigo_fuente)
    arbol = parser.parse(tokens)

    hubo_errores = bool(getattr(lexer, "errores", [])) or bool(getattr(parser, "errores", []))
    if hubo_errores or arbol is None:
        print("\nERROR: No se generó código WebAssembly debido a errores.")
        sys.exit(1)

    if args.ast:
        parser.tabla.imprimir()
        arbol.imprimir()

    generador = generador_assembler(parser.tabla)
    codigo_wat = generador.generar(arbol)

    ruta_wat = "salida.wat"
    ruta_wasm = "salida.wasm"
    with open(ruta_wat, "w", encoding="utf-8") as f_wat:
        f_wat.write(codigo_wat)

    print(f"Se ha compilado correctamente. Código generado en '{ruta_wat}'.")

    if not args.solo_compilar:
        ejecutar_modulo_wasm(ruta_wat, ruta_wasm)

if __name__ == "__main__":
    main()