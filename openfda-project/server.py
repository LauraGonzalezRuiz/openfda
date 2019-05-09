import http.server
import http.client
import json
import socketserver

PORT = 8000
INDEX_FILE = "index.html"
SERVIDOR_REST = "api.fda.gov"
LABEL = "/drug/label.json"

headers = {'User-Agent': 'http-client'}

class TestHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    # La clase tiene 7 metodos
    DRUG = '&search=active_ingredient:'
    COMPANY = '&search=openfda.manufacturer_name:'
    def pagina_inicio(self):

        with open(INDEX_FILE, "r") as f:
            index_html = f.read()

            return index_html

    def conexion_fda(self, limite=1, busqueda=""):
        #cadena de la petición
        str_pedido = "{}?limit={}".format(LABEL, limite)

        #si han pedido algo más en concreto lo añadimos a la cadena de peticion
        if busqueda != "":
            str_pedido += "&{}".format(busqueda)

        print("URL: ",str_pedido)

        #establecemos la conexion
        conexion = http.client.HTTPSConnection(SERVIDOR_REST)

        #enviamos la solicitud de la informacion desada
        conexion.request("GET", str_pedido, None, headers)

        #respuesta del servidor
        r1 = conexion.getresponse()
        print("  * {} {}".format(r1.status, r1.reason))
        #leemos json + transformamos en diccionario, en las demás funciones
        #cogeremos lo que necesitemos en cada una de ellas

        informacion_json = r1.read().decode("utf8")

        conexion.close()

        return json.loads(informacion_json)

    def lista_medicamentos(self, limite, principio_activo=''):
        #nos devolerá la lista de medicamentos, con el límite pedido
        if principio_activo:
            medicamentos = self.conexion_fda(limite, self.DRUG + principio_activo)
            print('HAY PRINCIO ACTIVO')
        else:
            medicamentos = self.conexion_fda(limite)
        #es un diccionario, indexaremos los nombres de los medicamentos
        listado_medicamentos =[]

        for medicamento in medicamentos['results']:
            try:
                nombre = medicamento['openfda']['generic_name'][0]
            except KeyError:
                nombre = 'Desconocido'
            listado_medicamentos.append(nombre)
        #hacemos el HTML que verá el cliente
        return self.index_2(listado_medicamentos)

    def lista_empresas(self, limite,empresa=''):
        if empresa:
            medicamentos = self.conexion_fda(limite, self.DRUG + empresa)
        else:
            medicamentos = self.conexion_fda(limite)

        listado_empresas = []

        for medicamento in medicamentos['results']:
            try:
                nombre_empresa = medicamento['openfda']['manufacturer_name'][0]
            except KeyError:
                nombre_empresa = 'Desconocido'

            listado_empresas.append(nombre_empresa)

        #hacemos el HTML que verá el cliente
        return self.index_2(listado_empresas)

    def lista_advertencias(self, limite):
        medicamentos = self.conexion_fda(limite)

        lista_advertencias = []

        for medicamento in medicamentos['results']:
            try:
                advertencia = medicamento['warnings'][0]
            except KeyError:
                advertencia = 'Desconocida'

            lista_advertencias.append(advertencia)

        #hacemos el HTML que verá el cliente
        return self.index_2(lista_advertencias)

    def index_2(self, lista):
        mensaje_html = (' <!DOCTYPE html>\n'
                        '<html lang="es">\n'
                        '<head>\n'
                        '<title>OpenFDA App</title>'
                        '</head>\n'
                        '<body style="background-color: #D358F7;">\n'
                        '<h1> La informacion buscada es: </h1>'
                        '\n'
                        '<ul>\n')

        for i in lista:
            mensaje_html += "<li>" + i + "</li>"

        mensaje_html += ('</ul>\n'
                    '\n'
                    '<a href="/">VOLVER</a>'
                    '</body>\n'
                    '</html>')

        return mensaje_html

    def error_html(self):
        mensaje_html=(' <!DOCTYPE html>\n'
                        '<html lang="es">\n'
                        '<head>\n'
                        '<title>OpenFDA App</title>'
                        '</head>\n'
                        '<body style="background-color: #FB4343;">\n'
                        '<h1>Valores introducidos incorectos, vuelva a intentarlo</h1>'
                        '\n'
                        '<ul>\n'
                        '<a href="/">VOLVER</a>'
                        '</body>\n'
                        '</html>')

        return mensaje_html

    def do_GET(self):

        print("Recurso pedido: {}".format(self.path))
        mensaje = ""

        # Dividimos entre el endpoint y los parametros
        lista_recurso_pedido = self.path.split("?")
        endpoint = lista_recurso_pedido[0]

        #Hay parámetros o no hay
        if len(lista_recurso_pedido) > 1:
            parametros = lista_recurso_pedido[1]
        else:
            parametros = ""
        # Limite por defecto
        limite = 1
        try:
            # Obtener los parametros
            if parametros:
                print("Se ha introducido un limite")
                limite_parametro = parametros.split("=")
                #Sacamos el limiten en un entero
                if limite_parametro[0] == "limit":
                    limite = int(limite_parametro[1])
                    print("Limit: {}".format(limite))
                elif limite_parametro[0] == 'active_ingredient':
                    principio_activo = str(limite_parametro[1])
                    print('PRINCIPIO ACTIVO', principio_activo)
                elif limite_parametro == 'company':
                    empresa = str(limite_parametro[1])
                    print('EMPRESA CONCRETA', empresa)
            else:
                print("No se han introducido parmetros")
                limite =1

            #dependiendo del botón pulsado, endpointvariará así como la función a usar
            #e introduciremos el límite obtenido
        
            if endpoint == "/":
                mensaje = self.pagina_inicio()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(mensaje, "utf8"))

            elif endpoint=='/listDrugs':
                print('Listado de medicamentos ')
                mensaje = self.lista_medicamentos(limite)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(mensaje, "utf8"))

            elif endpoint == '/listCompanies':
                print('Listado de empresas')
                mensaje = self.lista_empresas(limite)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(mensaje, "utf8"))

            elif endpoint == '/listWarnings' :
                print('Listado de advertencias')
                mensaje = self.lista_advertencias(limite)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(mensaje, "utf8"))

            elif endpoint == '/searchDrug':
                print('Listado de medicamentos con un principio activo concreto')
                limite =10
                mensaje = self.lista_medicamentos(limite,parametros)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(mensaje, "utf8"))

            elif endpoint=='/searchCompany':
                print('Lista de empresas')
                limite=10
                mensaje = self.lista_empresas(limite,parametros)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(mensaje, "utf8"))

            elif endpoint=='/redirect' :
                self.send_response(301)
                self.send_header('Location', 'http://localhost:' + str(PORT))
                self.end_headers()

            elif endpoint=='/secret':
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Mi servidor"')  # Le envias esa cabecera.
                self.end_headers()

            else:
                mensaje=self.error_html()
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(mensaje, "utf8"))
                #self.wfile.write("No encuentro ese recurso '{}'.".format(self.path).encode())
        except ValueError:
            print('LÍMITE INTRODUCIDO ERRÓNEO')
            mensaje=self.error_html()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(mensaje, "utf8"))

        except KeyError:
            print('NOMBRE NO ENCONTRADO')
            mensaje=self.error_html()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(mensaje, "utf8"))

        return

socketserver.TCPServer.allow_reuse_address = True #para evitar cmabiar de puerto

Handler = TestHTTPRequestHandler
#se encarga de responder a las peticciones http que puede venir de dos sitios, un ordenador o el test de la practica

httpd = socketserver.TCPServer(("", PORT), Handler)
print("Sirviendo en el puerto:", PORT)
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("El usuario ha interrumpido el servidor en el puerto:", PORT)
    print("Reanudelo de nuevo")
    print("Servidor parado")
