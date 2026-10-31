import sys
import json
from sly import Lexer, Parser
from pprint import pprint
from tabla_simbolos import TablaSimbolos
from analizador_lexico import analizador_lexico

class analizador_sintactico(Parser):

    def __init__(self):
        super().__init__()
        self.ts = TablaSimbolos()
        self.errores = 0
    
    def reportar_error(self, mensaje):
        print(mensaje)
        self.errores += 1

    tokens = analizador_lexico.tokens

    debugfile = 'parser.out'

    precedence = (
        ('right', 'ASIGNACION_IGUAL'),
        ('left', 'MAS', 'MENOS'),
        ('left', 'MULT', 'DIV'),
        ('right', 'UMINUS'),
        ('right', 'ID'),
    )

    #DECLARACION DE PROGRAMA

    @_('PROGRAM ID sentencias_declarativas cuerpo_programa')
    def programa(self, p):
        #aca no es necesario declarar nada para la tabla porque se inicializa en ambito main por defecto
        return p

    #-----------------------// SENTENCIAS DECLARATIVAS //-----------------------

    #Declaracion de una o mas sentencias
    @_('sentencias_declarativas sentencia_declarativa')
    def sentencias_declarativas(self, p):
        return p

    @_('BEGIN sentencias_ejecutables END')
    def cuerpo_programa(self, p):
        return p

    #ninguna sentencia declarada
    @_('')
    def sentencias_declarativas(self,p):
        return []
    
    #declaramos el cuerpo_declaracion para separar y que sea mas facil ver si falta el ;
    @_('cuerpo_declaracion ";"')
    def sentencia_declarativa(self, p):
        return p.cuerpo_declaracion
    
    #aca van las declaraciones posibles
    @_('declaracion_variables',
       'declaracion_funcion',
       'declaracion_de_clase_completa')
    def cuerpo_declaracion(self, p):
        return p[0]
    
    @_('TYPEDEF ID ASIGNACION_IGUAL "[" lista_valores "]"')
    def cuerpo_declaracion(self, p):
        exito = self.tabla.insertar(p.ID, 'ID', tipo='enum', uso='enumeracion', valores=p.lista_valores)
        if not exito:
            self.reportar_error(f"Error semantico: El identificador '{p.ID}' ya fue declarado en este ambito. Linea {p.lineno}")
            
        return p
    
    @_('CLASS ID')
    def cabecera_clase(self, p):
        exito = self.tabla.insertar(p.ID, 'ID', tipo='clase', uso='clase')
        #verificamos si la clase esta declarada o no previamente dentro del ambito en el que esta
        if not exito:
            self.reportar_error(f"Error semantico: la clase '{p.ID}' ya fue declarada. Linea {p.lineno}")
        self.tabla.abrir_ambito(p.ID)
        return p.ID

    @_('cabecera_clase BEGIN declaracion_clase END')
    def declaracion_de_clase_completa(self, p):
        #cerramos el ambito una vez encontramos que la declaracion de la clase termino
        self.tabla.cerrar_ambito()
        return p
    
    @_('tipo lista_variables')
    def declaracion_variables(self, p):
        tipo_var = p.tipo

        #aca no verificamos si el tipo existe ya que es un tipo nativo que existe predefinido en la tabla de simbolos
        for identificador in p.lista_variables:
            exito = self.tabla.insertar(identificador, 'ID', tipo=tipo_var, uso='variable')
            
            if not exito:
                self.reportar_error(f"Error semantico: la variable '{identificador}' ya fue declarada en este ambito. Linea {p.lineno}")
        return p
    
    @_('ID lista_variables')
    def declaracion_variables(self, p):
        tipo_custom = p.ID 
        
        #primero verificamos que el tipo del enumerado o clase exista en al tabla
        simbolo_tipo = self.tabla.buscar(tipo_custom)
        if not simbolo_tipo or simbolo_tipo.get('uso') not in ['clase', 'enumeracion']:
            self.reportar_error(f"Error semantico: el tipo '{tipo_custom}' no esta declarado o no es valido. Linea {p.lineno}")
            
        #si existe, nos fijamos si esta redeclarada o no la variable
        for identificador in p.lista_variables:
            exito = self.tabla.insertar(identificador, 'ID', tipo=tipo_custom, uso='variable')
            if not exito:
                self.reportar_error(f"Error semantico: la variable '{identificador}' ya fue declarada. Linea {p.lineno}")
        return p

    @_('USHORTINT', 
       'DOUBLEF')
    def tipo(self, p):
        return p

    @_('lista_variables "," ID')
    def lista_variables(self, p):
        return p.lista_variables + [p.ID]

    @_('ID')
    def lista_variables(self, p):
        return [p.ID]

    #DECLARACION DE FUNCIONES
    
    #parametros formales de funciones

    @_('firma_funcion cuerpo_funcion')
    def declaracion_funcion(self, p):
        self.tabla.cerrar_ambito(p.ID)
        return p

    #dividimos la funcion en cabecera y firma para poder revisar si en el ambito padre ya se encuentra un ID (redeclaracion)
    @_('tipo FUNCTION ID')
    def cabecera_funcion(self, p):
        exito = self.tabla.insertar(p.ID, 'ID', tipo=p.tipo, uso='funcion')
        if not exito:
            #verificamos si el ID de la funcion ya existe en el ambito en el que esta declarada la funcion
            self.reportar_error(f"Error semantico: la funcion '{p.ID}' ya fue declarada. Linea {p.lineno}")
            
        self.tabla.abrir_ambito(p.ID)
        return p.ID

    #dentro en la firma verificamos que los parametros y las declaraciones sean validas semanticamente
    @_('cabecera_funcion "(" parametros_formales ")" sentencias_declarativas')
    def firma_funcion(self, p):
        return p
    
    @_('BEGIN sentencias_ejecutables_funcion END')
    def cuerpo_funcion(self, p):
        return p

    @_('lista_parametros')
    def parametros_formales(self, p):
        return p.lista_parametros
    
    @_('')
    def parametros_formales(self, p):
        return []

    @_('tipo ID')
    def lista_parametros(self, p):
        exito = self.tabla.insertar(p.ID, 'ID', tipo=p.tipo, uso='parametro')
        if not exito:
            self.reportar_error(f"Error semantico: parametro '{p.ID}' redeclarado. Linea {p.lineno}")
        
        return [{'nombre': p.ID, 'tipo': p.tipo}]

    @_('lista_parametros "," tipo ID')
    def lista_parametros(self, p):
        exito = self.tabla.insertar(p.ID, 'ID', tipo=p.tipo, uso='parametro')
        if not exito:
            self.reportar_error(f"Error semantico: parametro '{p.ID}' redeclarado. Linea {p.lineno}")
        
        # Recuperamos la lista que venía subiendo por el árbol
        lista_acumulada = p.lista_parametros
        
        # Le agregamos el nuevo parámetro
        lista_acumulada.append({'nombre': p.ID, 'tipo': p.tipo})
        
        # Devolvemos la lista actualizada para que siga subiendo
        return lista_acumulada
    
    @_('sentencias_ejecutables_funcion sentencia_ejecutable_funcion')
    def sentencias_ejecutables_funcion(self, p):
        return p
    
    @_('')
    def sentencias_ejecutables_funcion(self, p):
        return p

    @_('sentencia_ejecutable')
    def sentencia_ejecutable_funcion(self, p):
        return p
        
    @_('cuerpo_retorno ";"')
    def sentencia_ejecutable_funcion(self, p):
        return p.cuerpo_retorno

    @_('RET retorno')
    def cuerpo_retorno(self, p):
        return p

    @_('expresion')
    def retorno(self, p):
        return p

    #DECLARACION DE CLASES
    
    @_('declaracion_clase elemento_clase',
       '')
    def declaracion_clase(self, p):
        return p
    
    @_('cuerpo_elemento_clase ";"')
    def elemento_clase(self, p):
        return p

    @_('EXTENDS lista_variables',
       'declaracion_variables',
       'declaracion_metodo')
    def cuerpo_elemento_clase(self, p):
        return p[0]

    @_('firma_metodo cuerpo_funcion')
    def declaracion_metodo(self, p):
        self.tabla.cerrar_ambito()
        return p
    
    @_('cabecera_metodo "(" parametros_formales ")"')
    def firma_metodo(self, p):
        return p

    @_('tipo ID') 
    def cabecera_metodo(self, p):
        exito = self.tabla.insertar(p.ID, 'ID', tipo=p.tipo, uso='metodo')
        if not exito:
            self.reportar_error(f"Error semantico: el metodo '{p.ID}' ya fue declarado en esta clase. Linea {p.lineno}")
            
        self.tabla.abrir_ambito(p.ID)
        return p.ID
    
    #----------------TEMA 23: ENUMERADOS

    @_('lista_valores "," CTE_USHORTINT')
    def lista_valores(self, p):
        return p

    @_('CTE_USHORTINT')
    def lista_valores(self, p):
        return p

    #-----------------------// FIN DE SENTENCIAS DECLARATIVAS //-----------------------

    #-----------------------// SENTENCIAS EJECUTABLES //-----------------------

    #ESTRUCTURA DE SENTENCIAS EJECUTABLES
    @_('BEGIN sentencias_ejecutables END')
    def bloque_ejecutable(self, p):
        return p
    
    @_('sentencia_ejecutable')
    def bloque_ejecutable(self, p):
        return p
    
    @_('sentencias_ejecutables sentencia_ejecutable')
    def sentencias_ejecutables(self, p):
        return p

    @_('')
    def sentencias_ejecutables(self, p):
        return []
    
    @_('cuerpo_sentencia_ejecutable ";"')
    def sentencia_ejecutable(self, p):
        return p
    
    @_('asignacion_punto',
       'llamado_funcion',
       'IF condicion_parentesis bloque_ejecutable bloque_else END_IF',
       'POUT "(" expresion ")"',
       'REPEAT bloque_ejecutable WHILE condicion_parentesis')
    def cuerpo_sentencia_ejecutable(self, p):
        return p[0]

    #----------------DEFINICION DE ASIGNACIONES
    
    @_('lado_izquierdo ASIGNACION_PUNTO expresion')
    def asignacion_punto(self, p):
        return p

    @_('lado_izquierdo ASIGNACION_IGUAL "(" expresion ")"')
    def asignacion_igual(self, p):
        return p
    
    @_('ID')
    def lado_izquierdo(self, p):
        simbolo = self.tabla.buscar(p.ID)
        
        # se valida que el ID este declarado en el ambito local o en algun padre
        if not simbolo:
            self.reportar_error(f"Error semantico: la variable '{p.ID}'- no fue declarada. Linea {p.lineno}")
            tipo_encontrado = "ERROR"
        else:
            # si se encuentra declarado en local o en algun padre, se guarda la informacion del tipo y uso para posterior utilizacion
            tipo_encontrado = simbolo["tipo"]
            if simbolo["uso"] not in ['variable', 'parametro']:
                self.reportar_error(f"Error semantico: uso incorrecto del identificador '{p.ID}'. Linea {p.lineno}")

        return NodoArbol(valor=p.ID, tipo=tipo_encontrado)

    @_('ID "." ID')
    def lado_izquierdo(self, p):
        nombre_obj = p.ID0
        nombre_attr = p.ID1

        #buscamos que el objeto exista primero
        simbolo_obj = self.tabla.buscar(nombre_obj)
        if not simbolo_obj:
            self.reportar_error(f"Error semantico: el objeto '{nombre_obj}' no fue declarado. Linea {p.lineno}")
            return NodoArbol(valor=".", izquierdo=NodoArbol(valor=nombre_obj), derecho=NodoArbol(valor=nombre_attr), tipo="ERROR")

        #si existe, extraemos el tipo, que el tipo del objeto es la entrada de la tabla que tiene el nombre de la clase
        #el cual usamos para verificar que ese tipo extraido sea efectivamente de uso Clase y ya haya estado declarada
        nombre_clase = simbolo_obj.get("tipo")        
        simbolo_clase = self.tabla.buscar(nombre_clase)
        if not simbolo_clase or simbolo_clase.get("uso") != "clase":
            self.reportar_error(f"Error semantico: '{nombre_obj}' no es un objeto de clase. Linea {p.lineno}")
            return NodoArbol(valor=".", izquierdo=NodoArbol(valor=nombre_obj), derecho=NodoArbol(valor=nombre_attr), tipo="ERROR")

        #para la clase valida que obtuvimos, armamos todo el alcance para verificar que el atributo existe realmente dentro de la clase
        #y no confundir y verificar en otro ambito
        alcance_clase = f"{simbolo_clase['alcance']}:{nombre_clase}"
        
        #de aca obtenemos el alcance completo que tiene el simbolo que vamos a verificar esta declarado en la clase
        simbolo_attr = self.tabla.obtener(nombre_attr, alcance=alcance_clase)

        #verificamos que el uso del atributo sea una variable
        if not simbolo_attr or simbolo_attr.get("uso") != "variable":
            self.reportar_error(f"Error semantico: el atributo '{nombre_attr}' no existe en la clase '{nombre_clase}'. Linea {p.lineno}")
            tipo_attr = "ERROR"
        else:
            tipo_attr = simbolo_attr["tipo"]

        #devolvemos un nodo para el arbol con el tipo de la variable para hacer la verificacion de compatibilidad de tipos
        return NodoArbol(valor=".", izquierdo=NodoArbol(valor=nombre_obj), derecho=NodoArbol(valor=nombre_attr), tipo=tipo_attr)

    @_('ID "[" CTE_USHORTINT "]"')
    def lado_izquierdo(self, p):
        nombre_obj = p.ID
        # Ajustá esto si tu lexer devuelve un diccionario en vez de un string (ej: int(p.CTE_USHORTINT['lexema']))
        indice = int(p.CTE_USHORTINT) 

        # 1. Buscamos el objeto y su clase (misma lógica que arriba)
        simbolo_obj = self.tabla.buscar(nombre_obj)
        if not simbolo_obj:
            self.reportar_error(f"Error semantico: el objeto '{nombre_obj}' no fue declarado. Linea {p.lineno}")
            return NodoArbol(valor="[]", izquierdo=NodoArbol(valor=nombre_obj), derecho=NodoArbol(valor=str(indice)), tipo="ERROR")

        nombre_clase = simbolo_obj.get("tipo")
        simbolo_clase = self.tabla.buscar(nombre_clase)
        if not simbolo_clase or simbolo_clase.get("uso") != "clase":
            self.reportar_error(f"Error semantico: '{nombre_obj}' no es un objeto de clase. Linea {p.lineno}")
            return NodoArbol(valor="[]", izquierdo=NodoArbol(valor=nombre_obj), derecho=NodoArbol(valor=str(indice)), tipo="ERROR")

        # 2. Recuperamos la lista posicional de atributos guardada en la tabla
        atributos_clase = simbolo_clase.get("atributos", [])
        
        # 3. Validamos que el índice no se pase del límite de atributos
        if indice >= len(atributos_clase):
            self.reportar_error(f"Error semantico: Indice fuera de rango. La clase '{nombre_clase}' tiene {len(atributos_clase)} atributos, se pidio el indice {indice}. Linea {p.lineno}")
            return NodoArbol(valor="[]", izquierdo=NodoArbol(valor=nombre_obj), derecho=NodoArbol(valor=str(indice)), tipo="ERROR")

        # 4. Extraemos el nombre real del atributo desde la lista
        nombre_attr = atributos_clase[indice]

        # 5. Buscamos ese atributo en el ámbito de la clase para obtener su tipo semántico
        alcance_clase = f"{simbolo_clase['alcance']}:{nombre_clase}"
        simbolo_attr = self.tabla.obtener(nombre_attr, alcance=alcance_clase)
        
        tipo_attr = simbolo_attr["tipo"] if simbolo_attr else "ERROR"

        # Transformamos el nodo posicional para que la generación de código sea más sencilla
        return NodoArbol(valor="posicional", izquierdo=NodoArbol(valor=nombre_obj), derecho=NodoArbol(valor=nombre_attr), tipo=tipo_attr)
    
    @_('"(" condicion ")"')
    def condicion_parentesis(self, p):
        return p
    
    @_('expresion comparador expresion')
    def condicion(self, p):
        return p
    
    @_('MAYOR', 
       'MENOR', 
       'MAYOR_IGUAL', 
       'MENOR_IGUAL', 
       'IGUAL', 
       'DISTINTO')
    def comparador(self, p):
        return p
    
    @_('ELSE bloque_ejecutable')
    def bloque_else(self, p):
        return p

    @_('')
    def bloque_else(self, p):
        return []
    
    # ---------------- EXPRESIONES ARITMETICAS ----------------

    def _procesar_operacion_binaria(self, op, izq, der, linea):
    # Verificación del Tema 33 (Conversión explícita requerida)
        if izq.tipo != der.tipo:
            self.reportar_error_semantico(
                f"Error Semántico: Tipos incompatibles para '{op}' ('{izq.tipo}' y '{der.tipo}'). "
                f"Se requiere conversión explícita 'todf'.", 
                linea
            )
            tipo_res = "ERROR"
        else:
            tipo_res = izq.tipo

        return NodoArbol(valor=op, izquierdo=izq, derecho=der, tipo=tipo_res)


    #chusmear que onda con que se pisan las definiciones de la expresion
    @_('expresion MAS expresion',
       'expresion MENOS expresion',
       'expresion MULT expresion',
       'expresion DIV expresion')
    def expresion(self, p):
        return self._procesar_operacion_binaria(p[1], p.expresion0, p.expresion1, p.lineno)

    @_('TODF "(" expresion ")"')
    def expresion(self, p):
        nodo_expr = p.expresion
        # Verificamos que lo que se intenta convertir sea de tipo entero
        if nodo_expr.tipo != "USHORTINT":
            self.reportar_error_semantico(
                f"Error Semántico: 'todf' requiere una expresión de tipo entero, se obtuvo '{nodo_expr.tipo}'", 
                p.lineno
            )
        # Retornamos el nodo de conversión promocionando el tipo a DOUBLEF
        return NodoArbol(valor="todf", izquierdo=nodo_expr, tipo="DOUBLEF")

    @_('lado_izquierdo',
       'asignacion_igual',
       'CTE_USHORTINT',
       'expr_cte_doublef',
       'expr_neg_cte_doublef',
       'llamado_funcion',
       'CADENA')
    def expresion(self, p):
        return p[0]
    
    @_('CTE_DOUBLEF')
    def expr_cte_doublef(self, p):
        return p.CTE_DOUBLEF

    @_('MENOS CTE_DOUBLEF %prec UMINUS')
    def expr_neg_cte_doublef(self, p):
        lexema_positivo = p.CTE_DOUBLEF["lexema"]
        lexema_negativo = f"-{lexema_positivo}"
        valor = float(lexema_negativo.lower().replace('d', 'e'))
        if hasattr(self, 'ts'):
            self.ts.insertar(lexema_negativo, "CTE_DOUBLEF", valor=valor)
            self.ts.eliminar(lexema_positivo, "CTE_DOUBLEF")
            return self.ts.obtener(lexema_negativo, "CTE_DOUBLEF")

    #----------------INVOCACION DE FUNCIONES (Y METODOS DE CLASES)
    
    @_('lado_izquierdo "(" lista_argumentos ")" orden_parametros')
    def llamado_funcion(self, p):
        return p
    
    @_('"[" lista_orden "]"')
    def orden_parametros(self, p):
        return p.lista_orden
    
    @_('')
    def orden_parametros(self, p):
        return p
    
    @_('lista_orden "," CTE_USHORTINT')
    def lista_orden(self, p):
        return p.lista_orden + [p.CTE_USHORTINT]

    @_('CTE_USHORTINT')
    def lista_orden(self, p):
        return [p.CTE_USHORTINT]

    @_('parametros_reales')
    def lista_argumentos(self, p):
        return p.parametros_reales
    
    @_('')
    def lista_argumentos(self, p):
        return []

    @_('parametros_reales "," expresion')
    def parametros_reales(self, p):
        return p.parametros_reales + [p.expresion]
    
    @_('expresion')
    def parametros_reales(self, p):
        return [p.expresion]

    # TRATAMIENTO DE ERRORES
    def error(self, p):
        if not p:
            self.reportar_error(f"Error Sintactico: fin de programa inesperado, revisar cierre de bloques.")
            return
        pass

    #ERROR: DECLARACION DE PROGRAMA INVALIDA
    @_('error sentencias_declarativas BEGIN sentencias_ejecutables END')
    def programa(self, p):
        self.reportar_error(f"Error sintactico: declaracion de programa invalida. Revisar inicio de programa")
        return ('ERROR_RECUPERADO',)

    #ERROR: DELIMITADORES FALTANTES
    @_('BEGIN sentencias_ejecutables error')
    def bloque_ejecutable(self, p):
        self.reportar_error(f"Error sintactico: falta delimitador END de linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    @_('firma_funcion BEGIN sentencias_ejecutables_funcion error')
    def sentencia_declarativa(self, p):
        self.reportar_error(f"Error sintactico: falta delimitador END para cerrar la funcion de linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    #ERRORES DE FUNCIONES

    #firma_funcion: tipo FUNCTION ID "(" parametros_formales ")" sentencias_declarativas

    @_('error FUNCTION ID "(" parametros_formales ")" sentencias_declarativas')
    def firma_funcion(self, p):
        self.reportar_error(f"Error sintactico: falta tipo de retorno en funcion. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    @_('tipo ID "(" parametros_formales ")" sentencias_declarativas')
    def firma_funcion(self, p):
        self.reportar_error(f"Error sintactico: funcion mal declarada. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    @_('tipo FUNCTION error "(" parametros_formales ")" sentencias_declarativas')
    def firma_funcion(self, p):
        self.reportar_error(f"Error sintactico: falta nombre de funcion. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
        
    @_('tipo FUNCTION ID "(" error ")" sentencias_declarativas')
    def firma_funcion(self, p):
        self.reportar_error(f"Error sintactico: parametros formales mal definidos, ver tipo o nombre. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)

    @_('tipo FUNCTION ID "(" error cuerpo_funcion')
    def declaracion_funcion(self, p):
        self.reportar_error(f"Error sintactico: falta parentesis de cierre ')'. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    #Regla general de error en firma_funcion
    @_('error cuerpo_funcion')
    def declaracion_funcion(self, p):
        self.reportar_error(f"Error sintactico: funcion mal declarada. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    #OPCION 1: todas las reglas de funcion + regla general ded firma_funcion
    #OPCION 2: unicamente regla general de funcion + regla de falta PR FUNCTION
    
    #FALTA DE PUNTO Y COMA (sentencias declarativas, ejecutables, ejecutables de funcion)

    @_('cuerpo_declaracion error')
    def sentencia_declarativa(self, p):
        self.reportar_error(f"Error sintactico en declaracion de variable. Revisar ; o caracteres indebidos cerca de linea {p._slice[1].lineno}")
        return ('ERROR_RECUPERADO',)

    @_('error ";"')
    def sentencia_declarativa(self, p):
        self.reportar_error(f"Error sintactico: declaracion invalida. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)

    @_('cuerpo_sentencia_ejecutable error')
    def sentencia_ejecutable(self, p):
        self.reportar_error(f"Error sintactico: sentencia ejecutable invalida. Revisar ';' o expresion invalida. Linea {p._slice[1].lineno}.")
        return ('ERROR_RECUPERADO',)
    
    @_('cuerpo_retorno error')
    def sentencia_ejecutable_funcion(self, p):
        self.reportar_error(f"Error sintactico: falta ; cerca de linea ac{p._slice[1].lineno}.")
        return ('ERROR_RECUPERADO',)
    
    @_('cuerpo_elemento_clase error')
    def elemento_clase(self, p):
        self.reportar_error(f"Error sintactico: revisar falta de ';' o declaracion erronea de metodos. Linea {p._slice[1].lineno}.")
        return ('ERROR_RECUPERADO',)
    
    #ERRORES EN ENUMERADO
    #Falta de valores en enumerado. Ademas, como la lista no puede ser vacia, usamos el error, para que cualquier error sea contado ahi dentro

    @_('TYPEDEF ID ASIGNACION_IGUAL "[" error "]"')
    def cuerpo_declaracion(self, p):
        self.reportar_error(f"Error sintactico: declaracion invalida para valores de enumerado. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)

    #ERRORES DE CLASE
    #Falta de nombre, delimitadores, errores internos (atributos y metodos)
    @_('CLASS error declaracion_clase END')
    def cuerpo_declaracion(self, p):
        self.reportar_error(f"Error sintactico: falta identificador de clase o BEGIN de clase. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    @_('error ";"')
    def elemento_clase(self, p):
        self.reportar_error(f"Error sintactico: elemento de clase mal declarado. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    #ERRORES EN METODOS DE CLASE
    @_('ID "(" parametros_formales ")"')
    def firma_metodo(self, p):
        self.reportar_error(f"Error sintactico: falta el tipo de retorno en el metodo. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)

    @_('tipo "(" parametros_formales ")"')
    def firma_metodo(self, p):
        self.reportar_error(f"Error sintactico: falta el nombre del metodo. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)

    @_('tipo ID "(" error ")"')
    def firma_metodo(self, p):
        self.reportar_error(f"Error sintactico: parametros invalidos en el metodo, revisar tipo y nombre. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    #ERRORES EN SENTENCIAS EJECUTABLES

    @_('POUT error')
    def cuerpo_sentencia_ejecutable(self, p):
        self.reportar_error(f"Error sintactico: argumento de salida invalido, revisar '()' o argumento. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    @_('"(" error ")"')
    def condicion_parentesis(self, p):
        self.reportar_error(f"Error sintactico: condicion invalida, revisar '()' y condicion. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    @_('lado_izquierdo ASIGNACION_PUNTO "(" expresion ")"')
    def asignacion_igual(self, p):
        self.reportar_error(f"Error sintactico: asignacion invalida, debe ser '='. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)

    @_('lado_izquierdo ASIGNACION_IGUAL expresion')
    def asignacion_punto(self, p):
        self.reportar_error(f"Error sintactico: la inicializacion de variables se hace con ':='. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    @_('error ";"')
    def sentencia_ejecutable(self, p):
        self.reportar_error(f"Error sintactico: sentencia o expresion invalida. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    #Control de errores de bloque IF
    @_('IF condicion_parentesis bloque_ejecutable bloque_else error')
    def cuerpo_sentencia_ejecutable(self, p):
        self.reportar_error(f"Error sintactico: multiples sentencias deben ir entre 'BEGIN' y 'END'. Revisar falta de 'END_IF' para linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    # Falta de while, condicion o delimitadores de bloque de sentencias
    @_('REPEAT bloque_ejecutable error')
    def cuerpo_sentencia_ejecutable(self, p):
        self.reportar_error(f"Error sintactico: revisar estructura 'REPEAT...WHILE'. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)
    
    @_('ELSE error')
    def bloque_else(self, p):
        self.reportar_error(f"Error sintactico: bloque 'ELSE' invalido. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)

    
if __name__ == '__main__':
        print("AVISO: LA COMPILACION SE REALIZA DE ARRIBA HACIA ABAJO, SE RECOMIENDA TRATAR PRIMERO LOS ERRORES DE ARRIBA DEL TODO.")

        if len(sys.argv) < 2:
            print("Error: Falta el archivo de entrada.")
            sys.exit(1)

        nombre_archivo = sys.argv[1]

        try:
            with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
                data = archivo.read()
                
            lexer = analizador_lexico()
            parser = analizador_sintactico()
                
            tokens = lexer.tokenize(data)

            parser.ts = lexer.ts 
            
            arbol = parser.parse(tokens)
                
            print("-" * 65)
            
            total_errores = lexer.errores + parser.errores
            
            if total_errores == 0:
                print("Se ha compilado exitosamente.")
                
            #parser.ts.imprimir()
        
            #pprint(arbol, indent=2, width=80)
                
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo '{nombre_archivo}'.")