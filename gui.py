# -*- coding: utf-8 *-*
import wx
import wx.html
import wx.animate
from wx.lib.wordwrap import wordwrap
import threading
from wx.lib.pubsub import Publisher
import httplib
import sys
import os
import datetime
import time
import getpass
import logging
import re
from statusnet import *

logging.basicConfig()
log = logging.getLogger('GUI')
log.setLevel(logging.DEBUG)


class InterfazPrincipal(wx.Frame):

    tls = ['tl_home','tl_public','replies','favorites','messages']
    cols = []
    ultimo = []
    cols_vacia = []
    tl_actual = ''
    indiceActual = 0
    red = None
    txt = []
    timer = None  # El timer de actualizar
    dir_perfiles = './perfiles/'
    dir_usuario = ''
    dir_imagenes = ''
    app_dir_img = './img/'
    html_loader_tl = '<br><br><center><img src="img/loader_timeline_transparente2.gif"></center>'
    usuario = ''
    clave = ''
    servidor = ''
    intervaloTL = 15
    txtDescripcion = ''
    me = None  # Variable con datos del usuario, no implementada aun
    primeraCargaImg = True
    carRestantes = 140
    Let_Tahoma_8 = None
    Let_Tahoma_9 = None
    Let_Tahoma_10 = None
    Let_Tahoma_11 = None
    Let_Tahoma_12 = None
    Let_Tahoma_13 = None
    Let_Tahoma_14 = None
    Let_Tahoma_15 = None
    Let_Tahoma_16 = None

    def __init__(self, parent, titulo, servidor, usuario, clave):
        self.parent = parent
        self.usuario = usuario
        self.clave = clave
        self.servidor = servidor
        wx.Frame.__init__(self, parent, wx.ID_ANY, titulo, size=(700, 600))
        self.Conectar(self.servidor, self.usuario, self.clave)

    def __del__(self):
        try:
            self.timer.cancel()
        except:
            pass
        log.debug('Terminando Aplicacion')
        self.parent.Destroy()

    def Conectar(self, servidor, usuario, clave):
        log.debug('Creando Coneccion')
        self.red = statusNet(servidor, usuario, clave)
        if self.red.EstaConectado():
            log.debug('Se establecio la Coneccion')
            self.ConfigurarFuentes()
            self.VerificarDirectorios()
            self.ConfigurarVentana()
            self.Actualizar()

    def ConfigurarFuentes(self):
        self.Let_Tahoma_16 = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Tahoma')
        self.Let_Tahoma_15 = wx.Font(15, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Tahoma')
        self.Let_Tahoma_14 = wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Tahoma')
        self.Let_Tahoma_13 = wx.Font(13, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Tahoma')
        self.Let_Tahoma_12 = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Tahoma')
        self.Let_Tahoma_11 = wx.Font(11, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Tahoma')
        self.Let_Tahoma_10 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Tahoma')
        self.Let_Tahoma_9 = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Tahoma')
        self.Let_Tahoma_8 = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Tahoma')

    def EnterEstado(self, event):
        self.EnviarMensaje()

    def BotonEstado(self, event):
        self.EnviarMensaje()

    def EscribeEstado(self, event):
        texto = self.txt_estado.GetValue()
        restante = 140 - len(texto)
        self.carRestantes = restante
        self.lblCuenta.SetLabel(str(restante))
        event.Skip()

    def AtajosTeclado(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_F5:
            log.debug('F5: Enviar Mensaje')
            self.EnviarMensaje()
        else:
            event.Skip()


    def EnviarMensaje(self):
        texto = self.txt_estado.GetValue()
        texto = texto.encode('utf8')
        texto = texto.strip()
        if texto != '':
            if self.carRestantes < 0:
                wx.MessageBox('No puede exceder los 140 caracteres')
                return False
            #
            self.txt_estado.Disable()
            self.btnAceptar.Disable()
            self.PlayLoaderEnvio()
            self.respuestaEnvio = HiloEnviarMensaje(self, self.servidor, self.usuario, self.clave, texto)
        else:
            wx.MessageBox('Debe ingresar un mensaje')
            self.txt_estado.SetValue('')
            self.txt_estado.SetFocus()


    def InnerHTML(self, txt):
        log.debug("Inyectando HTML")
        bottom=self.cols[0].GetBottom()
        self.cols[0].SetPage(txt)
        self.cols[0].SetBottom(bottom)
        log.debug("Finalizando Inyeccion HTML")

    def ActualizaBarraEstado(self):
        origen = self.cols[0].GetOrigen()
        Lugar = 'No definido'
        if origen == 'tl_home':
            Lugar = 'Inicio'
        if origen == 'tl_public':
            Lugar = u'Público'
        if origen == 'replies':
            Lugar = 'Respuestas'
        if origen == 'favorites':
            Lugar = 'Favoritos'
        if origen == 'messages':
            Lugar = 'Mensajes'
        self.sBar.SetFields((Lugar,'Autor: @jrcsdev'))

    def DescargarAvatar(self, ruta_img):
        tmp = ruta_img.split("/")
        img_nombre = tmp[len(tmp) - 1]
        #
        carpetas=''
        for i in range(3,len(tmp)-1):
            carpetas = carpetas + '/' + tmp[i]
        carpetas = carpetas + '/'
        img_ruta = carpetas + img_nombre
        img_ruta_local = self.dir_imagenes + img_nombre
        tmp_serv = self.red.servidor.split("//")
        serv = "www." + tmp_serv[1]
        tmp2 = img_nombre.split('-')
        idu = tmp2[0] #esto es el ID del usuario, antes del primer guion
        if (not os.path.isfile(img_ruta_local)):
            if self.primeraCargaImg:
                log.debug('Intentando eliminar la imagen antigua')
                try:
                    self.BorrarImgAnterior(idu)
                except:
                    log.debug('No se encontro la imagen o no se pudo borrar')
            # Descargando nueva imagen
            try:
                con = httplib.HTTPConnection(serv)
                con.request("GET", img_ruta)
                r = con.getresponse()
                archivo = file(img_ruta_local, 'wb')
                archivo.write(r.read())
                archivo.close()
                log.debug("Imagen descargada")
            except:
                log.debug("Error al descargar imagen")
        else:
            log.debug('Ya existe la imagen')

    def RutaOnlineToLocal(self, ruta):
        img_arr = ruta.split("/")
        img_nombre = img_arr[len(img_arr) - 1]
        if (os.path.isfile(self.dir_imagenes + img_nombre)):
            img_ruta_local = self.dir_imagenes + img_nombre
        else:
            img_ruta_local = self.app_dir_img + 'default.png'
        return img_ruta_local

    def Actualizar(self):
        self.ActualizaBarraEstado()
        self.respuestaTL = HiloTimeLine(self, self.servidor, self.usuario, self.clave,self.cols[0].GetOrigen(), self.primeraCargaImg)
        log.debug("Solicitando Actualizacion de: " + self.cols[0].GetOrigen())

    def ActualizarTimer(self):
        #Intentando crear timer
        if self.timer == None:
            self.timer = threading.Timer(self.intervaloTL, self.Actualizar)
            log.debug("Creando timer a %s segundos", str(self.intervaloTL))
        else:
            log.debug("Deteniendo el timer")
            self.timer.cancel()
            self.timer = None
            log.debug("Reiniciando timer a %s segundos", str(self.intervaloTL))
            self.timer = threading.Timer(self.intervaloTL, self.Actualizar)
        self.timer.start()

    def TL_Mensajes(self, msj):
        log.debug('****SE RECIBIERON MENSAJES DEL THREAD****')
        if self.primeraCargaImg:
            self.primeraCargaImg = False
        self.ultimo[self.indiceActual] = self.respuestaTL.ultimo
        if self.cols_vacia[self.indiceActual] == True:
            self.txt[self.indiceActual] = self.respuestaTL.txt
        else:
            self.txt[self.indiceActual] = self.respuestaTL.txt + self.txt[self.indiceActual]
        self.cols_vacia[self.indiceActual] = False
        self.InnerHTML(self.txt[self.indiceActual])

        self.ActualizarTimer()

    def TL_Vacio(self, msj):
        self.ActualizarTimer()

    def HiloEnviarMensaje(self, msj):
        respuesta = msj.data
        log.debug('Respuesta del Hilo "Enviar Mensaje": ' + respuesta)
        self.StopLoaderEnvio()
        if respuesta == "TimeOut":
            log.debug('Reintente el envio nuevamente')
            self.txt_estado.Enable()
            self.btnAceptar.Enable()
        if respuesta == "MensajeEnviado":
            log.debug('Mensaje Enviado')
            self.txt_estado.SetValue('')
            self.txt_estado.Enable()
            self.btnAceptar.Enable()
        if respuesta == "MensajeNoEnviado":
            log.debug('Mensaje No Enviado')
            self.txt_estado.Enable()
            self.btnAceptar.Enable()
        if respuesta == "APP_Desconectado":
            log.debug('Reintente el envio')
            self.txt_estado.Enable()
            self.btnAceptar.Enable()

    def HiloEnviarMensajeDirecto(self, msj):
        respuesta = msj.data
        log.debug('Respuesta del Hilo "Enviar Mensaje": ' + respuesta)
        if respuesta == "TimeOut":
            log.debug('Reintente el envio nuevamente')
            self.vtnRespuesta.Bloquear(False)
            wx.MessageBox(u'El servidor no respondió, intente de nuevo')
        if respuesta == "MensajeEnviado":
            log.debug('Mensaje Directo Enviado')
            self.vtnRespuesta.Destroy()
            self.Enable()
            self.txt_estado.SetFocus()
        if respuesta == "MensajeNoEnviado":
            log.debug('Mensaje Directo No Enviado')
            wx.MessageBox(u'El mensaje no se envió, intente de nuevo')
            self.vtnRespuesta.Bloquear(False)
        if respuesta == "APP_Desconectado":
            log.debug('Reintente el envio')
            wx.MessageBox(u'Aplicación Desconectada! Reintente el envío')
            self.vtnRespuesta.Bloquear(False)

    def APP_Desconectado(self, msj):
        log.debug('Aplicacion Desconectada')
        log.debug('Se reintentara nuevamente en ' + str(self.intervaloTL) + ' segundos')
        self.ActualizarTimer()

    def ReiniciaSolicitudTL(self, msj):
        log.debug('Interrumpiendo TL para reiniciar solicitud **')
        self.Actualizar()

    def LinkPresionado(self, msj):
        link = self.cols[0].enlace
        arreglo = link.split('/')
        url_servidor=arreglo[2]
        arreglo1 = self.servidor.split('/')
        app_servidor = arreglo1[2]
        #
        if url_servidor != app_servidor:
            wx.LaunchDefaultBrowser(link)
            return False

        url_tipo = arreglo[3]
        #
        if url_tipo == 'tag':
            wx.MessageBox(u'Los tags no están implementados todavía')
            return False

        if url_tipo == 'user':
            wx.MessageBox(u'Los perfiles de usuario no están implementados todavía')
            return False

        if url_tipo == 'group':
            wx.MessageBox(u'Los grupos no están implementados todavía')
            return False

        if url_tipo == 'url':
            wx.LaunchDefaultBrowser(link)
            #wx.MessageBox(u'Las URLs no están implementadas todavía')
            return False

        if url_tipo == 'notice':
            accion = arreglo[4]
            if accion == 'new':
                usuario = arreglo[5]
                id = arreglo[6]
                parametro = usuario + ',' + id
                #wx.MessageBox('Respuesta a usuario %s, Id del status %s' % (usuario, id))
                self.vtnRespuesta = VentanaResponder(self, parametro)
                self.vtnRespuesta.Show(callback=self.VentanaRespuestaOk, cancelCallback=self.VentanaRespuestaCancel)
            if accion == 'retweet':
                id = arreglo[5]
                wx.MessageBox('Repetir: ' + id)
            if accion == 'delete':
                id = arreglo[5]
                wx.MessageBox('Borrar: ' + id)

        if url_tipo == 'favorites':
            accion = arreglo[4]
            id = arreglo[5]
            if accion == 'create':
                wx.MessageBox('Crear Favorito: ' + id)
            if accion == 'destroy':
                wx.MessageBox('Destruir Favorito: ' + id)
            #
        if url_tipo == 'conversation':
            id = arreglo[4]
            wx.MessageBox('Ver Conversacion: ' + id)
            return False

    def VentanaRespuestaOk(self, txt, idmensaje):
        #wx.MessageBox('Se enviara el mensaje "%s" en respuesta al id = %s' % (txt, idmensaje))
        #{Error}
        self.respuestaEnvioDirecto = HiloEnviarMensaje(self, self.servidor, self.usuario, self.clave, txt, True, idmensaje)


    def VentanaRespuestaCancel(self):
        pass

    def PlayLoaderEnvio(self):
        self.loaderEnvio.Play()

    def StopLoaderEnvio(self):
        self.loaderEnvio.Stop()

    def ConfigurarVentana(self):
        Publisher().subscribe(self.TL_Mensajes, "TL_Mensajes")
        Publisher().subscribe(self.TL_Vacio, "TL_Vacio")
        Publisher().subscribe(self.HiloEnviarMensaje, "Hilo_Enviar_Mensaje")
        Publisher().subscribe(self.HiloEnviarMensajeDirecto, "Hilo_Enviar_Mensaje_Directo")
        Publisher().subscribe(self.APP_Desconectado, "APP_Desconectado")
        Publisher().subscribe(self.LinkPresionado, "LinkPresionado")
        Publisher().subscribe(self.ReiniciaSolicitudTL, "TL_No_Recibido")
        #
        log.debug('Cantidad de TimeLines: '+str(len(self.tls)))
        for i in range(len(self.tls)):
            log.debug('Inicializando TL ' + str(i) + ' (' + self.tls[i]  + ')')
            self.txt.append('')
            self.ultimo.append(0)
            self.cols_vacia.append(True)
        log.debug('Configurando Ventana')
        icono = wx.Icon('img/iconosolo16.png', wx.BITMAP_TYPE_PNG)
        self.SetIcon(icono)
        self.SetMinSize((400, 500))

        self.panel = wx.Panel(self)

        #Configurando la fila del perfil de usuario
        self.h_sizerPerfil = wx.BoxSizer(wx.HORIZONTAL)
        ruta_img = self.red.miPerfilAttr('profile_image_url')
        self.DescargarAvatar(ruta_img)
        ruta_img_local = self.RutaOnlineToLocal(ruta_img)
        self.miImagen = wx.StaticBitmap(self.panel, wx.ID_ANY, wx.Bitmap(ruta_img_local, wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.h_sizerPerfil.Add(self.miImagen, 0, wx.TOP|wx.LEFT|wx.RIGHT, 5 )

        self.v_sizerInfo = wx.BoxSizer(wx.VERTICAL)

        usr_nombre = self.red.miPerfilAttr('screen_name')
        self.lblUsuario = wx.StaticText(self.panel, wx.ID_ANY, usr_nombre, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lblUsuario.Wrap(-1)
        self.lblUsuario.SetFont(self.Let_Tahoma_14)

        self.txtDescripcion = self.red.miPerfilAttr('description')
        usr_descripcion = self.txtDescripcion
        if usr_descripcion == None:
            usr_descripcion = u'(Sin Descripción)'
        self.lblDescripcion = wx.StaticText(self.panel, wx.ID_ANY, usr_descripcion, wx.DefaultPosition, (-1,25), 0 )
        self.lblDescripcion.SetFont(self.Let_Tahoma_8)

        self.v_sizerInfo.Add(self.lblUsuario, 0, wx.TOP|wx.LEFT, 5 )
        self.v_sizerInfo.Add(self.lblDescripcion, 1, wx.EXPAND|wx.LEFT, 2 )

        self.h_sizerPerfil.Add(self.v_sizerInfo, 1, wx.ALL|wx.EXPAND, 0 )

        #agregar Loader de Envio
        loaderEnvioRuta = 'img/loader_envio.gif'
        self.loaderEnvio = wx.animate.GIFAnimationCtrl(self.panel, -1, loaderEnvioRuta, pos=(-1, -1))
        self.h_sizerPerfil.Add(self.loaderEnvio, 0, wx.RIGHT|wx.TOP|wx.ALIGN_TOP, 5)
        self.loaderEnvio.GetPlayer().UseBackgroundColour(True)


        #configurando la fila de estado
        self.h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.txt_estado = wx.TextCtrl(self.panel, wx.ID_ANY, '', (-1, -1), (-1, 50), style=wx.TE_MULTILINE|wx.TE_NO_VSCROLL|wx.TE_PROCESS_ENTER)
        self.txt_estado.SetFont(self.Let_Tahoma_10)
        self.h_sizer1.Add(self.txt_estado, 1, wx.ALL|wx.EXPAND, 5)
        #
        self.v_sizer3 = wx.BoxSizer(wx.VERTICAL) # Este contiene el boton y el label que cuenta
        self.btnAceptar = wx.BitmapButton(self.panel, wx.ID_ANY, wx.Bitmap( u"img/aceptar.png", wx.BITMAP_TYPE_ANY ), pos=wx.DefaultPosition, size=(40,25), style=wx.BU_AUTODRAW )
        self.btnAceptar.SetToolTipString(u'Enviar (F5)')
        self.lblCuenta = wx.StaticText(self.panel, wx.ID_ANY, '140', wx.DefaultPosition, wx.DefaultSize, 0 )
        #self.lblCuenta.SetFont( wx.Font(10, 70, 90, wx.NORMAL, False, wx.EmptyString ) )
        self.lblCuenta.SetFont(self.Let_Tahoma_10)
        self.v_sizer3.Add(self.btnAceptar, 0, wx.ALL, 5)
        self.v_sizer3.Add(self.lblCuenta, 0, wx.ALL, 5)
        self.h_sizer1.Add(self.v_sizer3, 0, 0, 5)

        #Configurando eventos
        self.panel.Bind(wx.EVT_BUTTON, self.BotonEstado, self.btnAceptar)
        self.txt_estado.Bind(wx.EVT_TEXT, self.EscribeEstado)
        self.txt_estado.Bind(wx.EVT_KEY_DOWN, self.AtajosTeclado)

        #Barra de Herramientas
        self.h_sizerBarra = wx.BoxSizer(wx.HORIZONTAL)
        btn_tam = wx.Size(40,40)
        self.btnInicio = wx.BitmapButton(self.panel, wx.ID_ANY, wx.Bitmap( u"img/inicio24x24.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, btn_tam, wx.BU_AUTODRAW)
        self.btnInicio.SetToolTipString( u"Inicio" )
        self.btnPublico = wx.BitmapButton(self.panel, wx.ID_ANY, wx.Bitmap( u"img/publico24x24.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, btn_tam, wx.BU_AUTODRAW)
        self.btnPublico.SetToolTipString( u"Público" )
        self.btnRespuestas = wx.BitmapButton(self.panel, wx.ID_ANY, wx.Bitmap( u"img/respuestas24x24.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, btn_tam, wx.BU_AUTODRAW)
        self.btnRespuestas.SetToolTipString( u"Respuestas" )
        self.btnMensajes = wx.BitmapButton(self.panel, wx.ID_ANY, wx.Bitmap( u"img/dm24x24.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, btn_tam, wx.BU_AUTODRAW)
        self.btnMensajes.SetToolTipString( u"Mensajes" )
        self.btnFavoritos = wx.BitmapButton(self.panel, wx.ID_ANY, wx.Bitmap( u"img/favoritos24x24.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, btn_tam, wx.BU_AUTODRAW)
        self.btnFavoritos.SetToolTipString( u"Favoritos" )
        self.h_sizerBarra.Add(self.btnInicio, 0, wx.BOTTOM|wx.LEFT, 5)
        self.h_sizerBarra.Add(self.btnPublico, 0, wx.BOTTOM, 5)
        self.h_sizerBarra.Add(self.btnRespuestas, 0, wx.BOTTOM, 5)
        self.h_sizerBarra.Add(self.btnFavoritos, 0, wx.BOTTOM, 5)
        self.h_sizerBarra.Add(self.btnMensajes, 0, wx.BOTTOM, 5)
        #
        self.Bind(wx.EVT_BUTTON, self.CambioLinea, self.btnPublico)
        self.Bind(wx.EVT_BUTTON, self.CambioLinea, self.btnInicio)
        self.Bind(wx.EVT_BUTTON, self.CambioLinea, self.btnRespuestas)
        self.Bind(wx.EVT_BUTTON, self.CambioLinea, self.btnFavoritos)
        self.Bind(wx.EVT_BUTTON, self.CambioLinea, self.btnMensajes)
        #
        self.h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        #
        self.tl_actual = self.tls[0]
        self.cols.append(self.NuevaColumna(self.tl_actual))
        self.v_sizer = wx.BoxSizer(wx.VERTICAL)
        #
        #Se agregan los Sizers horizontales al Sizer Vertical Principal
        self.v_sizer.Add(self.h_sizerPerfil, 0, wx.EXPAND|wx.ALL, 0)
        self.v_sizer.Add(self.h_sizer1, 0, wx.EXPAND|wx.ALL, 0)
        self.v_sizer.Add(self.h_sizerBarra, 0, 0, 0) #Sizer Barra
        self.v_sizer.Add(self.h_sizer2, 1, wx.EXPAND|wx.ALL, 0)
        self.panel.SetSizer(self.v_sizer)
        self.sBar = self.CreateStatusBar( 1, wx.ST_SIZEGRIP, wx.ID_ANY )
        self.txt_estado.SetFocus()
        log.debug('Ventana Configurada')
        log.debug('Cerrando Ventana de Login')
        self.Centre(wx.BOTH)
        self.InnerHTML(self.html_loader_tl)
        self.Show()
        self.parent.Hide()

    def CambioLinea(self, event):
        obj = event.GetEventObject()
        indiceViejo = self.tls.index(self.cols[0].GetOrigen())

        if obj == self.btnInicio:
            indiceNuevo = self.tls.index('tl_home')

        if obj == self.btnPublico:
            indiceNuevo = self.tls.index('tl_public')

        if obj == self.btnRespuestas:
            indiceNuevo = self.tls.index('replies')

        if obj == self.btnFavoritos:
            indiceNuevo = self.tls.index('favorites')

        if obj == self.btnMensajes:
            indiceNuevo = self.tls.index('messages')

        if indiceNuevo == indiceViejo:
            log.debug('Seleccionando mismo TL. Se ignora cambio')
            return False

        self.indiceActual = indiceNuevo
        self.cols[0].SetOrigen(self.tls[self.indiceActual])

        log.debug('Cambio de Linea de Tiempo')
        #
        self.InnerHTML('')
        if self.cols_vacia[self.indiceActual] == True:
            self.InnerHTML(self.html_loader_tl)
        else:
            self.InnerHTML(self.txt[self.indiceActual])

        try:
            self.timer.cancel()
            self.timer = None
            log.debug('Se detuvo el Timer')
        except:
            log.debug('Error al intentar detener Timer')
        self.Actualizar()


    def NuevaColumna(self, origen):
        col = cColumna(self.panel, origen)
        self.h_sizer2.Add(col, 1, wx.EXPAND | wx.ALL, 0)
        log.debug('Se agrego una colmuna')
        return col

    def VerificarDirectorios(self):
        log.debug('Verificando si existen los directorios')
        self.dir_usuario = self.dir_perfiles + str(self.red.miPerfilAttr('id'))
        self.dir_imagenes = self.dir_usuario + '/imagenes/'
        if (not os.path.isdir(self.dir_perfiles)):
            os.makedirs(self.dir_imagenes)
            log.debug('Se crearon las carpetas Perfiles, Usuario, Imagenes')
        if (not os.path.isdir(self.dir_usuario)):
            os.mkdir(self.dir_usuario)
            log.debug('Se creo la carpeta Perfil')
        if (not os.path.isdir(self.dir_imagenes)):
            os.mkdir(self.dir_imagenes)
            log.debug('Se creo la carpeta Imagenes')

class MiHtmlWindow(wx.html.HtmlWindow):

    enlace = ''
    def __init__(self, parent, id, size=(600,400)):
        wx.html.HtmlWindow.__init__(self,parent, id, size=size)
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        _FONT_SIZES = [5, 6,  8, 10, 14, 20, 24]
        # Original font sizes are [7, 8, 10, 12, 16, 22, 30]
        self.SetFonts("Tahoma", "Courier New", _FONT_SIZES)

    def OnLinkClicked(self, link):
        #
        #wx.MessageBox(str(self.GetVirtualSize()[0]))
        #return False
        #
        evento = link.GetEvent()
        if evento.Button != 1:
            return False
        self.enlace = link.GetHref()
        wx.CallAfter(Publisher().sendMessage, "LinkPresionado", "Final de Thread")
    
    def GetBottom(self):
        bottom = self.GetBestSize()[1]-self.GetViewStart()[1]
        return bottom
    
    def SetBottom(self, param):
        bottom = self.GetBestSize()[1]-param
        self.Scroll(0, bottom)

class cColumna(MiHtmlWindow):

    origen = ''
    intervalo = 0

    def __init__(self, parent, origen, intervalo=15):
        wx.html.HtmlWindow.__init__(self, parent)
        self.SetMinSize((200, -1))
        self.SetBorders(0)
        self.origen = origen
        self.intervalo = intervalo

    def SetOrigen(self, orig):
        self.origen = orig

    def GetOrigen(self):
        return self.origen


class PlaxedLogin(wx.Frame):
    Validado = False
    usr = ''
    pas = ''
    serv = ''
    def __init__(self, parent):
        self.parent = parent
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Plaxed Desktop (Pre-Alpha)', size=(320, 450))
        self.ConfigurarVentana()

    def ConfigurarVentana(self):
        Publisher().subscribe(self.HiloLogin, "Hilo_Login")
        log.debug('Configurando Ventana')
        icono = wx.Icon('img/iconosolo16.png', wx.BITMAP_TYPE_PNG)
        self.SetIcon(icono)
        self.SetMinSize((320, 450))
        self.panel = wx.Panel(self)
        self.bsizer = wx.BoxSizer(wx.VERTICAL)
        self.txt_usuario = wx.TextCtrl(self.panel, wx.ID_ANY, '', size=(160, -1))
        self.txt_usuario.SetFocus()
        self.txt_usuario.SetMaxLength(30)
        self.txt_clave = wx.TextCtrl(self.panel, wx.ID_ANY, '', size=(160, -1), style=wx.TE_PASSWORD)
        self.txt_clave.SetMaxLength(30)
        self.boton = wx.Button(self.panel, wx.ID_ANY, 'Ingresar')
        self.imagen = wx.StaticBitmap(self.panel, wx.ID_ANY, wx.Bitmap( u"img/iconosolo64.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )

        self.lbl_usuario = wx.StaticText(self.panel, wx.ID_ANY, u"Usuario:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_usuario.Wrap( -1 )
        self.lbl_clave = wx.StaticText(self.panel, wx.ID_ANY, u"Clave:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_clave.Wrap( -1 )

        self.bsizer.Add(self.imagen, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 30)
        self.bsizer.Add(self.lbl_usuario, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 3)
        self.bsizer.Add(self.txt_usuario, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 3)
        self.bsizer.Add(self.lbl_clave, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 3)
        self.bsizer.Add(self.txt_clave, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 3)
        self.bsizer.Add(self.boton, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 30)

        #Agregar un Loader:
        self.ag_fname = 'img/loader_timeline_transparente.gif'
        self.ag = wx.animate.GIFAnimationCtrl(self.panel, -1, self.ag_fname, pos=(-1, -1))
        self.bsizer.Add(self.ag, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 0)
        # clears the background
        self.ag.GetPlayer().UseBackgroundColour(True)


        #self.SetSizer(self.bsizer)
        self.panel.SetSizer(self.bsizer)
        self.Bind(wx.EVT_BUTTON, self.Entrar, self.boton)
        self.sBar = self.CreateStatusBar( 1, wx.ST_SIZEGRIP, wx.ID_ANY )
        self.Centre(wx.BOTH)
        log.debug('Ventana Configurada')
        self.Show()

    def Conectar(self, servidor, usuario, clave):
        log.debug('Verificando Sesion')
        self.red = statusNet(servidor, usuario, clave)
        if self.red.EstaConectado():
            log.debug('Credenciales Validas')
            self.Validado = True
        else:
            log.debug('Credenciales Invalidas')

    def PlayLoader(self):
        self.ag.Play()

    def StopLoader(self):
        self.ag.Stop()

    def Entrar(self, event):
        self.sBar.SetStatusText('Examinando los datos...')
        self.txt_usuario.Disable()
        self.txt_clave.Disable()
        usuario = self.txt_usuario.GetValue()
        usuario = usuario.strip()
        clave = self.txt_clave.GetValue()
        clave = clave.strip()
        #
        if usuario == "" or clave == "":
            self.sBar.SetStatusText(u'Debe ingresar sus usuario y clave...')
            self.txt_usuario.Enable()
            self.txt_clave.Enable()
            return False
        self.boton.Disable()
        servidor = 'http://beta.plaxed.com'
        self.usuario = usuario
        self.clave = clave
        self.servidor = servidor
        self.PlayLoader()
        self.sBar.SetStatusText('Validando credenciales...')
        self.t = HiloValidar(self, self.servidor, self.usuario, self.clave)


    def HiloLogin(self, msj):
        respuesta = msj.data
        if respuesta == 'LoginTimeOut':
            log.debug(u'No se recibió respuesta del servidor')
            self.StopLoader()
            self.sBar.SetStatusText(u'No se recibió respuesta del servidor')
            self.txt_usuario.Enable()
            self.txt_clave.Enable()
            self.txt_usuario.SetFocus()
            self.boton.Enable()
        if respuesta == 'LoginAceptado':
            log.debug('Accesando a Interfaz Principal')
            self.sBar.SetStatusText(u'Cargando Aplicación...')
            frmMain = InterfazPrincipal(self, APLICACION_VENTANA_TITULO, self.servidor, self.usuario, self.clave)
        if respuesta == 'LoginRechazado':
            log.debug('Error de Autenticacion')
            self.StopLoader()
            self.sBar.SetStatusText(u'Error de Autenticación...')
            self.txt_usuario.Enable()
            self.txt_clave.Enable()
            self.txt_usuario.SetFocus()
            self.boton.Enable()
        if respuesta == 'ErrorDesconocido':
            log.debug('Reintente nuevamente')
            self.StopLoader()
            self.sBar.SetStatusText(u'Error desconocido...')
            self.txt_usuario.Enable()
            self.txt_clave.Enable()
            self.txt_usuario.SetFocus()
            self.boton.Enable()


    def __del__(self):
        try:
            frmMain.Destroy()
        except:
            pass

class HiloTimeLine(threading.Thread):
    servidor = ''
    usuario = ''
    clave = ''
    parent = None
    txt = ''
    ultimo = 0
    time_line = ''
    color_tab_1 = "#FFFFFF"
    color_tab_2 = "#E6F8E0"
    color_tab = ""
    dir_perfiles = './perfiles/'
    dir_usuario = ''
    dir_imagenes = ''
    app_dir_img = './img/'
    def __init__(self, parent, servidor, usuario, clave, time_line, primera_carga):
        threading.Thread.__init__(self)
        self.parent = parent
        self.servidor = servidor
        self.clave = clave
        self.usuario = usuario
        self.time_line = time_line
        self.primera_carga = primera_carga
        self.ultimo=self.parent.ultimo[self.parent.indiceActual]
        self.daemon = True
        self.start()

    def run(self):
        self.red = statusNet(self.servidor, self.usuario, self.clave)
        if self.red.EstaConectado():
            self.dir_usuario = self.dir_perfiles + str(self.red.miPerfilAttr('id'))
            self.dir_imagenes = self.dir_usuario + '/imagenes/'
            log.debug("Solicitando Datos del Servidor")
            if self.time_line == 'tl_home':
                mitl = self.red.TimeLineHome(self.ultimo)
            if self.time_line == 'tl_public':
                mitl = self.red.TimeLinePublic(self.ultimo)
            if self.time_line == 'replies':
                mitl = self.red.Respuestas(self.ultimo)
            if self.time_line == 'favorites':
                mitl = self.red.Favoritos(self.ultimo)
            if self.time_line == 'messages':
                mitl = self.red.Buzon(self.ultimo)
            if mitl == '{TimeOut}':
                wx.CallAfter(Publisher().sendMessage, "TL_No_Recibido", "Final de Thread")
                return False
            tmp = ''
            ultimo = 0
            cont = 0
            if len(mitl) > 0:
                log.debug("Se recibieron mensajes nuevos")
                log.debug("Parseando los datos")
                for tl in mitl:
                    if self.color_tab != self.color_tab_1:
                        self.color_tab = self.color_tab_1
                    else:
                        self.color_tab = self.color_tab_2
                    cont = cont + 1
                    #Si son mensajes, los usuarios se llaman sender y recipient
                    usuario2 = 'recipient'
                    if self.time_line == 'messages':
                        usuario1 = 'sender'
                    else:
                        usuario1 = 'user'
                    self.DescargarAvatar(tl[usuario1]['profile_image_url'])
                    img_tmp = tl[usuario1]['profile_image_url']
                    img_arr = img_tmp.split("/")
                    img_nombre = img_arr[len(img_arr) - 1]
                    if (os.path.isfile(self.dir_imagenes + img_nombre)):
                        img_ruta_local = self.dir_imagenes + img_nombre
                    else:
                        img_ruta_local = self.app_dir_img + 'default.png'

                    tmp += '<table bgcolor="' + self.color_tab + '" width="100%" border="0">'
                    tmp += '<tr>'
                    tmp += '<td width="48" valign="top" rowspan="2"><img align="left" src="' + img_ruta_local + '"></td>'
                    tmp += '<td valign="top">'
                    if self.time_line == 'messages':
                        tmp += '<font size="2"><b>' + tl[usuario1 +'_screen_name'] + '</b><br>'
                    else:
                        tmp += '<font size="2"><b>' + tl[usuario1]['screen_name'] + '</b><br>'
                    #
                    if self.time_line == 'messages':
                        msj = tl['text']
                    else:
                        msj = tl['statusnet_html']

                    tmp = u"%s %s</font>" % (tmp, msj) #text o statusnet_html
                    tmp += '</td>'
                    tmp += '</tr>'
                    #
                    tmp += '<tr>'
                    tmp += '<td align="right" valign="top">'
                    tmp += '<font size="1" color="gray">'


                    #tmp += '</font>'
                    #tmp +='</td>'
                    #tmp += '</tr>'
                    #
                    #tmp += '<tr>'
                    #tmp +='<td valign="top" align="right">'
                    #tmp += '<font size="1" color="gray">'
                    #tmp += '<br>'
                    #
                    if self.time_line!= 'messages':

                        tmp += '<a href="%s/notice/new/%s/%s"><img src="img/link_responder.png"></a>' % (self.servidor, tl[usuario1]['screen_name'], tl['id'])

                        # si es mi tweet, puedo borrar, si no, puedo repetir
                        if self.red.miPerfilAttr('id')!=tl[usuario1]['id']:
                            tmp += '&nbsp;&nbsp;&nbsp;<a href="%s/notice/retweet/%s"><img src="img/link_repetir.png"></a>' % (self.servidor, tl['id'])

                        else:
                            tmp += '&nbsp;&nbsp;&nbsp;<a href="%s/notice/delete/%s"><img src="img/link_borrar.gif"></a>' % (self.servidor, tl['id'])


                        tmp += '&nbsp;&nbsp;&nbsp;<a href="%s/favorites/create/%s"><img src="img/link_favorito.png"></a>' % (self.servidor, tl['id'])


                        tmp += '&nbsp;&nbsp;&nbsp;<a href="%s/conversation/%s"><img src="img/link_contexto.png"></a>' % (self.servidor, tl['statusnet_conversation_id'])
                    #
                    tmp += '<br>'
                    if self.time_line != 'messages':
                        tmp += u'Vía %s' % tl['source']
                        if tl['in_reply_to_user_id'] != None:
                            tmp += ', en respuesta a <i>' + tl['in_reply_to_screen_name'] +  '</i>'
                    #
                    tmp += '</font>'
                    tmp += '</td>'
                    tmp += '</tr>'
                    tmp += '</table>'


                    #
                    if ultimo == 0:
                        ultimo = tl['id']
                        self.ultimo = ultimo
                log.debug('Ultimo ID: ' + str(self.ultimo))
                log.debug("Finalizando descarga de mensajes")
                self.txt = tmp

                wx.CallAfter(Publisher().sendMessage, "TL_Mensajes", "Final de Thread")
            else:
                wx.CallAfter(Publisher().sendMessage, "TL_Vacio", "Final de Thread")
                log.debug("No existen mensajes nuevos")
        else:
            wx.CallAfter(Publisher().sendMessage, "APP_Desconectado", "Final de Thread")


    def RutaOnlineToLocal(self, ruta):
        img_arr = ruta.split("/")
        img_nombre = img_arr[len(img_arr) - 1]
        if (os.path.isfile(self.dir_imagenes + img_nombre)):
            img_ruta_local = self.dir_imagenes + img_nombre
        else:
            img_ruta_local = self.app_dir_img + 'default.png'
        return img_ruta_local

    def DescargarAvatar(self, ruta_img):
        tmp = ruta_img.split("/")
        img_nombre = tmp[len(tmp) - 1]
        #
        carpetas=''
        for i in range(3,len(tmp)-1):
            carpetas = carpetas + '/' + tmp[i]
        carpetas = carpetas + '/'
        img_ruta = carpetas + img_nombre
        img_ruta_local = self.dir_imagenes + img_nombre
        tmp_serv = self.red.servidor.split("//")
        serv = "www." + tmp_serv[1]
        tmp2 = img_nombre.split('-')
        idu = tmp2[0] #esto es el ID del usuario, antes del primer guion
        if (not os.path.isfile(img_ruta_local)):
            if self.primera_carga:
                log.debug('Intentando eliminar la imagen antigua')
                try:
                    self.BorrarImgAnterior(idu)
                except:
                    log.debug('No se encontro la imagen o no se pudo borrar')
            # Descargando nueva imagen
            try:
                con = httplib.HTTPConnection(serv)
                con.request("GET", img_ruta)
                r = con.getresponse()
                archivo = file(img_ruta_local, 'wb')
                archivo.write(r.read())
                archivo.close()
                log.debug("Imagen descargada")
            except:
                log.debug("Error al descargar imagen")
        else:
            log.debug('Ya existe la imagen')

    def BorrarImgAnterior(self, idusuario):
        ficheros = os.listdir(self.dir_imagenes)
        for nombreA in ficheros:
            if (re.search('^'+ idusuario +'-', nombreA)):
                os.remove(self.dir_imagenes + nombreA)
                log.debug('Se borro la imagen anterior')

class HiloValidar(threading.Thread):
    servidor = ''
    usuario = ''
    clave = ''
    parent = None
    def __init__(self, parent, servidor, usuario, clave):
        threading.Thread.__init__(self)
        self.parent = parent
        self.servidor=servidor
        self.clave=clave
        self.usuario=usuario
        self.daemon = True
        self.start()

    def run(self):
        self.red = statusNet(self.servidor, self.usuario, self.clave)
        if self.red.respuesta_login == '{TimeOut}':
            wx.CallAfter(Publisher().sendMessage, "Hilo_Login", "LoginTimeOut")
            return False
        if self.red.respuesta_login == '{Error}':
            wx.CallAfter(Publisher().sendMessage, "Hilo_Login", "ErrorDesconocido")
            return False
        if self.red.respuesta_login == '{CredencialValida}':
            wx.CallAfter(Publisher().sendMessage, "Hilo_Login", "LoginAceptado")
            return True
        if self.red.respuesta_login == '{CredencialInvalida}':
            wx.CallAfter(Publisher().sendMessage, "Hilo_Login", "LoginRechazado")
            return True

class HiloEnviarMensaje(threading.Thread):
    servidor = ''
    usuario = ''
    clave = ''
    parent = None
    txt = ''
    directo = False
    idmensaje = True
    def __init__(self, parent, servidor, usuario, clave, txt, directo=False, idmensaje=''):
        threading.Thread.__init__(self)
        self.parent = parent
        self.servidor=servidor
        self.clave=clave
        self.usuario=usuario
        self.txt = txt
        self.directo = directo
        self.idmensaje = idmensaje
        self.daemon = True
        self.start()

    def run(self):
        self.red = statusNet(self.servidor, self.usuario, self.clave)
        if self.red.EstaConectado():
            if self.directo:
                res = self.red.PublicarRespuesta(self.txt, self.idmensaje)
                if res == "{TimeOut}":
                    wx.CallAfter(Publisher().sendMessage, "Hilo_Enviar_Mensaje_Directo", "TimeOut")
                if res != "{Error}":
                    wx.CallAfter(Publisher().sendMessage, "Hilo_Enviar_Mensaje_Directo", "MensajeEnviado")
                else:
                    wx.CallAfter(Publisher().sendMessage, "Hilo_Enviar_Mensaje_Directo", "MensajeNoEnviado")
            else:
                res = self.red.Publicar(self.txt)
                if res == "{TimeOut}":
                    wx.CallAfter(Publisher().sendMessage, "Hilo_Enviar_Mensaje", "TimeOut")
                if res != "{Error}":
                    wx.CallAfter(Publisher().sendMessage, "Hilo_Enviar_Mensaje", "MensajeEnviado")
                else:
                    wx.CallAfter(Publisher().sendMessage, "Hilo_Enviar_Mensaje", "MensajeNoEnviado")

        else:
            wx.CallAfter(Publisher().sendMessage, "Hilo_Enviar_Mensaje", "APP_Desconectado")

class VentanaResponder(wx.Frame):

    idmensaje = 0
    carRestantes = 140
    def __init__(self, parent, destinatario):
        wx.Frame.__init__(self, parent=parent, id=-1, title='Responder', size=(340,150), style=wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW | wx.SYSTEM_MENU| wx.CLOSE_BOX)
        self.parent = parent
        self.panel = wx.Panel(self, -1)
        self.bs_vertical = wx.BoxSizer(wx.VERTICAL)
        self.txtRespuesta = wx.TextCtrl(self.panel, wx.ID_ANY, '', (-1, -1), (-1, 50), style=wx.TE_MULTILINE|wx.TE_NO_VSCROLL|wx.TE_PROCESS_ENTER)
        Let_Tahoma_10 = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Tahoma')
        self.txtRespuesta.SetFont(Let_Tahoma_10)
        self.btnAceptar = wx.Button(self.panel, -1,'Enviar')
        self.bs_vertical.Add(self.txtRespuesta, 1, wx.LEFT|wx.TOP|wx.RIGHT|wx.EXPAND, 5)
        #
        self.bs_horizontal = wx.BoxSizer(wx.HORIZONTAL)
        loaderEnvioRuta = 'img/loader_envio.gif'
        self.loaderEnvio = wx.animate.GIFAnimationCtrl(self.panel, -1, loaderEnvioRuta, pos=(-1, -1))
        self.bs_horizontal.Add(self.loaderEnvio, 1, wx.ALL|wx.ALIGN_BOTTOM, 5)
        self.loaderEnvio.GetPlayer().UseBackgroundColour(True)
        #
        self.lblCuenta = wx.StaticText(self.panel, wx.ID_ANY, '140', wx.DefaultPosition, wx.DefaultSize, 0 )
        self.bs_horizontal.Add(self.lblCuenta, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 2)

        self.bs_horizontal.Add(self.btnAceptar, 0, wx.ALL|wx.ALIGN_RIGHT, 2)
        self.bs_vertical.Add(self.bs_horizontal, 0, wx.ALL|wx.EXPAND, 0)

        self.panel.SetSizer(self.bs_vertical)
        #
        self.btnAceptar.Bind(wx.EVT_BUTTON, self.OnOK)
        self.txtRespuesta.Bind(wx.EVT_TEXT, self.Escribiendo)
        #
        self.destinatario = destinatario
        self.ConfigurarVentana()

    def Escribiendo(self, evt):
        texto = self.txtRespuesta.GetValue()
        restante = 140 - len(texto)
        self.carRestantes = restante
        self.lblCuenta.SetLabel(str(restante))
        evt.Skip()

    def ConfigurarVentana(self):
        self.Bind(wx.EVT_CLOSE, self.CerrandoVentana)
        datos = self.destinatario.split(',')
        self.idmensaje = datos[1]
        self.SetTitle('Responder a @' + datos[0])

    def Show(self, callback=None, cancelCallback=None):
        self.callback = callback
        self.cancelCallback = cancelCallback

        self.CenterOnParent()
        self.GetParent().Enable(False)
        wx.Frame.Show(self)
        self.Raise()
        self.txtRespuesta.SetFocus()

    def OnOK(self, event):
        texto = self.txtRespuesta.GetValue()
        texto = texto.encode('utf8')
        texto = texto.strip()
        if texto == '':
            wx.MessageBox('Debe ingresar un mensaje')
            self.txtRespuesta.SetFocus()
        else:
            if self.carRestantes < 0:
                wx.MessageBox('No puede exceder los 140 caracteres')
                self.txtRespuesta.SetFocus()
                return False
            self.Bloquear(True)
            self.callback(texto, self.idmensaje)

    def Bloquear(self, bloquear):
        if bloquear:
            self.txtRespuesta.Disable()
            self.btnAceptar.Disable()
            self.loaderEnvio.Play()
        else:
            self.txtRespuesta.Enable()
            self.btnAceptar.Enable()
            self.txtRespuesta.SetFocus()
            self.loaderEnvio.Stop()


    def CerrandoVentana(self, event):
        self.GetParent().Enable(True)
        event.Skip()



class PlaxedApp(wx.App):
    usuario = ''
    clave = ''
    servidor = ''
    frmMain = None

    def __init__(self):
        wx.App.__init__(self, True)
        self.frmLogin = PlaxedLogin(self)
        self.MainLoop()
