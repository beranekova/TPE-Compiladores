class generador_assembler:
    def __init__(self, tabla_simbolos):
        self.tabla = tabla_simbolos
        self.codigo = []
        self.indentacion = 0
        self.contador_aux = 0
        self.contador_etiquetas = 0
        self.locales_actuales = []
        self.locales_declaradas = set()
        self.globales_recursion = []

        self.offset_data = 0
        self.strings_data = []
        self.mapa_strings = {}

        self.err_ovf_int = self._registrar_string("ERROR DE EJECUCION (d): Overflow en producto de enteros (USHORTINT > 255)")
        self.err_ovf_flt = self._registrar_string("ERROR DE EJECUCION (e): Overflow en producto de punto flotante (DOUBLEF)")
        self.err_enum    = self._registrar_string("ERROR DE EJECUCION (h): Asignacion invalida fuera de rango en enumeracion")
        self.err_rec     = self._registrar_string("ERROR DE EJECUCION (i): Recursion detectada en invocacion de funcion")

    #----------Estructura del codigo generado----------

    #control de identacion y escritura de codigo
    def _emitir(self, linea):
        self.codigo.append("  " * self.indentacion + linea)

    #etiquetas
    def _nueva_etiqueta(self, prefijo="lbl"):
        self.contador_etiquetas += 1
        return f"${prefijo}_{self.contador_etiquetas}"

    #variables auxiliares
    def _nuevo_aux(self, tipo_wasm):
        self.contador_aux += 1
        nombre = f"$__aux_{self.contador_aux}"
        self._declarar_local(nombre, tipo_wasm)
        return nombre

    #declaracion de variables locales para cada ambito
    def _declarar_local(self, nombre_wasm, tipo_wasm):
        if nombre_wasm not in self.locales_declaradas:
            self.locales_declaradas.add(nombre_wasm)
            self.locales_actuales.append(f"(local {nombre_wasm} {tipo_wasm})")

    #conversion de tipos del lenguaje a tipos de WebAssembly
    def _tipo_a_wasm(self, tipo_lenguaje):
        if tipo_lenguaje in ["USHORTINT", "BOOLEAN"] or self._es_enumeracion(tipo_lenguaje):
            return "i32"
        elif tipo_lenguaje == "DOUBLEF":
            return "f64"
        elif tipo_lenguaje == "CADENA":
            return "i32"
        return "i32"

    #chequeos de rangos y valores para enumeraciones
    def _es_enumeracion(self, nombre_tipo):
        sim = self.tabla.buscar(nombre_tipo)
        return sim is not None and sim.get("uso") == "enumeracion"

    #chequeos de tipos y herencia para clases
    def _es_clase(self, nombre_tipo):
        sim = self.tabla.buscar(nombre_tipo)
        return sim is not None and sim.get("uso") == "clase"

    #devuelve una lista ordenada con nombre_atributo, tipo y herencia para la clase
    def _obtener_atributos_clase(self, nombre_clase):
        atributos = []
        sim_clase = self.tabla.buscar(nombre_clase)
        if not sim_clase:
            return atributos

        # primero metemos los atributos heradados
        padre = sim_clase.get("padre") or sim_clase.get("extends")
        if padre:
            atributos.extend(self._obtener_atributos_clase(padre))

        for clave, datos in self.tabla.tabla.items():
            if datos.get("uso") == "variable":
                alcance = datos.get("alcance", "")
                if alcance.endswith(f":{nombre_clase}"):
                    atributos.append((datos.get("lexema", clave.split(":")[0]), datos.get("tipo")))
        return atributos

    #administracion de strings (cadenas de literales) en memoria lineal
    def _registrar_string(self, texto):
        #evitar duplicados y retornar offset y longitud
        if texto in self.mapa_strings:
            return self.mapa_strings[texto]
        offset = self.offset_data
        longitud = len(texto.encode("utf-8")) #codificado a utf-8 para contar bytes reales
        texto_escapado = texto.replace('"', '\\"')
        self.strings_data.append(f'(data (i32.const {offset}) "{texto_escapado}")')
        self.mapa_strings[texto] = (offset, longitud)
        self.offset_data += longitud
        return (offset, longitud)

    def _emitir_error_runtime(self, tupla_offset_len):
        offset, longitud = tupla_offset_len
        self._emitir(f"i32.const {offset}")
        self._emitir(f"i32.const {longitud}")
        self._emitir("call $imprime")
        self._emitir("unreachable")

    def generar(self, nodo_raiz):
        cuerpo_funciones = []
        nodo_decl = nodo_raiz.izquierdo
        if nodo_decl:
            lista_decl = self._aplanar_nodos(nodo_decl.derecho) + self._aplanar_nodos(nodo_decl.izquierdo)
            for decl in lista_decl:
                cuerpo_funciones.extend(self._generar_subprograma(decl))

        nodo_ejec = nodo_raiz.derecho
        cuerpo_main = self._generar_main(nodo_ejec)

        salida = ["(module"]
        salida.append('  (import "console" "log" (func $imprime (param i32 i32)))')
        salida.append('  (import "console" "log_i32" (func $imprime_i32 (param i32)))')
        salida.append('  (import "console" "log_f64" (func $imprime_f64 (param f64)))')
        salida.append('  (import "js" "mem" (memory 1))')

        # Segmentos de datos (strings estáticos y mensajes de error DEHI)
        for data_seg in self.strings_data:
            salida.append(f"  {data_seg}")

        # Variables globales para control de recursión (Control 'i')
        for glob in self.globales_recursion:
            salida.append(f"  {glob}")

        # Funciones y métodos del usuario
        for linea in cuerpo_funciones:
            salida.append(f"  {linea}")

        # Función principal main
        for linea in cuerpo_main:
            salida.append(f"  {linea}")

        salida.append(")")
        return "\n".join(salida)

    def _generar_main(self, nodo_ejec):
        self.codigo = []
        self.locales_actuales = []
        self.locales_declaradas = set()
        self.indentacion = 1

        # Declarar variables locales de main (expandiendo objetos de clase - Opción A)
        self._declarar_variables_de_ambito("main")

        # Generar sentencias ejecutables
        if nodo_ejec:
            sents = self._aplanar_nodos(nodo_ejec.derecho) + self._aplanar_nodos(nodo_ejec.izquierdo)
            for s in sents:
                self._generar_sentencia(s, ambito="main")

        header = ['(func $main (export "main")']
        return header + self.locales_actuales + self.codigo + [")"]

    def _generar_subprograma(self, nodo):
        self.codigo = []
        self.locales_actuales = []
        self.locales_declaradas = set()
        self.indentacion = 1

        if not hasattr(nodo, "valor") or not isinstance(nodo.valor, str):
            return []
        if not (nodo.valor.startswith("FUNCION:") or nodo.valor.startswith("METODO:")):
            return []
        
        es_metodo = nodo.valor.startswith("METODO:")
        if es_metodo:
            nombre_raw = nodo.valor.replace("METODO:", "")
            clase_duena = self._buscar_clase_de_metodo(nombre_raw)
            nombre_wasm = f"${clase_duena}_{nombre_raw}" if clase_duena else f"${nombre_raw}"
            ambito_sub = f"main:{clase_duena}:{nombre_raw}" if clase_duena else f"main:{nombre_raw}"
            params_nodos = []
            # En Opción A, si es método, los atributos de la clase entran como parámetros
            if clase_duena:
                for attr_nom, attr_tipo in self._obtener_atributos_clase(clase_duena):
                    params_nodos.append((f"${attr_nom}", self._tipo_a_wasm(attr_tipo)))
            # Agregamos también los parámetros propios del método desde la TS
            sim_met = self.tabla.buscar(nombre_raw)
            if sim_met:
                for p in sim_met.get("parametros", []):
                    params_nodos.append((f"${p['nombre']}", self._tipo_a_wasm(p["tipo"])))
            tipo_retorno_wasm = self._tipo_a_wasm(sim_met.get("tipo")) if sim_met else "i32"
        else:
            # DECL_FUNCION
            firma = nodo.izquierdo
            nombre_raw = firma.valor.replace("FIRMA:", "")
            nombre_wasm = f"${nombre_raw}"
            ambito_sub = f"main:{nombre_raw}"
            sim_func = self.tabla.buscar(nombre_raw)
            params_nodos = []
            if firma.izquierdo:
                lista_p = firma.izquierdo if isinstance(firma.izquierdo, list) else [firma.izquierdo]
                for p_nodo in lista_p:
                    if self._es_clase(p_nodo.tipo):
                        for attr_nom, attr_tipo in self._obtener_atributos_clase(p_nodo.tipo):
                            params_nodos.append((f"${p_nodo.valor}_{attr_nom}", self._tipo_a_wasm(attr_tipo)))
                    else:
                        params_nodos.append((f"${p_nodo.valor}", self._tipo_a_wasm(p_nodo.tipo)))
            tipo_retorno_wasm = self._tipo_a_wasm(sim_func.get("tipo")) if sim_func else "i32"

        # Declarar variables locales propias de la función/método
        self._declarar_variables_de_ambito(ambito_sub, excluir_params={p[0] for p in params_nodos})

        # CONTROL (i): Detección de recursión en tiempo de ejecución
        flag_rec = f"$rec_{nombre_wasm[1:]}"
        self.globales_recursion.append(f"(global {flag_rec} (mut i32) (i32.const 0))")

        lbl_ok = self._nueva_etiqueta("no_rec")
        self._emitir(f"(block {lbl_ok}")
        self.indentacion += 1
        self._emitir(f"global.get {flag_rec}")
        self._emitir("i32.eqz")
        self._emitir(f"br_if {lbl_ok}")
        self._emitir_error_runtime(self.err_rec)
        self.indentacion -= 1
        self._emitir(")")
        self._emitir("i32.const 1")
        self._emitir(f"global.set {flag_rec}")

        cuerpo = self._aplanar_nodos(nodo.derecho)
        for sent in cuerpo:
            self._generar_sentencia(sent, ambito=ambito_sub, flag_recursion=flag_rec)

        params_str = " ".join([f"(param {p_nom} {p_tipo})" for p_nom, p_tipo in params_nodos])
        header = [f"(func {nombre_wasm} {params_str} (result {tipo_retorno_wasm})"]
        return header + self.locales_actuales + self.codigo + [")"]

    def _buscar_clase_de_metodo(self, nombre_metodo):
        for clave, datos in self.tabla.tabla.items():
            if datos.get("uso") == "metodo" and datos.get("lexema") == nombre_metodo:
                partes = datos.get("alcance", "").split(":")
                if len(partes) >= 2:
                    return partes[-1]
        return None

    def _declarar_variables_de_ambito(self, ambito_objetivo, excluir_params=None):
        excluir = excluir_params or set()
        for clave, datos in self.tabla.tabla.items():
            if datos.get("uso") == "variable" and datos.get("alcance") == ambito_objetivo:
                lex = datos.get("lexema", clave.split(":")[0])
                tipo = datos.get("tipo")
                if self._es_clase(tipo):
                    for attr_nom, attr_tipo in self._obtener_atributos_clase(tipo):
                        nom_wasm = f"${lex}_{attr_nom}"
                        if nom_wasm not in excluir:
                            self._declarar_local(nom_wasm, self._tipo_a_wasm(attr_tipo))
                else:
                    nom_wasm = f"${lex}"
                    if nom_wasm not in excluir:
                        self._declarar_local(nom_wasm, self._tipo_a_wasm(tipo))

    # =========================================================================
    # GENERACIÓN DE SENTENCIAS Y CONTROLES (h: ENUM, d/e: PRODUCTO)
    # =========================================================================

    def _generar_sentencia(self, nodo, ambito="main", flag_recursion=None):
        if nodo is None:
            return

        val = nodo.valor

        # --- ASIGNACIÓN (:= o =) ---
        if val in [":=", "="]:
            izq = nodo.izquierdo
            der = nodo.derecho

            # Caso 1: Asignación entre objetos de clase (Equivalencia estructural - Opción A)
            if self._es_clase(izq.tipo):
                attrs_dest = self._obtener_atributos_clase(izq.tipo)
                attrs_orig = self._obtener_atributos_clase(der.tipo)
                for (a_dest, _), (a_orig, _) in zip(attrs_dest, attrs_orig):
                    self._emitir(f"local.get ${der.valor}_{a_orig}")
                    self._emitir(f"local.set ${izq.valor}_{a_dest}")
                return

            # Caso 2: Asignación a atributo de objeto (obj.attr := expr)
            if izq.valor == ".":
                destino_wasm = f"${izq.izquierdo.valor}_{izq.derecho.valor}"
                self._generar_expresion(der)
                self._emitir(f"local.set {destino_wasm}")
                return

            # Caso 3: Variable primitiva o Enumeración
            self._generar_expresion(der)

            # CONTROL (h): Validar que el valor asignado pertenezca a la enumeración
            if self._es_enumeracion(izq.tipo):
                self._emitir_chequeo_enum(izq.tipo)

            self._emitir(f"local.set ${izq.valor}")

        # --- SELECCIÓN (IF / ELSE) ---
        elif val == "IF":
            condicion = nodo.izquierdo
            cuerpo_if = nodo.derecho  # Nodo CUERPO_IF: izquierdo=THEN, derecho=ELSE
            rama_then = cuerpo_if.izquierdo if cuerpo_if else None
            rama_else = cuerpo_if.derecho if cuerpo_if else None

            lbl_salida = self._nueva_etiqueta("if_end")
            lbl_else = self._nueva_etiqueta("if_else")

            self._emitir(f"(block {lbl_salida}")
            self.indentacion += 1
            self._emitir(f"(block {lbl_else}")
            self.indentacion += 1

            # Evaluamos condición: si es falsa (eqz), saltamos a $if_else
            self._generar_expresion(condicion)
            self._emitir("i32.eqz")
            self._emitir(f"br_if {lbl_else}")

            # Rama THEN
            self._generar_bloque_sentencias(rama_then, ambito, flag_recursion)
            self._emitir(f"br {lbl_salida}")

            self.indentacion -= 1
            self._emitir(")")

            # Rama ELSE (si existe)
            if rama_else is not None:
                self._generar_bloque_sentencias(rama_else, ambito, flag_recursion)

            self.indentacion -= 1
            self._emitir(")")

        # --- BUCLE REPEAT ... WHILE ---
        elif val == "REPEAT":
            cuerpo_rep = nodo.izquierdo
            condicion = nodo.derecho

            lbl_salida = self._nueva_etiqueta("rep_end")
            lbl_loop = self._nueva_etiqueta("rep_loop")

            self._emitir(f"(block {lbl_salida}")
            self.indentacion += 1
            self._emitir(f"(loop {lbl_loop}")
            self.indentacion += 1

            # Ejecuta cuerpo al menos una vez
            self._generar_bloque_sentencias(cuerpo_rep, ambito, flag_recursion)

            # Evalúa condición al final: si es falsa sale, si es verdadera repite
            self._generar_expresion(condicion)
            self._emitir("i32.eqz")
            self._emitir(f"br_if {lbl_salida}")
            self._emitir(f"br {lbl_loop}")

            self.indentacion -= 1
            self._emitir(")")
            self.indentacion -= 1
            self._emitir(")")

        # --- RETORNO (RET) ---
        elif val == "RET":
            if nodo.izquierdo is not None:
                self._generar_expresion(nodo.izquierdo)
            # Liberamos el flag de recursión antes de salir de la función
            if flag_recursion:
                self._emitir("i32.const 0")
                self._emitir(f"global.set {flag_recursion}")
            self._emitir("return")

        # --- SALIDA POR CONSOLA (POUT) ---
        elif val == "POUT":
            arg = nodo.izquierdo
            if arg.tipo == "CADENA":
                texto_limpio = arg.valor.strip('"')
                offset, longitud = self._registrar_string(texto_limpio)
                self._emitir(f"i32.const {offset}")
                self._emitir(f"i32.const {longitud}")
                self._emitir("call $imprime")
            elif arg.tipo == "DOUBLEF":
                self._generar_expresion(arg)
                self._emitir("call $imprime_f64")
            else:
                self._generar_expresion(arg)
                self._emitir("call $imprime_i32")

        # --- INVOCACIÓN SUELTA COMO SENTENCIA ---
        elif val == "INVOCACION":
            self._generar_expresion(nodo)
            # Si la función/método devolvió un valor en la pila y no se asignó, lo descartamos
            if nodo.tipo is not None:
                self._emitir("drop")

    def _generar_bloque_sentencias(self, bloque, ambito, flag_recursion):
        for s in self._aplanar_nodos(bloque):
            self._generar_sentencia(s, ambito, flag_recursion)

    def _emitir_chequeo_enum(self, tipo_enum):
        sim_enum = self.tabla.buscar(tipo_enum)
        valores_raw = sim_enum.get("valores", []) if sim_enum else []
        valores_int = [int(str(v).replace("$us", "")) for v in valores_raw]

        aux_val = self._nuevo_aux("i32")
        lbl_ok = self._nueva_etiqueta("enum_ok")

        self._emitir(f"local.set {aux_val}")
        self._emitir(f"(block {lbl_ok}")
        self.indentacion += 1
        for val_permitido in valores_int:
            self._emitir(f"local.get {aux_val}")
            self._emitir(f"i32.const {val_permitido}")
            self._emitir("i32.eq")
            self._emitir(f"br_if {lbl_ok}")
        self._emitir_error_runtime(self.err_enum)
        self.indentacion -= 1
        self._emitir(")")
        self._emitir(f"local.get {aux_val}")

    # =========================================================================
    # GENERACIÓN DE EXPRESIONES Y CONTROLES (d: OVF INT, e: OVF FLOAT)
    # =========================================================================

    def _generar_expresion(self, nodo):
        if nodo is None:
            return

        val = nodo.valor
        tipo = nodo.tipo

        # --- CONSTANTES ---
        if nodo.uso == "constante":
            if tipo == "USHORTINT":
                num = val.replace("$us", "")
                self._emitir(f"i32.const {num}")
            elif tipo == "DOUBLEF":
                # Convertimos formato D si lo hubiera (ej. 1.5D2 -> 1.5e2)
                num = val.replace("D", "e").replace("d", "e")
                self._emitir(f"f64.const {num}")
            elif tipo == "CADENA":
                texto_limpio = val.strip('"')
                offset, _ = self._registrar_string(texto_limpio)
                self._emitir(f"i32.const {offset}")
            return

        # --- VARIABLES / PARÁMETROS ---
        if nodo.uso in ["variable", "parametro"]:
            self._emitir(f"local.get ${val}")
            return

        # --- ACCESO A ATRIBUTO (obj.attr) ---
        if val == ".":
            self._emitir(f"local.get ${nodo.izquierdo.valor}_{nodo.derecho.valor}")
            return

        # --- CONVERSIÓN EXPLÍCITA todf ---
        if val == "todf":
            self._generar_expresion(nodo.izquierdo)
            self._emitir("f64.convert_i32_u")
            return

        # --- INVOCACIÓN DE FUNCIÓN O MÉTODO ---
        if val == "INVOCACION":
            destino = nodo.izquierdo
            args = nodo.derecho
            lista_args = [] if args is None else (args if isinstance(args, list) else [args])

            if destino.valor == ".":
                # Invocación de método: obj_a.calcular(x)
                obj_nombre = destino.izquierdo.valor
                met_nombre = destino.derecho.valor
                sim_obj = self.tabla.buscar(obj_nombre)
                clase_nombre = sim_obj.get("tipo") if sim_obj else ""
                # Apilamos primero los atributos del objeto receptor (Opción A)
                for attr_nom, _ in self._obtener_atributos_clase(clase_nombre):
                    self._emitir(f"local.get ${obj_nombre}_{attr_nom}")
                # Luego apilamos los argumentos reales
                for arg in lista_args:
                    self._generar_expresion(arg)
                self._emitir(f"call ${clase_nombre}_{met_nombre}")
            else:
                # Invocación de función global: calcular(x)
                for arg in lista_args:
                    if self._es_clase(arg.tipo):
                        for attr_nom, _ in self._obtener_atributos_clase(arg.tipo):
                            self._emitir(f"local.get ${arg.valor}_{attr_nom}")
                    else:
                        self._generar_expresion(arg)
                self._emitir(f"call ${destino.valor}")
            return

        # --- OPERACIONES ARITMÉTICAS ---
        if val in ["+", "-", "*", "/"]:
            self._generar_expresion(nodo.izquierdo)
            self._generar_expresion(nodo.derecho)

            if tipo == "USHORTINT":
                if val == "+":
                    self._emitir("i32.add")
                elif val == "-":
                    self._emitir("i32.sub")
                elif val == "*":
                    self._emitir("i32.mul")
                    # CONTROL (d): Overflow en producto de enteros sin signo (> 65535)
                    aux_res = self._nuevo_aux("i32")
                    lbl_ok = self._nueva_etiqueta("mul_int_ok")
                    self._emitir(f"local.set {aux_res}")      # <-- Guardamos ANTES de abrir el block
                    self._emitir(f"(block {lbl_ok}")
                    self.indentacion += 1
                    self._emitir(f"local.get {aux_res}")      # <-- Leemos ADENTRO del block
                    self._emitir("i32.const 255")
                    self._emitir("i32.le_u")
                    self._emitir(f"br_if {lbl_ok}")
                    self._emitir_error_runtime(self.err_ovf_int)
                    self.indentacion -= 1
                    self._emitir(")")
                    self._emitir(f"local.get {aux_res}")      # <-- Dejamos el resultado válido en la pila
                elif val == "/":
                    self._emitir("i32.div_u")

            elif tipo == "DOUBLEF":
                if val == "+":
                    self._emitir("f64.add")
                elif val == "-":
                    self._emitir("f64.sub")
                elif val == "*":
                    self._emitir("f64.mul")
                    # CONTROL (e): Overflow en producto de punto flotante (abs(res) == inf)
                    aux_res = self._nuevo_aux("f64")
                    lbl_ok = self._nueva_etiqueta("mul_flt_ok")
                    self._emitir(f"local.set {aux_res}")      # <-- Guardamos ANTES de abrir el block
                    self._emitir(f"(block {lbl_ok}")
                    self.indentacion += 1
                    self._emitir(f"local.get {aux_res}")      # <-- Leemos ADENTRO del block
                    self._emitir("f64.abs")
                    self._emitir("f64.const inf")
                    self._emitir("f64.lt")
                    self._emitir(f"br_if {lbl_ok}")
                    self._emitir_error_runtime(self.err_ovf_flt)
                    self.indentacion -= 1
                    self._emitir(")")
                    self._emitir(f"local.get {aux_res}")      # <-- Dejamos el resultado válido en la pila
                elif val == "/":
                    self._emitir("f64.div")
            return

        # --- COMPARADORES RELACIONALES ---
        if isinstance(val, tuple) and val[0] == "comparador":
            op_rel = val[1]
            tipo_ops = nodo.izquierdo.tipo
            self._generar_expresion(nodo.izquierdo)
            self._generar_expresion(nodo.derecho)

            if tipo_ops == "DOUBLEF":
                mapa_f64 = {"==": "f64.eq", "!=": "f64.ne", "<": "f64.lt", ">": "f64.gt", "<=": "f64.le", ">=": "f64.ge"}
                self._emitir(mapa_f64[op_rel])
            else:
                mapa_i32 = {"==": "i32.eq", "!=": "i32.ne", "<": "i32.lt_u", ">": "i32.gt_u", "<=": "i32.le_u", ">=": "i32.ge_u"}
                self._emitir(mapa_i32[op_rel])
            return

    def _aplanar_nodos(self, item):
        if item is None:
            return []
        if isinstance(item, list):
            res = []
            for sub in item:
                res.extend(self._aplanar_nodos(sub))
            return res
        return [item]