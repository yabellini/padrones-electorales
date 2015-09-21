# -*- coding: utf-8 -*-
""" encontrar numeros de DNI duplicados en diferentes padrones """
import csv
import codecs
import os
import sys

padrones_a_usar = []
for arg in sys.argv:
    if arg == '-h' or arg == '--help':
        print "Analizar padrones en CSV (listados previamente en <padrones_index.csv>)"
        print "  <padrones_index.csv> es un CSV con los padrones cargados en el sistema"
        print "  Usa los campos:"
        print "    0: path. Path relativo al csv con el padron"
        print "    1: dni_column. Indice (basado en cero) de la columna con el DNI en el padron"
        print "    2: Nombre de la ciudad"
        print "    3: calle_column. Indice de la columna que tiene la calle(o toda la direccion)"
        print "    4: nro de casa, solo en caso de que exista. -1 si no se usa"
        print "    5: depto nro, solo en caso de que exista. -1 si no se usa"
        print "    6: barrio, solo en caso de que exista. -1 si no se usa"
        print "    7: No me acuerdo"
        print "    8: Detalle de la eleccion que usa este padron"
        print "    9: ID unico sin espacios (para usar con --just por ejemplo)"
        print ""
        print "  --PARAMS--"
        print ""
        print "  -h | --help inprime esta lista"
        print "  --just=Padron1,Padron2 Analizar SOLO los padrones listados. Identificar el padron con el campo ID (9 de la lista)"
        print ""
        exit(0)
        
    if arg.startswith('--just'):
        p = arg.split('=')
        padrones_a_usar=p[1].split(',')    
        


# cargar todos los padrones al sistema
pi = open('padrones_index.csv', 'r')
reader = csv.reader(pi)
padrones = []
for line in reader:
    # path, dni_column, nombre, calle_column, calle_nro_column, depto_column, barrio_column = line
    padron = {'path': line[0],'dni_column': int(line[1]), 'nombre': line[2],'calle_column': int(line[3]),
                'calle_nro_column': int(line[4]), 'depto_column': int(line[5]),
                'barrio_column': int(line[6]), 'detalle': line[8], 'id': line[9]}
    # print str(padron)
    # detectar si hay un <cleaner>
    if len(padrones_a_usar) > 0 and padron['id'] not in padrones_a_usar:
        print "OMITIENDO %s" % padron['id']
        continue
        
    ps = padron['path'].split('/')
    padron['folder'] = ps[1]
    cleaner = '%s/%s/cleaner.py' % (ps[0], padron['folder'])
    if not os.path.exists(cleaner):
        print '%s NO tienen cleaner %s' % (padron['nombre'], cleaner)
        cleaner = None
    else:
        print '%s SI tienen cleaner %s' % (padron['nombre'], cleaner)
        
    padron['cleaner'] = cleaner
    padrones.append(padron)
    


votantes = {} # DNI: los demas datos del votante y padron (todos juntos)
total_votantes_padron = {} # votantes total de cada padron
dnis = [] # lista de dnis cargados
domicilios = {} # contador de domicilios por padron

for p in padrones:
    f = open(p['path'], 'r')
    reader = csv.reader(f)

    domicilios[p['nombre']] = {'errores': [], 'domicilios': {}} # inicializar contador de domicilios
    total_votantes_padron[p['nombre']] = 0
    for line in reader:
        total_votantes_padron[p['nombre']] = total_votantes_padron[p['nombre']] + 1
        if total_votantes_padron[p['nombre']] % 5000 == 0:
            print '%s Processing %d' % (p['id'], total_votantes_padron[p['nombre']])
        # -------------------DNIs--------------------------------------------
        try:
            dni = line[p['dni_column']]
        except Exception, e:
            print "Error Padron %s" % p['nombre']
            print str(p)
            print str(line)
            exit(1)
        dni = str(dni).strip()
        dni = dni.replace('.', '')
        try:
            dni = int(dni)
        except Exception, e:
            print "Padron %s. DNI no valido '%s' %s" % (p['nombre'], dni, str(e))
            continue

        linea = unicode(line)
        este = {'Padron': p['nombre'], 'linea': linea}
        
        if dni in dnis: # puede haber duplicados denotr de un mismo padron
            votantes[dni].append(este)
        else:
            dnis.append(dni)
            votantes[dni] = [este]

        # -------------------DOMICILIOs--------------------------------------
        # algunas veces le faltan comas ...
        try:
            domicilio = line[p['calle_column']]
        except Exception, e:
            domicilios[p['nombre']]['errores'].append(line)
            print "ERROR leyendo domicilio %s (index: %d)" % (unicode(line), p['calle_column'])
            continue
            
        try:
            if p['barrio_column'] > -1:
                domicilio = '%s %s' % (line[p['barrio_column']], domicilio)
            if p['calle_nro_column'] > -1:
                domicilio = '%s %s' % (domicilio, line[p['calle_nro_column']])
            if p['depto_column'] > -1:
                domicilio = '%s %s' % (domicilio, line[p['depto_column']])
        except Exception, e:
            domicilios[p['nombre']]['errores'].append(line)
            continue
            
        # quitar espacios multiples
        try:
            domicilio = domicilio if type(domicilio) == unicode else domicilio.decode('utf-8')
        except Exception, e:
            print "type %s" % str(type(domicilio))
            print "DOM error %s" % domicilio
            print str(e)
            exit(1)
        
        domicilio = ' '.join(domicilio.split())
        domicilio = domicilio.upper()

        # Testing cleaner ----
        if p['cleaner']:
            imp = 'padronesListos.%s.cleaner' % p['folder']
            _temp = __import__(imp, globals(), locals(), ['Cleaner'], -1)
            Cleaner = _temp.Cleaner
            c = Cleaner()
            domicilio = c.clean(domicilio)
            
        if domicilios[p['nombre']]['domicilios'].get(domicilio, None):
            domicilios[p['nombre']]['domicilios'][domicilio]['total'] = domicilios[p['nombre']]['domicilios'][domicilio]['total'] + 1
            domicilios[p['nombre']]['domicilios'][domicilio]['usos'].append(linea)
        else:
            domicilios[p['nombre']]['domicilios'][domicilio] = {'total': 1, 'usos': [linea]}
    
# imprimir los resultados a CSV

# DNIs repetidos
with open('dnis_repetidos.csv', 'w') as csvfile:
    fieldnames = ['DNI','Padron', 'Extras']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for dni, votantes in votantes.iteritems():
        if len(votantes) > 1:
            writer.writerow({'DNI': '--------', 'Padron': '--------', 'Extras': '---------------------------'})
            for v in votantes:
                writer.writerow({'DNI': dni, 'Padron': v['Padron'], 'Extras': v['linea']})


# domicilios mas usados por ciudad TXT
for p in padrones:
    print "Analysing %s %s" % (p['nombre'], p['detalle'])
    
    lista = domicilios[p['nombre']]['domicilios']
    lista_ord = sorted(lista.iteritems(), key=lambda d: d[1].get('total', {}), reverse=True)

    f = codecs.open('domicilios-mas-usados/domicilios_en_%s.txt' % p['nombre'], 'w', encoding='utf8')
    f.write('DOMICILIOS MAS USADOS EN EL PADRON: %s\n' % p['nombre'])
    f.write('Cantidad de votantes en el padron: %d\n' % total_votantes_padron[p['nombre']])
    f.write('Cantidad de domicilios diferentes: %d\n' % len(lista))
    f.write('Errores al leer domicilios: %d\n' % len(domicilios[p['nombre']]['errores']))
    f.write('\n===========================================\n')
    

    # primero los domicilios y su conteo
    for domicilio in lista_ord:
        k, v = domicilio
        f.write('%s :: %d USOS \n' % (k, len(v['usos'])))
        
    # ahora los dpomicilios y el detalle
    for domicilio in lista_ord:
        k, v = domicilio
        f.write('\n===========================================\n')
        f.write('%s :: %d USOS \n' % (k, len(v['usos'])))
        for usos in v['usos']:
            f.write('  - %s\n' % usos)

    # mostrar errores
    f.write('\n===========================================\n')
    f.write('ERRORES: %d\n' % len(domicilios[p['nombre']]['errores']))
        
    for error in domicilios[p['nombre']]['errores']:
        f.write('%s\n' % error)
        
    f.close()


# domicilios mas usados por ciudad (NICE)
from jinja2 import Environment, FileSystemLoader
# from slugify import slugify
env = Environment(loader=FileSystemLoader('templates'))

template = env.get_template('domicilios.html')

for p in padrones:
    print "Nicing %s %s" % (p['nombre'], p['detalle'])
    
    lista = domicilios[p['nombre']]['domicilios']
    # solo los top 500 con mas votantes
    lista_ord = sorted(lista.iteritems(), key=lambda d: d[1].get('total', {}), reverse=True)[:500]

    tpl = template.render(title='Padron de %s %s'  % (p['nombre'], p['detalle']),
        cantidad_votantes=total_votantes_padron[p['nombre']],
        cantidad_domicilios=len(lista),
        direcciones=lista_ord)

    ciudad = p['nombre'].replace(' ', '-')
    detalle = p['detalle'].replace(' ', '-')
    nice_city = '%s-%s' % (ciudad, detalle)
    f = codecs.open('domicilios-mas-usados/view/%s.html' % nice_city, 'w', encoding='utf8')
    f.write(tpl)    
    f.close()