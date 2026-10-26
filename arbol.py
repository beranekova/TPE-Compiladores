class NodoArbol:
    def __init__(self, valor, izquierdo=None, derecho=None, tipo=None):
        self.valor = valor          # Operador o instrucción (ej: '+', ':=', 'repeat_while')
        self.izquierdo = izquierdo  # Hijo izquierdo / Subárbol
        self.derecho = derecho      # Hijo derecho / Subárbol / Lista de nodos
        self.tipo = tipo            # Tipo de la expresión resultante (INT, DOUBLE, etc.)

    def imprimir(self, nivel=0):
        # Método para cumplir con el requisito de visualización de la consigna
        indentacion = "  " * nivel
        print(f"{indentacion}{self.valor} (Tipo: {self.tipo})")
        if self.izquierdo:
            self.izquierdo.imprimir(nivel + 1)
        if self.derecho:
            self.derecho.imprimir(nivel + 1)