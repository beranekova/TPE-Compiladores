(module
  (import "console" "log" (func $imprime (param i32 i32)))
  (import "console" "log_i32" (func $imprime_i32 (param i32)))
  (import "console" "log_f64" (func $imprime_f64 (param f64)))
  (import "js" "mem" (memory 1))
  (data (i32.const 0) "ERROR DE EJECUCION (d): Overflow en producto de enteros (USHORTINT > 65535)")
  (data (i32.const 75) "ERROR DE EJECUCION (e): Overflow en producto de punto flotante (DOUBLEF)")
  (data (i32.const 147) "ERROR DE EJECUCION (h): Asignacion invalida fuera de rango en enumeracion")
  (data (i32.const 220) "ERROR DE EJECUCION (i): Recursion detectada en invocacion de funcion")
  (global $rec_clase_a_calcular (mut i32) (i32.const 0))
  (global $rec_calcular (mut i32) (i32.const 0))
  (func $clase_a_calcular (param $papepo i32) (param $x i32) (result i32)
    (block $no_rec_1
      global.get $rec_clase_a_calcular
      i32.eqz
      br_if $no_rec_1
      i32.const 220
      i32.const 68
      call $imprime
      unreachable
    )
    i32.const 1
    global.set $rec_clase_a_calcular
    local.get $x
    i32.const 1
    i32.add
    local.set $papepo
    i32.const 0
    i32.const 0
    global.set $rec_clase_a_calcular
    return
  )
  (func $calcular (param $x i32) (result i32)
    (block $no_rec_2
      global.get $rec_calcular
      i32.eqz
      br_if $no_rec_2
      i32.const 220
      i32.const 68
      call $imprime
      unreachable
    )
    i32.const 1
    global.set $rec_calcular
    local.get $x
    i32.const 1
    i32.add
    local.set $x
    i32.const 0
    i32.const 0
    global.set $rec_calcular
    return
  )
  (func $main (export "main")
  (local $x i32)
  (local $y f64)
  (local $obj_a_papepo i32)
    i32.const 1
    local.set $x
    (block $if_end_3
      (block $if_else_4
        local.get $x
        i32.const 2
        i32.lt_u
        i32.eqz
        br_if $if_else_4
        i32.const 7
        local.set $x
        br $if_end_3
      )
      i32.const 7
      local.set $x
    )
    (block $rep_end_5
      (loop $rep_loop_6
        local.get $obj_a_papepo
        local.get $x
        call $clase_a_calcular
        local.set $x
        local.get $x
        i32.const 3
        i32.lt_u
        i32.eqz
        br_if $rep_end_5
        br $rep_loop_6
      )
    )
    local.get $x
    call $calcular
    local.set $x
    local.get $x
    f64.convert_i32_u
    local.set $y
    local.get $y
    call $imprime_f64
  )
)