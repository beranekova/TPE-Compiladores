from sly import Lexer
import sys
from tabla_simbolos import TablaSimbolos

class analizador_lexico(Lexer):

    def __init__(self):
        super().__init__()
        self.ts = TablaSimbolos()

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
            print(f"Error Lexico: Identificador invalido'{t.value}'. Debe ser en minusculas. Línea {self.lineno}")
            return None

        if len(t.value) > 22:
            print(f"WARNING: Se trunco el identificador '{t.value}'. Debe tener maximo 22 caracteres. Línea {self.lineno}")
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
            if val == 0.0 or (2.2250738585072014e-308 <= val <= 1.7976931348623157e+308):
                self.ts.insertar(t.value, "CTE_DOUBLEF", valor=val)
                t.value = self.ts.obtener(t.value, "CTE_DOUBLEF")
                return t
            else:
                print(f"Error Léxico: DOUBLEF fuera de rango en línea {self.lineno}")
                return None
        except ValueError:
            print(f"Error Léxico: DOUBLEF inválido en línea {self.lineno}")
            return None
    
    @_(r'\d+\$us')
    def CTE_USHORTINT(self, t):
        val = int(t.value[:-3]) 
        if 0 <= val <= 255:
            self.ts.insertar(t.value, "CTE_USHORTINT", valor=val)
            t.value = self.ts.obtener(t.value, "CTE_USHORTINT")
            return t
        else:
            print(f"Error Léxico: USHORTINT fuera de rango ({t.value}) en línea {self.lineno}")
            return None

    def error(self, t):
        print(f"Error Lexico: Caracter no reconocido '{t.value[0]}' en la linea {self.lineno}")
        self.index +=1


if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        print("Error: Falta el archivo de entrada.")
        print("Uso: python3 analizador_lexico.py <ruta_del_archivo.txt>")
        sys.exit(1)

    nombre_archivo = sys.argv[1]

    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            data = archivo.read()
        
        lexer = analizador_lexico()

        print(f"\n--- INICIANDO ANÁLISIS LÉXICO: {nombre_archivo} ---")
        print("-" * 60)
        print(f"{'TOKEN':<18} | {'LEXEMA':<28} | {'LÍNEA'}")
        print("-" * 60)

        for tok in lexer.tokenize(data):
            # Extraemos el string del diccionario para una impresión limpia en consola
            if isinstance(tok.value, dict):
                valor_imprimir = tok.value.get("lexema", str(tok.value))
            else:
                valor_imprimir = tok.value
                
            print(f"{tok.type:<18} | {str(valor_imprimir)!r:<28} | {tok.lineno}")

        print("-" * 60)
        
        # Imprimimos la Tabla de Símbolos
        lexer.ts.imprimir()

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{nombre_archivo}'.")