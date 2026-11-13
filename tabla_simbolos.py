import json

class TablaSimbolos:
    def __init__(self):
        self.tabla = {}
        # Pila de ámbitos para saber en qué alcance estamos actualmente
        self.pila_ambitos = ["main"]

    def obtener_ambito_actual(self):
        # Genera la cadena del ámbito actual concatenando la pila (ej: "main:funcion1")
        return ":".join(self.pila_ambitos)

    def abrir_ambito(self, nombre_ambito):
        self.pila_ambitos.append(nombre_ambito)

    def cerrar_ambito(self):
        if len(self.pila_ambitos) > 1:
            self.pila_ambitos.pop()

    def _generar_clave(self, lexema, alcance=None):
        if alcance:
            return f"{lexema}:{alcance}"
        return lexema

    def insertar(self, lexema, token, tipo=None, uso=None, valor=None, longitud=None, alcance=None, **kwargs):
        # Si no se provee alcance de forma explícita, usamos el ámbito actual
        alcance_efectivo = alcance if alcance is not None else self.obtener_ambito_actual()
        clave = self._generar_clave(lexema, alcance_efectivo)

        if clave not in self.tabla:
            entrada = {
                "token": token,
                "lexema": lexema,
                "tipo": tipo,
                "uso": uso,            # 'variable', 'funcion', 'parametro', 'constante', etc.
                "alcance": alcance_efectivo
            }

            # Agrega cualquier atributo extra pasado (parametros, valores_enum, extend, valor, longitud, etc)
            entrada.update(kwargs);
                
            self.tabla[clave] = entrada
            return True  # Inserción exitosa
        else:
            # Si la clave ya existe en el MISMO ámbito, es un error de redeclaración
            return False

    def buscar(self, lexema):
        """
        Busca un símbolo desde el ámbito más interno hacia el más externo (regla de visibilidad).
        """
        # Recorremos la pila de ámbitos de atrás hacia adelante
        for i in range(len(self.pila_ambitos), 0, -1):
            alcance_parcial = ":".join(self.pila_ambitos[:i])
            clave = self._generar_clave(lexema, alcance_parcial)
            if clave in self.tabla:
                return self.tabla[clave]
        return None

    def eliminar(self, lexema, alcance=None):
        clave = self._generar_clave(lexema, alcance)
        if clave in self.tabla:
            del self.tabla[clave]
            
    def obtener(self, lexema, alcance=None):
        clave = self._generar_clave(lexema, alcance)
        return self.tabla.get(clave, None)


    def imprimir(self):
        print("\n" + "=" * 110)
        print(" " * 40 + "TABLA DE SÍMBOLOS")
        print("=" * 110)

        columnas = ("TOKEN", "LEXEMA", "TIPO", "USO", "ALCANCE", "EXTRA")

        filas = []

        for simbolo, datos in self.tabla.items():
            token = datos.get("token", "")
            lexema = datos.get("lexema", "")
            tipo = datos.get("tipo", "")
            uso = datos.get("uso", "")
            alcance = datos.get("alcance", "")

            # Reunir todos los atributos adicionales en EXTRA
            atributos_extra = {
                clave: valor
                for clave, valor in datos.items()
                if clave not in ("token", "lexema", "tipo", "uso", "alcance")
                and valor is not None
            }

            texto_extra = (
                ", ".join(f"{clave}: {valor}" for clave, valor in atributos_extra.items())
                if atributos_extra
                else "—"
            )

            filas.append((
                str(token),
                str(lexema),
                str(tipo),
                str(uso),
                str(alcance),
                texto_extra
            ))

        # Calcular el ancho necesario para cada columna
        anchos = [
            max(len(columnas[i]), *(len(fila[i]) for fila in filas))
            for i in range(len(columnas))
        ]

        # Dibujar los bordes
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


#tipo: puede ser USHORTINT, DOUBLEF, un enumerado o clase declarada por el usuario
#uso: puede ser parametro, variable, clase, metodo, funcion
#valor:
#longitud:
#alcance: en que ambitos se puede usar ese ID declarado