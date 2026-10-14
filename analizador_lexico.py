import sys
import json
from sly import Lexer, Parser
from pprint import pprint
from tabla_simbolos import TablaSimbolos

# =========================================================================
# ANALIZADOR LÉXICO
# =========================================================================

class analizador_lexico(Lexer):

    def __init__(self):
        super().__init__()
        self.ts = TablaSimbolos()
        self.errores = 0
    
    def reportar_error(self, mensaje):
        print(mensaje)
        self.errores += 1

    tokens = {ID, CTE_USHORTINT, CTE_DOUBLEF, CADENA,
    ASIGNACION_PUNTO, ASIGNACION_IGUAL, IGUAL, DISTINTO, MAYOR_IGUAL, MENOR_IGUAL, 
    MAYOR, MENOR, MAS, MENOS, MULT, DIV, 
    IF, ELSE, END_IF, BEGIN, END,
    POUT, RET, CLASS, FUNCTION, USHORTINT, DOUBLEF, 
    TODF, TYPEDEF, REPEAT, WHILE, EXTENDS
    }

    literals = {'(', ')', ',', ';', '[', ']','.'}

    ignore = ' \t'

    @_(r'\{\{[\s\S]*?\}\}')
    def ignore_comentario(self, t):
        self.lineno += t.value.count('\n')

    @_(r'\n+')
    def ignore_salto_linea(self, t):
        self.lineno += len(t.value)
        self.es_inicio = False

    ASIGNACION_PUNTO = r':='
    IGUAL            = r'==' 
    DISTINTO         = r'!='
    MAYOR_IGUAL      = r'>='
    MENOR_IGUAL      = r'<='
    ASIGNACION_IGUAL = r'='
    MAYOR            = r'>'
    MENOR            = r'<'
    MAS              = r'\+'
    MENOS            = r'-'
    MULT             = r'\*'
    DIV              = r'/'

    @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    def ID(self, t):
        pr = {
            'if': 'IF', 'else': 'ELSE', 'end_if': 'END_IF',
            'begin': 'BEGIN', 'end': 'END', 'pout': 'POUT',
            'ret': 'RET', 'class': 'CLASS', 'function': 'FUNCTION',
            'ushortint': 'USHORTINT', 'doublef': 'DOUBLEF',
            'todf': 'TODF', 'typedef': 'TYPEDEF', 'repeat': 'REPEAT',
            'while': 'WHILE', 'extends': 'EXTENDS'
        }

        lexema = t.value.lower()

        if lexema in pr:
            t.type = pr[lexema]
            return t

        if t.value != lexema:
            self.reportar_error(f"Error Lexico: Identificador invalido en linea {self.lineno}. Debe ser en minusculas.")
            return None

        if len(t.value) > 22:
            # Los warnings no usan reportar_error para no hacer fallar la compilacion final
            print(f"WARNING: Se trunco el identificador en linea {self.lineno}. Maximo 22 caracteres.")
            t.value = t.value[:22]

        self.ts.insertar(t.value, "ID")
        t.value = self.ts.obtener(t.value, "ID")
        return t

    @_(r"'[^'\n]*'")
    def CADENA(self, t):
        longitud = len(t.value) - 2
        self.ts.insertar(t.value, "CADENA", longitud=longitud)
        t.value = self.ts.obtener(t.value, "CADENA")
        return t

    @_(r'\d*\.\d+(?:d[+-]?\d+)?')
    def CTE_DOUBLEF(self, t):
        val_str = t.value.replace('d', 'e')
        try:
            val = float(val_str)
            if (val == 0.0) or (2.2250738585072014e-308 <= val <= 1.7976931348623157e+308):
                self.ts.insertar(t.value, "CTE_DOUBLEF", valor=val)
                t.value = self.ts.obtener(t.value, "CTE_DOUBLEF")
                return t
            else:
                self.reportar_error(f"Error Léxico: DOUBLEF fuera de rango en línea {self.lineno}")
                return None
        except ValueError:
            self.reportar_error(f"Error Léxico: DOUBLEF inválido en línea {self.lineno}")
            return None

    @_(r'\d+\$us')
    def CTE_USHORTINT(self, t):
        val = int(t.value[:-3]) 
        if 0 <= val <= 255:
            self.ts.insertar(t.value, "CTE_USHORTINT", valor=val)
            t.value = self.ts.obtener(t.value, "CTE_USHORTINT")
            return t
        else:
            self.reportar_error(f"Error Léxico: USHORTINT fuera de rango ({t.value}) en línea {self.lineno}")
            return None

    def error(self, t):
        self.reportar_error(f"Error Lexico: Caracter no reconocido '{t.value[0]}' en la linea {self.lineno}")
        self.index +=1

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Error: Falta el archivo de entrada.")
        sys.exit(1)

    nombre_archivo = sys.argv[1]

    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            data = archivo.read()
        
        lexer = analizador_lexico()

        for tok in lexer.tokenize(data):
            if isinstance(tok.value, dict):
                valor_imprimir = tok.value.get("lexema", str(tok.value))
            else:
                valor_imprimir = tok.value
                        
        if lexer.errores == 0:
            print("Se ha compilado exitosamente.")
        
        lexer.ts.imprimir()

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{nombre_archivo}'.")