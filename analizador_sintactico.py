import sys
import json
from sly import Parser
from pprint import pprint
from analizador_lexico import analizador_lexico

class analizador_sintactico(Parser):

    tokens = analizador_lexico.tokens

    debugfile = 'parser.out'

    precedence = (
        ('right', 'ASIGNACION_IGUAL'),
        ('left', 'MAS', 'MENOS'),
        ('left', 'MULT', 'DIV'),
        ('right', 'UMINUS'),
    )

    #DECLARACION DE PROGRAMA

    @_('ID sentencias_declarativas BEGIN sentencias_ejecutables END')
    def programa(self, p):
        return p

    #-----------------------// SENTENCIAS DECLARATIVAS //-----------------------

    @_('sentencias_declarativas sentencia_declarativa')
    def sentencias_declarativas(self, p):
        return p

    @_('')
    def sentencias_declarativas(self,p):
        return []
    
    @_('cuerpo_declaracion ";"')
    def sentencia_declarativa(self, p):
        return p.cuerpo_declaracion
    
    @_('declaracion_variables',
       'tipo FUNCTION ID "(" parametros_formales ")" sentencias_declarativas BEGIN sentencias_ejecutables_funcion END',
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
    
    @_('tipo ID',
       '')
    def parametros_formales(self, p):
        return [{
            "tipo": f"lista de parametros de tipo: {p.tipo}",
            "id": p.ID
        }]

    @_('parametros_formales "," tipo ID')
    def parametros_formales(self, p):
        return p.parametros_formales + [{
            "tipo": f"lista de parametros de tipo: {p.tipo}",
            "id": p.ID
        }]

    @_('sentencias_ejecutables_funcion sentencia_ejecutable_funcion')
    #1 o mas sentencias ejecutables dentro de una funcion
    def sentencias_ejecutables_funcion(self,p):
        return p

    @_('')
    #0 o para terminar de detectar sentencias ejecutables dentro de una funcion
    def sentencias_ejecutables_funcion(self, p):
        return []

    @_('sentencia_ejecutable')
    def sentencia_ejecutable_funcion(self, p):
        return p
    
    @_('RET retorno')
    def cuerpo_retorno(self, p):
        return p
        
    @_('cuerpo_retorno ";"')
    def sentencia_ejecutable_funcion(self, p):
        return p.cuerpo_retorno

    @_('expresion')
    def retorno(self, p):
        return p

    #DECLARACION DE CLASES
    
    @_('declaracion_clase elemento_clase',
       '')
    def declaracion_clase(self, p):
        return p

    @_('EXTENDS lista_variables',
       'declaracion_variables',
       'declaracion_metodo')
    def cuerpo_elemento_clase(self, p):
        return p[0]

    @_('cuerpo_elemento_clase ";"')
    def elemento_clase(self, p):
        return p

    @_('tipo ID "(" parametros_formales ")" BEGIN sentencias_ejecutables_funcion END')
    def declaracion_metodo(self, p):
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

    @_('sentencias_ejecutables sentencia_ejecutable')
    def sentencias_ejecutables(self, p):
        return p
        
    @_('')
    def sentencias_ejecutables(self, p):
        return []
    
    @_('cuerpo_sentencia_ejecutable ";"')
    def sentencia_ejecutable(self, p):
        return p.cuerpo_sentencia_ejecutable

    #----------------DEFINICION DE ASIGNACIONES
    
    @_('lado_izquierdo ASIGNACION_PUNTO expresion')
    def asignacion_punto(self, p):
        return p

    @_('lado_izquierdo ASIGNACION_IGUAL expresion')
    def asignacion_igual(self, p):
        return p

    @_('lado_izquierdo ASIGNACION_IGUAL expresion')
    def asignacion_inline(self, p):
        return p
    
    #definir estrictamente si permitimos esto en el sintactico pero en el semantico se verifica que no es posible
    #llamar una funcion desde un atributo posicional o no permitirlo de una aca en el sintactico
    @_('ID',
       'ID "." ID',
       'ID "[" CTE_USHORTINT "]"')
    def lado_izquierdo(self, p):
        return p
    
    @_('asignacion_punto', 
       'asignacion_igual',
       'llamado_funcion',
       'IF condicion_parentesis bloque_sentencias bloque_else END_IF',
       'POUT "(" expresion ")"',
       'REPEAT bloque_sentencias WHILE condicion_parentesis')
    def cuerpo_sentencia_ejecutable(self, p):
        return p[0]
    
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
    
    @_('ELSE bloque_sentencias')
    def bloque_else(self, p):
        return p

    @_('')
    def bloque_else(self, p):
        return []

    @_('BEGIN sentencias_ejecutables END')
    def bloque_sentencias(self, p):
        return p

    @_('sentencia_ejecutable')
    def bloque_sentencias(self, p):
        return p
        
    # ---------------- EXPRESIONES ARITMETICAS ----------------

    @_('expresion MAS expresion')
    def expresion(self, p):
        return ('SUMA', p.expresion0, p.expresion1)

    @_('expresion MENOS expresion')
    def expresion(self, p):
        return ('RESTA', p.expresion0, p.expresion1)

    @_('expresion MULT expresion')
    def expresion(self, p):
        return ('MULT', p.expresion0, p.expresion1)

    @_('expresion DIV expresion')
    def expresion(self, p):
        return ('DIV', p.expresion0, p.expresion1)

    @_('TODF "(" expresion ")"')
    def expresion(self, p):
        return ('TODF', p.expresion)

    @_('lado_izquierdo',
       'asignacion_inline',
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
    
    @_('lista_orden "," CTE_USHORTINT')
    def lista_orden(self, p):
        return p.lista_orden + [p.CTE_USHORTINT]

    @_('CTE_USHORTINT')
    def lista_orden(self, p):
        return [p.CTE_USHORTINT]

    @_('')
    def orden_parametros(self, p):
        return p

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

    #-----------------------// FIN DE SENTENCIAS EJECUTABLES //-----------------------

    #-----------------------// RECUPERACIÓN DE ERRORES //-----------------------

    @_('POUT "(" error ")"')
    def cuerpo_sentencia_ejecutable(self, p):
        print(f"Error: falta argumento de salida en pout en linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)

    @_('cuerpo_declaracion error')
    def sentencia_declarativa(self, p):
        print(f"Error: falta ; en declaracion de linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)

    @_('cuerpo_sentencia_ejecutable error')
    def sentencia_ejecutable(self, p):
        print(f"Error: falta ; en sentencia de linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)
    
    @_('cuerpo_elemento_clase error')
    def elemento_clase(self, p):
        print(f"Error: falta ; en elemento de clase de linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)
    
    @_('cuerpo_retorno error')
    def sentencia_ejecutable_funcion(self, p):
        print(f"Error: falta ; en retorno (ret) de linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)
    
    @_('error bloque_sentencias WHILE condicion_parentesis')
    def cuerpo_sentencia_ejecutable(self, p):
        print(f"Error: falta REPEAT en iteracion de linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)

    @_('REPEAT bloque_sentencias error condicion_parentesis')
    def cuerpo_sentencia_ejecutable(self, p):
        print(f"Error: falta WHILE en iteracion de linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)

    @_('TYPEDEF ID ASIGNACION_IGUAL "[" "]"')
    def cuerpo_declaracion(self, p):
        print(f"Error: ausencia de valores para ENUMERADO en linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)

    @_('EXTENDS error')
    def cuerpo_elemento_clase(self, p):
        print(f"Error: ausencia de clases en EXTENDS en linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)

    @_('asignacion_punto')
    def asignacion_inline(self, p):
        print(f"Error: usa := donde va = en asignacion de linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)
    
    @_('IF condicion_parentesis bloque_sentencias bloque_else error')
    def cuerpo_sentencia_ejecutable(self, p):
        print(f"Error: falta end_if en estructura IF de linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)

    @_('error condicion ")"')
    def condicion_parentesis(self, p):
        print(f"Error: falta '(' en condicion de linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)

    @_('"(" condicion error')
    def condicion_parentesis(self, p):
        print(f"Error: falta ')' en condicion de linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)

    @_('tipo FUNCTION error "(" parametros_formales ")" sentencias_declarativas BEGIN sentencias_ejecutables_funcion END')
    def cuerpo_declaracion(self, p):
        print(f"Error: falta nombre de funcion en linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)

    @_('error sentencias_declarativas BEGIN sentencias_ejecutables END')
    def programa(self, p):
        print(f"Error: falta nombre del programa al inicio.")
        return ('ERROR_RECUPERADO',)
    
    @_('lista_variables error ID')
    def lista_variables(self, p):
        print(f"Error: falta ',' para separar variables en linea {p.lineno}.")
        return p.lista_variables + [p.ID]

    @_('tipo error')
    def parametros_formales(self, p):
        print(f"Error: falta nombre del parametro formal en linea {p.lineno}.")
        return [{"tipo": f"lista de parametros de tipo: {p.tipo}", "id": "ERROR"}]

    @_('error ID')
    def parametros_formales(self, p):
        print(f"Error: falta tipo del parametro formal '{p.ID}' en linea {p.lineno}.")
        return [{"tipo": "ERROR", "id": p.ID}]

    @_('REPEAT error WHILE condicion_parentesis')
    def cuerpo_sentencia_ejecutable(self, p):
        print(f"Error: falta cuerpo en iteracion de linea {p.lineno}.")
        return ('ERROR_RECUPERADO',)

    @_('ID sentencias_declarativas error sentencias_ejecutables END')
    def programa(self, p):
        print(f"Error: falta BEGIN del programa.")
        return ('ERROR_RECUPERADO',)

    @_('ID sentencias_declarativas BEGIN sentencias_ejecutables error')
    def programa(self, p):
        print(f"Error: falta END de fin de programa.")
        return ('ERROR_RECUPERADO',)

    @_('error ";"')
    def sentencia_ejecutable(self, p):
        print(f"Error: error general, linea {p.lineno} omitida.")
        return ('ERROR_RECUPERADO',)

    def error(self, p):
        if not p:
            print("Error: Fin de archivo inesperado.")
            return
        pass

    # comentario del tipo p
    # p.CTE_DOUBLEF = referencia a la ts
    # cada objeto p contiene como atributo cada parte de la regla que lo compone
    # por ejemplo, la regla @_('MENOS CTE_DOUBLEF %prec UMINUS')
    # hace que sly cree un objeto p con p.MENOS y p.CTE_DOUBLEF (lo demas no porque no son tokens)

if __name__ == '__main__':
    
    lexer = analizador_lexico()
    parser = analizador_sintactico()
        
    if len(sys.argv) > 1:
        nombre_archivo = sys.argv[1]
        try:
            with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
                data = archivo.read()
                
            print(f"\n Analisis Sintactico ")

            # esto funciona como el yylex() ya que internamente va consumiendo tokens a medida que los pide el parser
            # usa metodo next() por debajo para consumir tokens del lexer

            tokens = lexer.tokenize(data)
            
            parser.ts = lexer.ts 
            
            arbol = parser.parse(tokens)
                
            # print(f"\n Arbol de Sintaxis (AST)")
            # pprint(arbol, indent=2, width=100)
            
            # parser.ts.imprimir()
                
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo '{nombre_archivo}'.")