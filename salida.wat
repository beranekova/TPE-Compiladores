(module
  (import "console" "log" (func $imprime (param i32 i32)))
  (import "console" "log_i32" (func $imprime_i32 (param i32)))
  (import "console" "log_f64" (func $imprime_f64 (param f64)))
  (import "js" "mem" (memory 1))
  (data (i32.const 0) "ERROR DE EJECUCION (d): Overflow en producto de enteros (USHORTINT > 255)")
  (data (i32.const 73) "ERROR DE EJECUCION (e): Overflow en producto de punto flotante (DOUBLEF)")
  (data (i32.const 145) "ERROR DE EJECUCION (h): Asignacion invalida fuera de rango en enumeracion")
  (data (i32.const 218) "ERROR DE EJECUCION (i): Recursion detectada en invocacion de funcion")
  (func $main (export "main")
  (local $x i32)
  (local $y f64)
    i32.const 1
    local.set $x
    local.get $x
    call $imprime_i32
    local.get $x
    f64.convert_i32_u
    local.set $y
    local.get $y
    call $imprime_f64
    local.get $x
    call $imprime_i32
  )
)