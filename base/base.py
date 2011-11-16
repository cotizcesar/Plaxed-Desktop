# -*- coding: utf-8 *-*

#Importaciones
import re
from datetime import datetime
import time
import logging

#Variables GLOBALES
APLICACION_VENTANA_TITULO = 'Plaxed Desktop'
APLICACION_SOURCE = "Plaxed Desktop"
APLICACION_TIEMPO_ESPERA_TIMEOUT = 15
APLICACION_SERVIDORES = [{'nombre': 'Plaxed', 'ruta': 'http://beta.plaxed.com', 'imagen': 'iconosolo16.png'}, {'nombre': 'Identica', 'ruta': 'http://identi.ca', 'imagen': 'identica.png'}]

logging.basicConfig()
log = logging.getLogger('BASE')
log.setLevel(logging.DEBUG)

#Funciones

def str_utf8(texto):
    return "%s" % texto.encode('utf8')

def ProcesarFecha(fecha):
    filtro = re.compile('(\-)?\d{4} ')
    tfecha = filtro.sub("", fecha)
    formato = '%a %b %d %H:%M:%S %Y'
    try:
        #fechaMensaje = datetime.strptime(tfecha, formato)
        fechaMensaje = _strptime(tfecha, formato)
        fechaNueva = 'el ' + str(fechaMensaje.day) + '/' + str(fechaMensaje.month)
        fechaNueva += '/' + str(fechaMensaje.year) + ' a las ' + [str(fechaMensaje.hour), str(int(fechaMensaje.hour)-12)][fechaMensaje.hour>12]
        fechaNueva += ':' + str(fechaMensaje.minute) + ['a.m','p.m'][fechaMensaje.hour>=12]
    except:
        fechaNueva = '(sin fecha)'
    return fechaNueva

def _strptime(str_fecha, str_formato):
    salida = datetime(*(time.strptime(str_fecha, str_formato)[0:6]))
    return salida
