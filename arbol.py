class NodoArbol:
    def __init__(self, valor, izquierdo=None, derecho=None, tipo=None, uso=None):
        self.valor = valor          # Operador o instrucción (ej: '+', ':=', 'repeat_while')
        self.izquierdo = izquierdo  # Hijo izquierdo / Subárbol
        self.derecho = derecho      # Hijo derecho / Subárbol / Lista de nodos
        self.tipo = tipo            # Tipo de la expresión resultante (INT, DOUBLE, etc.)
        self.uso = uso              # guardamos el uso en el arbol ademas, para que los nodos padres validen las expresiones


    def imprimir(self, nivel=0):
        indentacion = "  " * nivel
        print(f"{indentacion}{self.valor} (Tipo: {self.tipo}, Uso: {self.uso})")

        self._imprimir_hijo(self.izquierdo, nivel + 1)
        self._imprimir_hijo(self.derecho, nivel + 1)

    def _imprimir_hijo(self, hijo, nivel):
        if hijo is None:
            return
            
        indentacion = "  " * nivel

        if isinstance(hijo, NodoArbol):
            hijo.imprimir(nivel)
        elif isinstance(hijo, (list, tuple)):
            for elem in hijo:
                self._imprimir_hijo(elem, nivel)
        else:
            print(f"{indentacion}{hijo}")

    def __repr__(self):
        if self.izquierdo or self.derecho:
            return f"Nodo({self.valor}, izq={repr(self.izquierdo)}, der={repr(self.derecho)})"
        return f"Hoja({self.valor}, tipo={self.tipo})"