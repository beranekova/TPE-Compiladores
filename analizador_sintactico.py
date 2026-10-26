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
       'TYPEDEF ID ASIGNACION_IGUAL "[" lista_valores "]"',
       'CLASS ID BEGIN declaracion_clase END')
    def cuerpo_declaracion(self, p):
        return p[0]
    
    @_('tipo lista_variables',
       'ID lista_variables')
    def declaracion_variables(self, p):
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
        return p

    @_('tipo FUNCTION ID "(" parametros_formales ")" sentencias_declarativas')
    def firma_funcion(self, p):
        return p
    
    @_('BEGIN sentencias_ejecutables_funcion END')
    def cuerpo_funcion(self, p):
        return p

    @_('lista_parametros',
       '')
    def parametros_formales(self, p):
        return p

    @_('tipo ID')
    def lista_parametros(self, p):
        return p

    @_('lista_parametros "," tipo ID')
    def lista_parametros(self, p):
        return p

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
        return p
    
    @_('tipo ID "(" parametros_formales ")"')
    def firma_metodo(self, p):
        return p
    
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
    
    @_('ID',
       'ID "." ID',
       'ID "[" CTE_USHORTINT "]"')
    def lado_izquierdo(self, p):
        return p
    
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

    @_('expresion MAS expresion',
       'expresion MENOS expresion',
       'expresion MULT expresion',
       'expresion DIV expresion')
    def expresion(self, p):
        return self._procesar_operacion_binaria(p[1], p.expresion0, p.expresion1, p.lineno)

    @_('expresion MENOS expresion')
    def expresion(self, p):
        return self._procesar_operacion_binaria(MENOS, p.expresion0, p.expresion1, p.lineno)

    @_('expresion MULT expresion')
    def expresion(self, p):
        return self._procesar_operacion_binaria(MULT, p.expresion0, p.expresion1, p.lineno)

    @_('expresion DIV expresion')
    def expresion(self, p):
        return self._procesar_operacion_binaria(DIV, p.expresion0, p.expresion1, p.lineno)

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