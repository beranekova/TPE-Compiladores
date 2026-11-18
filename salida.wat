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
  (local $c i32)
  (local $x i32)
  (local $__aux_1 i32)
    i32.const 23
    local.set $x
    local.get $x
    local.set $__aux_1
    (block $enum_ok_1
      local.get $__aux_1
      i32.const 1
      i32.eq
      br_if $enum_ok_1
      local.get $__aux_1
      i32.const 15
      i32.eq
      br_if $enum_ok_1
      local.get $__aux_1
      i32.const 255
      i32.eq
      br_if $enum_ok_1
      i32.const 145
      i32.const 73
      call $imprime
      unreachable
    )
    local.get $__aux_1
    local.set $c
    local.get $c
    call $imprime_i32
  )
)