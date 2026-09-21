import json

class TablaSimbolos:
    def __init__(self):
        self.tabla = {}

    def _generar_clave(self, token, lexema):
        return f"<{token}, {lexema}>"

    def insertar(self, lexema, token, valor=None, longitud=None):
        clave = self._generar_clave(token, lexema)
        if clave not in self.tabla:
            entrada = {
                "token": token,
                "lexema": lexema
            }
            if valor is not None:
                entrada["valor"] = valor
            if longitud is not None:
                entrada["longitud"] = longitud
                
            self.tabla[clave] = entrada

    def eliminar(self, lexema, token):
        clave = self._generar_clave(token, lexema)
        if clave in self.tabla:
            del self.tabla[clave]
            
    def obtener(self, lexema, token):
        clave = self._generar_clave(token, lexema)
        return self.tabla.get(clave, None)

    def imprimir(self):
        print("\n" + "="*40)
        print("          TABLA DE SÍMBOLOS")
        print("="*40)
        print(json.dumps(self.tabla, indent=4))