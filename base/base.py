# -*- coding: utf-8 *-*

#Importaciones
import re
from datetime import datetime
from datetime import date
import time
import logging
import locale
import sys

if sys.platform.startswith('linux'):
    locale.setlocale(locale.LC_ALL,"en_US.utf8")

logging.basicConfig()
log = logging.getLogger('BASE')
if len(sys.argv) > 1:
    if sys.argv.index('--debug'):
        log.setLevel(logging.DEBUG)

#Variables GLOBALES
APLICACION_VENTANA_TITULO = 'Plaxed Desktop'
APLICACION_SOURCE = "Plaxed Desktop"
APLICACION_TIEMPO_ESPERA_TIMEOUT = 10
APLICACION_SERVIDOR = "http://www.plaxed.com"
#APLICACION_SERVIDOR = "http://localhost/statusnet"
if not APLICACION_SERVIDOR.startswith("http://"):
    APLICACION_SERVIDOR = "http://" + APLICACION_SERVIDOR
ARR_CARPETA = APLICACION_SERVIDOR.split("//")
APLICACION_CARPETA_PERFIL = ARR_CARPETA[1].replace("/",".")
log.debug('Generando nombre de carpeta de perfil: ' + APLICACION_CARPETA_PERFIL)

filtroFecha = re.compile('\[fecha\].+\[/fecha\]')
#Funciones

def str_utf8(texto):
    return "%s" % texto.encode('utf8')

#def ProcesarFecha(fecha):
#    filtro = re.compile('(\-)?\d{4} ')
#    tfecha = filtro.sub("", fecha)
#    tfecha = tfecha.replace(' ','-')
#    tfecha = tfecha.replace(':','-')
#    return tfecha

def ProcesarFecha(fecha):
    filtro = re.compile('(\-)?\d{4} ')
    tfecha = filtro.sub("", fecha)
    formato = '%a %b %d %H:%M:%S %Y'
    try:
        fechaMensaje = datetime.strptime(tfecha, formato)
        minutos = str(fechaMensaje.minute)
        if len(minutos)==1:
            minutos = "0" + minutos
        dia = str(fechaMensaje.day)
        if len(dia)==1:
            dia = "0" + dia
        mes = str(fechaMensaje.month)
        if len(mes)==1:
            mes = "0" + mes
        hora = str(fechaMensaje.hour)
        if hora == "0":
            hora = "12"
        fechaNueva = 'el ' + dia + '/' + mes
        fechaNueva += '/' + str(fechaMensaje.year) + ' a las ' + [hora, str(int(fechaMensaje.hour)-12)][fechaMensaje.hour>12]
        fechaNueva += ':' + minutos + ['a.m','p.m'][fechaMensaje.hour>=12]
    except ValueError, e:
        fechaNueva = '(sin fecha)'
    return fechaNueva
