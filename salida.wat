(module
  (import "console" "log" (func $imprime (param i32 i32)))
  (import "console" "log_i32" (func $imprime_i32 (param i32)))
  (import "console" "log_f64" (func $imprime_f64 (param f64)))
  (import "js" "mem" (memory 1))
  (data (i32.const 0) "ERROR DE EJECUCION (d): Overflow en producto de enteros (USHORTINT > 255)")
  (data (i32.const 73) "ERROR DE EJECUCION (e): Overflow en producto de punto flotante (DOUBLEF)")
  (data (i32.const 145) "ERROR DE EJECUCION (h): Asignacion invalida fuera de rango en enumeracion")
  (data (i32.const 218) "ERROR DE EJECUCION (i): Recursion detectada en invocacion de funcion")
  (global $rec_f (mut i32) (i32.const 0))
  (func $f (param $n i32) (result i32)
    (block $no_rec_1
      global.get $rec_f
      i32.eqz
      br_if $no_rec_1
      i32.const 218
      i32.const 68
      call $imprime
      unreachable
    )
    i32.const 1
    global.set $rec_f
    (block $if_end_2
      (block $if_else_3
        local.get $n
        i32.const 0
        i32.gt_u
        i32.eqz
        br_if $if_else_3
        local.get $n
        i32.const 1
        i32.sub
        call $f
        local.set $n
        br $if_end_2
      )
    )
    local.get $n
    i32.const 0
    global.set $rec_f
    return
  )
  (func $main (export "main")
  (local $r i32)
    i32.const 2
    call $f
    local.set $r
    local.get $r
    call $imprime_i32
  )
)