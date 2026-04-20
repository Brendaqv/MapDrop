"""
senamhi_stations.py
Módulo de búsqueda de estaciones SENAMHI para MapDrop.
Carga el archivo estaciones.json y provee funciones de búsqueda y generación de URLs.
"""

import json
import os
from urllib.parse import urlencode

BASE_URL = "https://www.senamhi.gob.pe/mapas/mapa-estaciones-2/map_red_graf.php"

# Etiquetas legibles por categoría
CATEGORIA_LABELS = {
    'CO':   'Climatológica Ordinaria',
    'CP':   'Climatológica Principal',
    'EMA':  'Estación Meteorológica Automática',
    'EAA':  'Estación Automática Agrícola',
    'EAMA': 'Estación Agrometeorológica Automática',
    'EHMA': 'Estación Hidrometeorológica Automática',
    'EHA':  'Estación Hidrológica Automática',
    'HLM':  'Hidrológica con Limnígrafo',
    'HLG':  'Hidrológica con Limniógrafo',
    'MAP':  'Meteorológica Aeroportuaria',
    'PE':   'Pluviométrica Especial',
    'PLU':  'Pluviométrica',
}

TIPO_LABELS = {
    'M': 'Meteorológica',
    'H': 'Hidrológica',
}

ESTADO_LABELS = {
    'REAL':       '🟢 Tiempo real',
    'DIFERIDO':   '🟡 Diferido',
    'AUTOMATICA': '🔵 Automática',
}

# Qué variables tiene cada tipo de estación
VARIABLES_POR_CATEGORIA = {
    'CO':   'Temperatura (Tmax/Tmin), Humedad relativa, Precipitación',
    'CP':   'Temperatura (Tmax/Tmin), Humedad relativa, Precipitación',
    'EMA':  'Temperatura, Precipitación (horaria), Humedad, Viento',
    'EAA':  'Temperatura, Precipitación, Humedad, Viento',
    'EAMA': 'Temperatura, Precipitación, Humedad, Viento, Radiación solar',
    'EHMA': 'Temperatura, Precipitación, Humedad, Nivel del río',
    'EHA':  'Nivel del río, Precipitación',
    'HLM':  'Nivel del río (mediciones diarias)',
    'HLG':  'Nivel del río (continuo)',
    'MAP':  'Temperatura, Humedad, Presión, Viento, Precipitación',
    'PE':   'Precipitación',
    'PLU':  'Precipitación',
}


def cargar_estaciones(json_path: str = None) -> list:
    """Carga el JSON de estaciones. Busca en la carpeta del script si no se especifica ruta."""
    if json_path is None:
        # Buscar en el directorio del script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, 'estaciones.json')

    if not os.path.exists(json_path):
        return []

    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def buscar_estaciones(query: str, estaciones: list, max_results: int = 10) -> list:
    """
    Busca estaciones por nombre o código.
    Retorna lista de matches ordenados por relevancia.
    """
    if not query or len(query) < 2:
        return []

    query_upper = query.upper().strip()
    exactos = []
    parciales = []

    for e in estaciones:
        nombre = e.get('nom', '').upper()
        codigo = e.get('cod', '').upper()
        codigo_old = e.get('cod_old', '').upper()

        # Match exacto de código
        if codigo == query_upper or codigo_old == query_upper:
            exactos.append(e)
        # Match al inicio del nombre
        elif nombre.startswith(query_upper):
            exactos.append(e)
        # Match parcial en nombre
        elif query_upper in nombre:
            parciales.append(e)

    results = exactos + parciales
    return results[:max_results]


def construir_url_senamhi(estacion: dict) -> str:
    """Construye la URL de descarga del SENAMHI para una estación."""
    params = {
        'cod':       estacion.get('cod', ''),
        'estado':    estacion.get('estado', ''),
        'tipo_esta': estacion.get('ico', ''),
        'cate':      estacion.get('cate', ''),
        'cod_old':   estacion.get('cod_old', ''),
    }
    return f"{BASE_URL}?{urlencode(params)}"


def get_info_estacion(estacion: dict) -> dict:
    """Enriquece un dict de estación con etiquetas legibles."""
    cate = estacion.get('cate', '')
    tipo = estacion.get('ico', '')
    estado = estacion.get('estado', '')
    return {
        'nombre':     estacion.get('nom', 'N/A'),
        'codigo':     estacion.get('cod', 'N/A'),
        'codigo_old': estacion.get('cod_old', ''),
        'categoria':  CATEGORIA_LABELS.get(cate, cate),
        'tipo':       TIPO_LABELS.get(tipo, tipo),
        'estado':     ESTADO_LABELS.get(estado, estado),
        'lat':        estacion.get('lat', 0),
        'lon':        estacion.get('lon', 0),
        'variables':  VARIABLES_POR_CATEGORIA.get(cate, 'Consultar en SENAMHI'),
        'url':        construir_url_senamhi(estacion),
        'es_ema':     cate in ('EMA', 'EAMA', 'EHMA', 'EHA', 'EAA'),
    }
