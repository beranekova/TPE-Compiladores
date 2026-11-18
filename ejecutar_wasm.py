from wasmtime import Engine, Store, Module, Instance, Func, FuncType, ValType, Limits, Memory, MemoryType

engine = Engine()
store = Store(engine)

# 1. Cargamos el binario salida.wasm (o directamente salida.wat)
modulo = Module.from_file(engine, "salida.wat")

# 2. Creamos la memoria lineal (1 página = 64 KB) y las funciones de consola
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

# 3. Instanciamos el módulo conectando los 4 imports en el orden exacto de salida.wat
instancia = Instance(store, modulo, [func_log, func_log_i32, func_log_f64, memoria])
main_func = instancia.exports(store)["main"]

print("--- Iniciando ejecución ---")
try:
    main_func(store)
    print("--- Ejecución finalizada sin errores ---")
except Exception as e:
    print(f"--- Ejecución abortada (trap): {e} ---")