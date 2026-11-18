import sys
import json
from sly import Lexer, Parser
from pprint import pprint
from tabla_simbolos import TablaSimbolos
from analizador_lexico import analizador_lexico
from arbol import NodoArbol
from generador_assembler import generador_assembler

class analizador_sintactico(Parser):

    def __init__(self):
        super().__init__()
        self.tabla = TablaSimbolos()
        self.errores = 0
        self.errores_emitidos = set()
        self.warnings_emitidos = set()
    
    def reportar_error(self, mensaje, linea=None):
        if linea is not None and f"Linea {linea}" not in str(mensaje):
            mensaje_final = f"{mensaje}. Linea {linea}"
        else:
            mensaje_final = str(mensaje)
        #verificamos si la linea y el error ya se registro anteriormente
        if mensaje_final in self.errores_emitidos:
            return
        self.errores_emitidos.add(mensaje_final)
        print(mensaje_final)
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
        self.verificar_uso_variables()
        return NodoArbol(
            valor=f"PROGRAMA:{p.ID}",
            izquierdo=NodoArbol(valor="DECLARACIONES", derecho=p.sentencias_declarativas),
            derecho=NodoArbol(valor="EJECUTABLES", derecho=p.cuerpo_programa)
        )

    #-----------------------// SENTENCIAS DECLARATIVAS //-----------------------

    #Declaracion de una o mas sentencias
    @_('sentencias_declarativas sentencia_declarativa')
    def sentencias_declarativas(self, p):
        return p.sentencias_declarativas + [p.sentencia_declarativa]

    @_('BEGIN sentencias_ejecutables END')
    def cuerpo_programa(self, p):
        return p.sentencias_ejecutables

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

    @_('cabecera_clase BEGIN declaracion_clase clausula_extends END')
    def declaracion_de_clase_completa(self, p):
        nombre_clase = p.cabecera_clase
        padres_crudos = p.clausula_extends 
        ambito_clase = self.tabla.obtener_ambito_actual()
        
        atributos_ordenados = []
        for clave, datos in self.tabla.tabla.items():
            if datos.get("alcance") == ambito_clase and datos.get("uso") == "variable":
                atributos_ordenados.append(datos["lexema"])  # <-- Mantenemos lexema (nombres)
                
        simbolo_clase = self.tabla.buscar(nombre_clase)
        
        if simbolo_clase:
            padres_validos = []
            for padre in padres_crudos:
                simbolo_padre = self.tabla.buscar(padre)
                if not simbolo_padre or simbolo_padre.get("uso") != "clase":
                    self.reportar_error(f"Error semantico: La clase padre '{padre}' no esta declarada", p.lineno)
                else:
                    padres_validos.append(padre)
            
            simbolo_clase["herencia"] = padres_validos
            simbolo_clase["atributos"] = atributos_ordenados
            
        self.tabla.cerrar_ambito()
        metodos = [elem for elem in p.declaracion_clase if elem is not None]
        return metodos if metodos else None
    
    @_('tipo lista_variables')
    def declaracion_variables(self, p):
        tipo_var = p.tipo

        #aca no verificamos si el tipo existe ya que es un tipo nativo que existe predefinido en la tabla de simbolos
        for identificador in p.lista_variables:
            exito = self.tabla.insertar(
                identificador, 
                'ID', 
                tipo=tipo_var, 
                uso='variable',
                leida=False,
                escrita=False,
                linea=p.lineno
            )

            if not exito:
                self.reportar_error(f"Error semantico: la variable '{identificador}' ya fue declarada en este ambito. Linea {p.lineno}")
        return None
    
    @_('ID lista_variables')
    def declaracion_variables(self, p):
        tipo_custom = p.ID 
        
        #primero verificamos que el tipo del enumerado o clase exista en al tabla
        simbolo_tipo = self.tabla.buscar(tipo_custom)
        if not simbolo_tipo or simbolo_tipo.get('uso') not in ['clase', 'enumeracion']:
            self.reportar_error(f"Error semantico: el tipo '{tipo_custom}' no esta declarado o no es valido. Linea {p.lineno}")
        
        es_escrita = (simbolo_tipo is not None and simbolo_tipo.get('uso') == 'clase')

        #si existe, nos fijamos si esta redeclarada o no la variable
        for identificador in p.lista_variables:
            exito = self.tabla.insertar(
                identificador, 
                'ID', 
                tipo=tipo_custom, 
                uso='variable',
                leida=False,
                escrita=es_escrita,
                linea=p.lineno
            )
            if not exito:
                self.reportar_error(f"Error semantico: la variable '{identificador}' ya fue declarada. Linea {p.lineno}")
        return None

    @_('USHORTINT', 
      'DOUBLEF')
    def tipo(self, p):
        return p[0].upper()

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
        if isinstance(p.firma_funcion, NodoArbol):
            nombre_func = p.firma_funcion.valor.replace("FIRMA:", "")
        else:
            nombre_func = str(p.firma_funcion)
        cuerpo_final = self._asegurar_retorno_en_cuerpo(nombre_func, p.cuerpo_funcion, p.lineno)
        self.tabla.cerrar_ambito()
        return NodoArbol(
            valor="DECL_FUNCION",
            izquierdo=p.firma_funcion,
            derecho=cuerpo_final
        )

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
        nombre_func = p.cabecera_funcion
        lista_params = p.parametros_formales  # Lista de dicts: [{'nombre': 'a', 'tipo': 'USHORTINT'}, ...]
        
        simbolo_func = self.tabla.buscar(nombre_func)
        if simbolo_func:
            simbolo_func["parametros"] = lista_params

        # Convertimos cada diccionario en un NodoArbol homogéneo
        nodos_params = [
            NodoArbol(
                valor=param['nombre'],
                tipo=param['tipo'],
                uso="parametro"
            )
            for param in (lista_params or [])
        ]
            
        return NodoArbol(
            valor=f"FIRMA:{nombre_func}",
            izquierdo=nodos_params if nodos_params else None,
            derecho=p.sentencias_declarativas
        )
    
    @_('BEGIN sentencias_ejecutables_funcion END')
    def cuerpo_funcion(self, p):
        return p.sentencias_ejecutables_funcion

    @_('lista_parametros')
    def parametros_formales(self, p):
        return p.lista_parametros
    
    @_('')
    def parametros_formales(self, p):
        return []

    @_('tipo ID')
    def lista_parametros(self, p):
        exito = self.tabla.insertar(
            p.ID, 
            'ID', 
            tipo=p.tipo, 
            uso='parametro',
            leida=False,
            escrita=True,
            linea=p.lineno
        )
        if not exito:
            self.reportar_error(f"Error semantico: parametro '{p.ID}' redeclarado. Linea {p.lineno}")
        
        return [{'nombre': p.ID, 'tipo': p.tipo}]

    @_('lista_parametros "," tipo ID')
    def lista_parametros(self, p):
        exito = self.tabla.insertar(
            p.ID, 
            'ID', 
            tipo=p.tipo, 
            uso='parametro',
            leida=False,
            escrita=True,
            linea=p.lineno
        )
        if not exito:
            self.reportar_error(f"Error semantico: parametro '{p.ID}' redeclarado. Linea {p.lineno}")
        
        lista_acumulada = p.lista_parametros
        lista_acumulada.append({'nombre': p.ID, 'tipo': p.tipo})
        
        return lista_acumulada
    
    @_('sentencias_ejecutables_funcion sentencia_ejecutable_funcion')
    def sentencias_ejecutables_funcion(self, p):
        return p.sentencias_ejecutables_funcion + [p.sentencia_ejecutable_funcion]
    
    @_('')
    def sentencias_ejecutables_funcion(self, p):
        return []

    @_('sentencia_ejecutable')
    def sentencia_ejecutable_funcion(self, p):
        return p.sentencia_ejecutable
        
    @_('cuerpo_retorno ";"')
    def sentencia_ejecutable_funcion(self, p):
        return p.cuerpo_retorno

    @_('RET retorno')
    def cuerpo_retorno(self, p):
        return NodoArbol(valor="RET", izquierdo=p.retorno)

    @_('expresion')
    def retorno(self, p):
        return p.expresion

    #DECLARACION DE CLASES
    
    @_('declaracion_clase elemento_clase')
    def declaracion_clase(self, p):
        return p.declaracion_clase + [p.elemento_clase]

    @_('')
    def declaracion_clase(self, p):
        return []
    
    @_('cuerpo_elemento_clase ";"')
    def elemento_clase(self, p):
        return p.cuerpo_elemento_clase

    @_('declaracion_variables',
       'declaracion_metodo')
    def cuerpo_elemento_clase(self, p):
        return p[0]
    
    @_('EXTENDS lista_variables ";"')
    def clausula_extends(self, p):
        ambito_actual = self.tabla.obtener_ambito_actual()
        nombre_clase = ambito_actual.split(':')[-1]
        simbolo = self.tabla.buscar(nombre_clase)
        if simbolo:
            simbolo["herencia"] = p.lista_variables   
        return p.lista_variables
    
    @_('')
    def clausula_extends(self, p):
        return []

    @_('firma_metodo cuerpo_funcion')
    def declaracion_metodo(self, p):
        nombre_met = p.firma_metodo['nombre']
        cuerpo_final = self._asegurar_retorno_en_cuerpo(nombre_met, p.cuerpo_funcion, p.lineno)
        self.tabla.cerrar_ambito()
        return NodoArbol(
            valor=f"METODO:{nombre_met}",
            derecho=cuerpo_final
        )
    
    @_('cabecera_metodo "(" parametros_formales ")"')
    def firma_metodo(self, p):
        return {
            'nombre': p.cabecera_metodo,
            'parametros': p.parametros_formales
        }

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
        return p.lista_valores + [p[2]]

    @_('CTE_USHORTINT')
    def lista_valores(self, p):
        return [p[0]]

    #-----------------------// FIN DE SENTENCIAS DECLARATIVAS //-----------------------

    #-----------------------// SENTENCIAS EJECUTABLES //-----------------------

    #ESTRUCTURA DE SENTENCIAS EJECUTABLES
    @_('BEGIN sentencias_ejecutables END')
    def bloque_ejecutable(self, p):
        return p.sentencias_ejecutables
    
    @_('sentencia_ejecutable')
    def bloque_ejecutable(self, p):
        return p.sentencia_ejecutable
    
    @_('sentencias_ejecutables sentencia_ejecutable')
    def sentencias_ejecutables(self, p):
        return p.sentencias_ejecutables + [p.sentencia_ejecutable]

    @_('')
    def sentencias_ejecutables(self, p):
        return []
    
    @_('cuerpo_sentencia_ejecutable ";"')
    def sentencia_ejecutable(self, p):
        return p.cuerpo_sentencia_ejecutable
    
    @_('asignacion_punto',
       'llamado_funcion')
    def cuerpo_sentencia_ejecutable(self, p):
        return p[0]

    @_('POUT "(" expresion ")"')
    def cuerpo_sentencia_ejecutable(self, p):
        return NodoArbol(valor="POUT", izquierdo=p.expresion)

    @_('IF condicion_parentesis bloque_ejecutable bloque_else END_IF')
    def cuerpo_sentencia_ejecutable(self, p):
        nodo_condicion = p.condicion_parentesis
        nodo_then = p.bloque_ejecutable
        nodo_else = p.bloque_else

        nodo_ramas = NodoArbol(valor="CUERPO_IF", izquierdo=nodo_then, derecho=nodo_else)

        return NodoArbol(valor="IF", izquierdo=nodo_condicion, derecho=nodo_ramas)

    @_('REPEAT bloque_ejecutable WHILE condicion_parentesis')
    def cuerpo_sentencia_ejecutable(self, p):
        return NodoArbol(valor="REPEAT", izquierdo=p.bloque_ejecutable, derecho=p.condicion_parentesis)

    def _obtener_tipos_atributos(self, nombre_clase):
        simbolo_clase = self.tabla.buscar(nombre_clase)
        if not simbolo_clase or simbolo_clase.get("uso") != "clase":
            return []

        tipos = []
        # 1. Primero recolectamos en orden los tipos heredados de las clases padre
        for padre in simbolo_clase.get("herencia", []):
            tipos.extend(self._obtener_tipos_atributos(padre))

        # 2. Luego recolectamos los tipos de los atributos propios de esta clase
        alcance_clase = f"{simbolo_clase['alcance']}:{nombre_clase}"
        for nombre_attr in simbolo_clase.get("atributos", []):
            simb_attr = self.tabla.obtener(nombre_attr, alcance=alcance_clase)
            if simb_attr:
                tipos.append(simb_attr["tipo"])

        return tipos

    def _son_tipos_compatibles(self, tipo_izq, tipo_der):
        if tipo_izq == tipo_der or "ERROR" in [tipo_izq, tipo_der]:
            return True

        simbolo_izq = self.tabla.buscar(tipo_izq)

        if simbolo_izq and simbolo_izq.get("uso") == "enumeracion" and tipo_der == "USHORTINT":
            return True
        
        simbolo_der = self.tabla.buscar(tipo_der)

        if not simbolo_izq or not simbolo_der:
            return False
        if simbolo_izq.get("uso") != "clase" or simbolo_der.get("uso") != "clase":
            return False

        tipos_izq = self._obtener_tipos_atributos(tipo_izq)
        tipos_der = self._obtener_tipos_atributos(tipo_der)

        if len(tipos_izq) != len(tipos_der):
            return False
        
        for t_i, t_d in zip(tipos_izq, tipos_der):
            if not self._son_tipos_compatibles(t_i, t_d):
                return False

        return True
    
    @_('lado_izquierdo ASIGNACION_PUNTO expresion')
    def asignacion_punto(self, p):
        nodo_izq = p.lado_izquierdo
        nodo_der = p.expresion
        tipo_res = self._validar_asignacion(nodo_izq, nodo_der, ":=", p.lineno)
        return NodoArbol(valor=":=", izquierdo=nodo_izq, derecho=nodo_der, tipo=tipo_res)

    @_('lado_izquierdo ASIGNACION_IGUAL expresion')
    def asignacion_igual(self, p):
        nodo_izq = p.lado_izquierdo
        nodo_der = p.expresion

        es_id_o_constante = getattr(nodo_der, 'uso', None) in ["variable", "parametro", "constante"]
        
        if not es_id_o_constante and nodo_der.tipo != "ERROR":
            self.reportar_error(
                f"Error Semántico: En asignaciones con '=' dentro de expresiones, el lado derecho debe ser un identificador o constante, no un/a '{nodo_der.valor}'",
                p.lineno
            )
            tipo_resultado = "ERROR"
        else:
            tipo_resultado = self._validar_asignacion(nodo_izq, nodo_der, "=", p.lineno)

        return NodoArbol(valor="=", izquierdo=nodo_izq, derecho=nodo_der, tipo=tipo_resultado)
    
    def _validar_asignacion(self, nodo_izq, nodo_der, operador, linea):
        if nodo_izq.uso not in ['variable', 'parametro'] and nodo_izq.uso != "ERROR":
            self.reportar_error(f"Error semantico: No se puede asignar a un/a {nodo_izq.uso}", linea)
            return "ERROR"

        if not self._son_tipos_compatibles(nodo_izq.tipo, nodo_der.tipo):
            self.reportar_error(
                f"Error Semantico: Incompatibilidad de tipos en asignacion ({operador}). No se puede asignar '{nodo_der.tipo}' a '{nodo_izq.tipo}'",
                linea
            )
            return "ERROR"

        simbolo_tipo_izq = self.tabla.buscar(nodo_izq.tipo)
        if simbolo_tipo_izq and simbolo_tipo_izq.get("uso") == "enumeracion":
            if nodo_der.uso == 'constante' or str(nodo_der.valor).isupper():
                valores_permitidos = simbolo_tipo_izq.get("valores", [])
                if nodo_der.valor not in valores_permitidos:
                    self.reportar_error(
                        f"Error Semantico: El valor '{nodo_der.valor}' no es valido para la enumeracion '{nodo_izq.tipo}'. Permitidos: {valores_permitidos}",
                        linea
                    )
                    return "ERROR"

        if nodo_izq.tipo != "ERROR":
            simbolo_izq = self.tabla.buscar(nodo_izq.valor)
            if simbolo_izq:
                simbolo_izq['escrita'] = True

        return nodo_izq.tipo
    
    @_('ID')
    def lado_izquierdo(self, p):
        simbolo = self.tabla.buscar(p.ID)
        
        if not simbolo:
            self.reportar_error(f"Error semantico: la variable '{p.ID}' no fue declarada", p.lineno)
            return NodoArbol(valor=p.ID, tipo="ERROR", uso="ERROR")

        return NodoArbol(valor=p.ID, tipo=simbolo["tipo"], uso=simbolo["uso"])
    
    def _registrar_lectura(self, nodo, linea):
        if not isinstance(nodo, NodoArbol) or nodo.tipo == "ERROR":
            return

        if nodo.uso in ['variable', 'parametro']:
            simbolo = self.tabla.buscar(nodo.valor)
            if simbolo:
                if not simbolo.get('escrita', False):
                    self.reportar_warning(f"Warning: Uso de variable '{nodo.valor}' sin haber sido inicializada", linea)
                
                # 2. Marcamos que fue leída
                simbolo['leida'] = True

    @_('ID "." ID')
    def lado_izquierdo(self, p):
        # Llamamos al helper pasando es_posicional = False
        tipo_attr, uso_attr, nombre_attr = self._validar_acceso_objeto(
            nombre_obj=p.ID0, 
            referencia=p.ID1, 
            es_posicional=False, 
            lineno=p.lineno
        )
        
        return NodoArbol(valor=".", izquierdo=NodoArbol(valor=p.ID0), derecho=NodoArbol(valor=nombre_attr), tipo=tipo_attr, uso=uso_attr)

    @_('ID "[" CTE_USHORTINT "]"')
    def lado_izquierdo(self, p):
        indice = int(p.CTE_USHORTINT)
        tipo_attr, uso_attr, nombre_attr = self._validar_acceso_objeto(
            nombre_obj=p.ID, 
            referencia=indice, 
            es_posicional=True, 
            lineno=p.lineno
        )
        
        return NodoArbol(valor="posicional", izquierdo=NodoArbol(valor=p.ID), derecho=NodoArbol(valor=nombre_attr), tipo=tipo_attr, uso=uso_attr)
    
    def _validar_acceso_objeto(self, nombre_obj, referencia, es_posicional, lineno):
        simbolo_obj = self.tabla.buscar(nombre_obj)
        if not simbolo_obj:
            self.reportar_error(f"Error semantico: el objeto '{nombre_obj}' no fue declarado. Linea {lineno}")
            return "ERROR", "ERROR", str(referencia)

        nombre_clase = simbolo_obj.get("tipo")        
        simbolo_clase = self.tabla.buscar(nombre_clase)
        if not simbolo_clase or simbolo_clase.get("uso") != "clase":
            self.reportar_error(f"Error semantico: '{nombre_obj}' no es un objeto de clase. Linea {lineno}")
            return "ERROR", "ERROR", str(referencia)

        if es_posicional:
            indice = referencia
            atributos_clase = simbolo_clase.get("atributos", [])
            if indice >= len(atributos_clase):
                self.reportar_error(f"Error semantico: Indice fuera de rango. La clase '{nombre_clase}' tiene {len(atributos_clase)} atributos, se pidio el indice {indice}. Linea {lineno}")
                return "ERROR", "ERROR", str(indice)
            nombre_attr = atributos_clase[indice]
        else:
            nombre_attr = referencia

        alcance_clase = f"{simbolo_clase['alcance']}:{nombre_clase}"
        simbolo_attr = self.tabla.obtener(nombre_attr, alcance=alcance_clase)

        #si el atributo o metodo no esta en la clase local, buscamos en la lista de padres
        #cuando lo encuentra corta y devuelve el simbolo del padre que contiene el atributo
        if not simbolo_attr:
            padres = simbolo_clase.get("herencia", [])
            for padre in padres:
                simbolo_padre = self.tabla.buscar(padre)
                alcance_padre = f"{simbolo_padre['alcance']}:{padre}"
                simbolo_attr = self.tabla.obtener(nombre_attr, alcance=alcance_padre)
                if simbolo_attr:
                    break

        #si no encuentra el atributo o no es un elemento valido de clase, da error
        if not simbolo_attr or simbolo_attr.get("uso") not in ["variable", "metodo"]:
            self.reportar_error(f"Error semantico: El atributo/metodo '{nombre_attr}' no existe en la clase '{nombre_clase}' ni en sus clases heredadas. Linea {lineno}")
            return "ERROR", "ERROR", nombre_attr

        return simbolo_attr["tipo"], simbolo_attr["uso"], nombre_attr

    @_('"(" condicion ")"')
    def condicion_parentesis(self, p):
        return p.condicion
    
    @_('expresion comparador expresion')
    def condicion(self, p):
        izq = p.expresion0
        der = p.expresion1
        
        #se valida la compatibilidad de tipos entre las expresiones
        if izq.tipo != der.tipo and "ERROR" not in [izq.tipo, der.tipo]:
            self.reportar_error(f"Error Semantico: Tipos incompatibles en la condicion. Linea {p.lineno}")
            
        #el valor es que tipo de comparador es y el tipo es booleano porque una condicion es true o false
        return NodoArbol(valor=p.comparador, izquierdo=izq, derecho=der, tipo="BOOLEAN")
    
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
        return p.bloque_ejecutable

    @_('')
    def bloque_else(self, p):
        return None
    
    # ---------------- EXPRESIONES ARITMETICAS ----------------

    def _procesar_operacion_binaria(self, op, izq, der, linea):
        if "ERROR" in [izq.tipo, der.tipo]:
            return NodoArbol(valor=op, izquierdo=izq, derecho=der, tipo="ERROR")

        if izq.tipo != der.tipo:
            self.reportar_error(
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
            self.reportar_error(
                f"Error Semántico: 'todf' requiere una expresión de tipo entero, se obtuvo '{nodo_expr.tipo}'", 
                p.lineno
            )
        # Retornamos el nodo de conversión promocionando el tipo a DOUBLEF
        return NodoArbol(valor="todf", izquierdo=nodo_expr, tipo="DOUBLEF")

    @_('lado_izquierdo')
    def expresion(self, p):
        nodo_izq = p.lado_izquierdo
        #verificamos si lo que se usa como lado_izquierdo es una variable o parametro, nunca funcion, clase o metodo
        if nodo_izq.uso not in ['variable', 'parametro'] and nodo_izq.uso != "ERROR":
            self.reportar_error(
                f"Error semantico: Uso incorrecto de '{nodo_izq.valor}'. "
                f"No se puede usar un/a {nodo_izq.uso} como valor. Linea {p.lineno}"
            )
            nodo_izq.tipo = "ERROR"
        self._registrar_lectura(p.lado_izquierdo, p.lineno)
        return nodo_izq
    
    def reportar_warning(self, mensaje, linea=None):
        if linea is not None and f"Linea {linea}" not in str(mensaje):
            mensaje_final = f"{mensaje}. Linea {linea}"
        else:
            mensaje_final = str(mensaje)

        if mensaje_final in self.warnings_emitidos:
            return

        self.warnings_emitidos.add(mensaje_final)
        print(mensaje_final)

    @_('asignacion_igual',
       'llamado_funcion')
    def expresion(self, p):
        return p[0]

    @_('CTE_USHORTINT')
    def expresion(self, p):
        return NodoArbol(valor=p.CTE_USHORTINT, tipo="USHORTINT", uso="constante")

    @_('CADENA')
    def expresion(self, p):
        return NodoArbol(valor=p.CADENA, tipo="CADENA", uso="constante")

    @_('expr_cte_doublef')
    def expresion(self, p):
        return NodoArbol(valor=p.expr_cte_doublef, tipo="DOUBLEF", uso="constante")

    @_('expr_neg_cte_doublef')
    def expresion(self, p):
        return NodoArbol(valor=p.expr_neg_cte_doublef, tipo="DOUBLEF", uso="constante")
    
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
        nodo_funcion = p.lado_izquierdo
        argumentos = p.lista_argumentos
        orden = p.orden_parametros

        #validamos que existe la funcion/metodo
        if nodo_funcion.uso not in ["funcion", "metodo"] and nodo_funcion.uso != "ERROR":
            self.reportar_error(f"Error semantico: No se puede invocar a '{nodo_funcion.valor}'. Linea {p.lineno}")

        #validamos los parametros reales contra los formales
        simbolo_func = self.tabla.buscar(nodo_funcion.valor)
        if simbolo_func:
            params_formales = simbolo_func.get("parametros", [])
            
            if len(argumentos) != len(params_formales):
                self.reportar_error(
                    f"Error Semantico: La funcion '{nodo_funcion.valor}' espera {len(params_formales)} "
                    f"argumentos, pero se pasaron {len(argumentos)}. Linea {p.lineno}"
                )
            else:
                for i, (arg_real, param_formal) in enumerate(zip(argumentos, params_formales)):
                    tipo_esperado = param_formal.get("tipo")
                    
                    if not self._son_tipos_compatibles(tipo_esperado, arg_real.tipo):
                        self.reportar_error(
                            f"Error Semantico: Tipo de argumento invalido en la posicion {i+1} al invocar "
                            f"'{nodo_funcion.valor}'. Se esperaba '{tipo_esperado}', se recibio '{arg_real.tipo}'. Linea {p.lineno}"
                        )

        #vemos si hay orden o no y verificamos que el orden sea valido de haber
        if orden is not None:
            if len(orden) != len(argumentos):
                self.reportar_error(f"Error Semantico: La cantidad de elementos en el orden ({len(orden)}) no coincide con la cantidad de argumentos ({len(argumentos)}). Linea {p.lineno}")
            
            orden_esperado = list(range(1, len(argumentos) + 1))
            if sorted(orden) != orden_esperado:
                self.reportar_error(f"Error Semantico: El orden indicado {orden} es invalido. Faltan o sobran indices. Linea {p.lineno}")
        else:
            orden = list(range(1, len(argumentos) + 1))

        nodo_llamado = NodoArbol(valor="INVOCACION", izquierdo=nodo_funcion, derecho=argumentos, tipo=nodo_funcion.tipo)
        nodo_llamado.orden_evaluacion = orden
        
        return nodo_llamado
    
    @_('"[" lista_orden "]"')
    def orden_parametros(self, p):
        return p.lista_orden
    
    @_('')
    def orden_parametros(self, p):
        return None
    
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
    
    def verificar_uso_variables(self):
        for clave, datos in self.tabla.tabla.items():
            uso = datos.get("uso")
            if uso not in ["variable", "parametro"]:
                continue

            # 1. Excluir atributos declarados dentro de una clase
            alcance = datos.get("alcance", "")
            partes_alcance = alcance.split(":")
            if len(partes_alcance) > 1:
                padre_alcance = self.tabla.buscar(partes_alcance[-1])
                if padre_alcance and padre_alcance.get("uso") == "clase":
                    continue

            leida = datos.get("leida", False)
            escrita = datos.get("escrita", False)
            linea = datos.get("linea", "?")
            nombre_mostrar = datos.get("lexema", clave)

            # Verificamos si la variable es una instancia de una clase
            simbolo_tipo = self.tabla.buscar(datos.get("tipo"))
            es_objeto_clase = (simbolo_tipo is not None and simbolo_tipo.get("uso") == "clase")

            if uso == "parametro":
                if not leida and not escrita:
                    self.reportar_warning(f"WARNING (Línea {linea}): El parámetro '{clave}' fue declarado pero nunca se utilizó.")
                continue

            if not leida and (not escrita or es_objeto_clase):
                self.reportar_warning(f"WARNING (Línea {linea}): La variable '{clave}' fue declarada pero nunca utilizada.")
            elif escrita and not leida and not es_objeto_clase:
                self.reportar_warning(f"WARNING (Línea {linea}): La variable '{clave}' fue asignada pero su valor nunca fue leído.")
    
    def _contiene_retorno(self, nodo):
        if nodo is None:
            return False
        if isinstance(nodo, list):
            return any(self._contiene_retorno(hijo) for hijo in nodo)
        if not isinstance(nodo, NodoArbol):
            return False
        if nodo.valor == "RET":
            return True
        return self._contiene_retorno(nodo.izquierdo) or self._contiene_retorno(nodo.derecho)
    
    def _crear_retorno_por_defecto(self, tipo_retorno, linea):
        # 1. Tipos primitivos
        if tipo_retorno == "USHORTINT":
            valor_defecto = NodoArbol(valor="0$us", tipo="USHORTINT", uso="constante")
            return NodoArbol(valor="RET", izquierdo=valor_defecto, tipo="USHORTINT")
            
        elif tipo_retorno == "DOUBLEF":
            valor_defecto = NodoArbol(valor="0.0", tipo="DOUBLEF", uso="constante")
            return NodoArbol(valor="RET", izquierdo=valor_defecto, tipo="DOUBLEF")
            
        elif tipo_retorno == "CADENA":
            valor_defecto = NodoArbol(valor='""', tipo="CADENA", uso="constante")
            return NodoArbol(valor="RET", izquierdo=valor_defecto, tipo="CADENA")

        simbolo_tipo = self.tabla.buscar(tipo_retorno)
        if simbolo_tipo:
            if simbolo_tipo.get("uso") == "enumeracion":
                valores = simbolo_tipo.get("valores", [])
                if valores:
                    valor_defecto = NodoArbol(valor=valores[0], tipo=tipo_retorno, uso="constante")
                    return NodoArbol(valor="RET", izquierdo=valor_defecto, tipo=tipo_retorno)
            
            elif simbolo_tipo.get("uso") == "clase":
                self.reportar_error(
                    f"Error semantico: La funcion retorna la clase '{tipo_retorno}' y requiere una sentencia RET explicita",
                    linea
                )
                return NodoArbol(valor="RET", tipo="ERROR")

        return NodoArbol(valor="RET", tipo="ERROR")
    
    def _asegurar_retorno_en_cuerpo(self, nombre_subprograma, cuerpo, linea):
        if self._contiene_retorno(cuerpo):
            return cuerpo

        simbolo = self.tabla.buscar(nombre_subprograma)
        tipo_ret = simbolo.get("tipo") if simbolo else "ERROR"
        nodo_ret = self._crear_retorno_por_defecto(tipo_ret, linea)

        if cuerpo is None:
            return [nodo_ret]
        elif isinstance(cuerpo, list):
            return cuerpo + [nodo_ret]
        else:
            return [cuerpo, nodo_ret]

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
    
    @_('RET error ";"')
    def sentencia_ejecutable_funcion(self, p):
        self.reportar_error(f"Error sintactico: retorno mal formado. Linea {p.lineno}")

    #ERRORES DE FUNCIONES
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

    # @_('tipo FUNCTION ID "(" error ")" cuerpo_funcion')
    # def declaracion_funcion(self, p):
    #     self.reportar_error(f"Error sintactico: falta parentesis de cierre ')'. Linea {p.lineno}")
    #     self.tabla.cerrar_ambito()
    #     return ('ERROR_RECUPERADO',)
    
    @_('error cuerpo_funcion')
    def declaracion_funcion(self, p):
        self.reportar_error(f"Error sintactico: funcion mal declarada. Linea {p.lineno}")
        self.tabla.cerrar_ambito()
        return ('ERROR_RECUPERADO',)
    
    #FALTA DE PUNTO Y COMA 
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
        self.reportar_error(f"Error sintactico: falta ; cerca de linea {p._slice[1].lineno}.")
        return ('ERROR_RECUPERADO',)
    
    @_('cuerpo_elemento_clase error')
    def elemento_clase(self, p):
        self.reportar_error(f"Error sintactico: revisar falta de ';' o declaracion erronea de metodos. Linea {p._slice[1].lineno}.")
        return ('ERROR_RECUPERADO',)

    #ERRORES EN ENUMERADO
    @_('TYPEDEF ID ASIGNACION_IGUAL "[" error "]"')
    def cuerpo_declaracion(self, p):
        self.reportar_error(f"Error sintactico: declaracion invalida para valores de enumerado. Linea {p.lineno}")
        return ('ERROR_RECUPERADO',)

    #ERRORES DE CLASE
    @_('CLASS error BEGIN declaracion_clase clausula_extends END')
    def declaracion_de_clase_completa(self, p):
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
        print("Uso: python3 analizador_sintactico.py <archivo> [--ast]")
        sys.exit(1)

    nombre_archivo = sys.argv[1]
    mostrar_arbol = "--ast" in sys.argv or "-a" in sys.argv

    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            data = archivo.read()
            
        lexer = analizador_lexico()
        parser = analizador_sintactico()
            
        tokens = lexer.tokenize(data)
        parser.tabla = lexer.ts 
        
        arbol = parser.parse(tokens)
            
        print("-" * 65)
        
        # Impresión de la Tabla de Símbolos (requerida en las salidas del TP4)
        parser.tabla.imprimir()

        # Impresión opcional del Árbol Sintáctico (AST)
        if mostrar_arbol and arbol:
            print("\n" + "=" * 30 + " ÁRBOL SINTÁCTICO " + "=" * 30)
            if hasattr(arbol, 'imprimir'):
                arbol.imprimir()
            else:
                pprint(arbol, indent=2, width=80)
            print("=" * 78)

        total_errores = lexer.errores + parser.errores
        
        if arbol is not None and total_errores == 0:
            print("\nSe ha compilado exitosamente.")
            generador = generador_assembler(parser.tabla)
            codigo_wat = generador.generar(arbol)

            with open("salida.wat", "w", encoding="utf-8") as archivo_salida:
                archivo_salida.write(codigo_wat)
            print("Codigo WebAssembly generado exitosamente en 'salida.wat'.")
        else:
            print("\nNo se genero codigo WebAssembly debido a errores de compilacion.")
            
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{nombre_archivo}'.")