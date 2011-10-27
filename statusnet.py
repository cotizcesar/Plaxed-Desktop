# -*- coding: utf-8 *-*
import json
import urllib2
from urllib import urlencode
from base.base import *
import logging

logging.basicConfig()
log = logging.getLogger('StatusNET')
log.setLevel(logging.DEBUG)

class statusNet():

    #Variables Globales
    var_conectado = False
    usuario = ''
    clave = ''
    apibase = ''
    servidor = ''
    mi_perfil = {}
    app_origen = 'Plaxed Desktop (Demo)'

    def __init__(self, servidor, usuario, clave):
        self.conectar(servidor, usuario, clave)

    def conectar(self, servidor, usuario, clave):
        apibase = servidor + "/api"
        apibase.replace("//", "/")
        pwd_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pwd_mgr.add_password(None, apibase, usuario, clave)
        self.handler = urllib2.HTTPBasicAuthHandler(pwd_mgr)
        self.opener = urllib2.build_opener(self.handler)
        urllib2.install_opener(self.opener)
        self.conectado = False
        try:
            open = urllib2.urlopen(apibase + '/account/verify_credentials.json')
            leido = open.read()
            self.mi_perfil = json.loads(leido)
            self.var_conectado = True
            self.usuario = usuario
            self.clave = clave
            self.servidor = servidor
            self.apibase = apibase
        except urllib2.HTTPError:
            pass

    def estaConectado(self):
        return self.var_conectado

    def mostrarMensaje(self, texto):
        #cuando tenga interfaz grafica, esto debe modificarse
        #print str_utf8(texto)
        pass

    def miPerfilAttr(self, param):
        try:
            dato = self.mi_perfil[param]
        except:
            dato = "{Error}"
        return dato

    def Respuestas(self, ultimo=0):
        if ultimo != 0:
            #ultimo = ultimo + 1
            filtro = "?since_id=" + str(ultimo)
        else:
            filtro = ""
        open = urllib2.urlopen(self.apibase + '/statuses/replies.json' + filtro)
        leido = open.read()
        miTL = json.loads(leido)
        return miTL

    def Favoritos(self, ultimo=0):
        if ultimo != 0:
            #ultimo = ultimo + 1
            filtro = "?since_id=" + str(ultimo)
        else:
            filtro = ""
        open = urllib2.urlopen(self.apibase + '/favorites.json' + filtro)
        leido = open.read()
        miTL = json.loads(leido)
        return miTL

    def TimeLineUser(self): #Esto hay que ARREGLARLO
        open = urllib2.urlopen(self.apibase + '/statuses/user_timeline.json')
        leido = open.read()
        miTL = json.loads(leido)
        return miTL

    def TimeLineHome(self, ultimo=0):
        if ultimo != 0:
            #ultimo = ultimo + 1
            filtro = "?since_id=" + str(ultimo)
        else:
            filtro = ""
        open = urllib2.urlopen(self.apibase + '/statuses/home_timeline.json' + filtro)
        leido = open.read()
        miTL = json.loads(leido)
        return miTL

    def TimeLinePublic(self, ultimo=0):
        if ultimo != 0:
            #ultimo = ultimo + 1
            filtro = "?since_id=" + str(ultimo)
        else:
            filtro = ""
        open = urllib2.urlopen(self.apibase + '/statuses/public_timeline.json' + filtro)
        leido = open.read()
        miTL = json.loads(leido)
        return miTL

    def miBuzon(self, param=''):
        param.lower()
        if param != "sent" and param != "new":
            param = ""
        else:
            param = u"/%s" % param
            param.replace("//", "/")
        print param
        open = urllib2.urlopen(self.apibase + '/direct_messages' + param + '.json')
        leido = open.read()
        miTL = json.loads(leido)
        return miTL

    def Publicar(self, txt):
        paquete = urlencode({'status': txt, 'source': self.app_origen})
        try:
            open = urllib2.urlopen(self.apibase + '/statuses/update.json?%s' % paquete, '')
            leido = open.read()
            log.debug('Enviado: ' + str(leido))
        except:
            leido = "{Error}"
            log.debug('Envio Fallido')
        return leido
