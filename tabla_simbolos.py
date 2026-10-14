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
        print("\n" + "=" * 90)
        print(" " * 30 + "TABLA DE SÍMBOLOS")
        print("=" * 90)

        # Encabezados
        columnas = ("TOKEN", "LEXEMA", "ATRIBUTOS")

        # Extraer los datos de la tabla de símbolos
        filas = []

        for simbolo, datos in self.tabla.items():
            token = datos.get("token", "")
            lexema = datos.get("lexema", "")

            # Obtener los atributos adicionales, excluyendo token y lexema
            atributos = {
                clave: valor
                for clave, valor in datos.items()
                if clave not in ("token", "lexema")
            }

            # Mostrar los atributos en una sola columna
            texto_atributos = (
                ", ".join(f"{clave}: {valor}" for clave, valor in atributos.items())
                if atributos
                else "—"
            )

            filas.append((token, lexema, texto_atributos))

        # Calcular el ancho necesario para cada columna
        anchos = [
            max(len(columnas[i]), *(len(fila[i]) for fila in filas))
            for i in range(len(columnas))
        ]

        # Dibujar los bordes de la tabla
        def borde(izquierda, union, derecha, horizontal="─"):
            return (
                izquierda
                + union.join(horizontal * (ancho + 2) for ancho in anchos)
                + derecha
            )

        def imprimir_fila(fila):
            print(
                "│"
                + "│".join(
                    f" {valor:<{ancho}} "
                    for valor, ancho in zip(fila, anchos)
                )
                + "│"
            )

        print(borde("┌", "┬", "┐"))
        imprimir_fila(columnas)
        print(borde("├", "┼", "┤"))

        for fila in filas:
            imprimir_fila(fila)

        print(borde("└", "┴", "┘"))
        print(f"Total de símbolos: {len(filas)}")
