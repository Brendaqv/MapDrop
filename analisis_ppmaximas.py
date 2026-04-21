import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_LAYOUT = dict(
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family="Arial, sans-serif", size=14, color="#1a1a1a"),
    xaxis=dict(showgrid=True, gridcolor='#eeeeee', linecolor='#cccccc',
               tickfont=dict(size=13, color="#1a1a1a"), title_font=dict(size=14, color="#1a1a1a")),
    yaxis=dict(showgrid=True, gridcolor='#eeeeee', linecolor='#cccccc',
               tickfont=dict(size=13, color="#1a1a1a"), title_font=dict(size=14, color="#1a1a1a")),
    margin=dict(l=60, r=40, t=50, b=60),
    hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial", font_color="#1a1a1a"),
)

# Referencia única de nombres de meses para todo el módulo
MESES_NOMBRES = {
    1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Oct', 11: 'Nov', 12: 'Dic'
}

# ─────────────────────────────────────────────
# DETECCIÓN DE TIPO DE ARCHIVO
# ─────────────────────────────────────────────

def detectar_tipo_archivo(archivo):
    archivo.seek(0)
    nombre = archivo.name.lower()

    if nombre.endswith('.xlsx') or nombre.endswith('.xls'):
        archivo.seek(0)
        return {'tipo': 'xlsx', 'subtipo': 'excel'}

    try:
        raw = archivo.read()
        for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                contenido = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        archivo.seek(0)
        lineas = [l.strip() for l in contenido.splitlines() if l.strip()]
        if nombre.endswith('.txt') and lineas and lineas[0][0].isdigit():
            return {'tipo': 'txt', 'subtipo': 'convencional'}
        for linea in lineas[:8]:
            linea_up = linea.upper()
            if 'TIPO' in linea_up and 'EMA' in linea_up:
                return {'tipo': 'csv_ema', 'subtipo': 'EMA'}
            if 'HORA' in linea_up and 'PRECIPITACI' in linea_up:
                return {'tipo': 'csv_ema', 'subtipo': 'EMA'}
        return {'tipo': 'csv_convencional', 'subtipo': 'CP'}
    except Exception:
        archivo.seek(0)
        return {'tipo': 'desconocido', 'subtipo': 'desconocido'}


# ─────────────────────────────────────────────
# PROCESAMIENTO EMA (HORARIO → DIARIO)
# ─────────────────────────────────────────────

def _leer_csv_ema_single(archivo):
    """Lee un solo archivo EMA y retorna DataFrame horario."""
    try:
        archivo.seek(0)
        raw = archivo.read()
        for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                texto = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        archivo.seek(0)
        lineas = texto.splitlines()
        inicio = 6
        for i, l in enumerate(lineas):
            partes = l.strip().split(',')
            if len(partes) >= 2 and '/' in partes[0] and partes[0][0].isdigit():
                inicio = i
                break
        df = pd.read_csv(io.StringIO('\n'.join(lineas[inicio:])), header=None)
        df = df.iloc[:, [0, 1, 3]]
        df.columns = ['fecha', 'hora', 'pp']
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['año'] = df['fecha'].dt.year
        df['mes'] = df['fecha'].dt.month
        df['dia'] = df['fecha'].dt.day
        df['pp'] = df['pp'].astype(str).str.upper().replace({'S/D': '0', 'T': '0.05'})
        df['pp'] = pd.to_numeric(df['pp'], errors='coerce').fillna(0)
        df.loc[df['pp'] < 0, 'pp'] = 0
        df = df.dropna(subset=['año', 'mes', 'dia'])
        df[['año', 'mes', 'dia']] = df[['año', 'mes', 'dia']].astype(int)
        df['hora'] = df['hora'].astype(str).str[:2]
        df['hora'] = pd.to_numeric(df['hora'], errors='coerce').fillna(0).astype(int)
        return df[['año', 'mes', 'dia', 'hora', 'pp']].reset_index(drop=True)
    except Exception as e:
        print(f"Error leyendo EMA: {e}")
        archivo.seek(0)
        return None


def procesar_csv_ema_horario(archivos_ema):
    """Combina múltiples archivos EMA en una sola serie horaria."""
    lista = []
    archivos = archivos_ema if isinstance(archivos_ema, list) else [archivos_ema]
    for archivo in archivos:
        df = _leer_csv_ema_single(archivo)
        if df is not None:
            lista.append(df)
    if not lista:
        return None
    resultado = pd.concat(lista, ignore_index=True)
    resultado = resultado.drop_duplicates(subset=['año', 'mes', 'dia', 'hora'])
    return resultado.sort_values(['año', 'mes', 'dia', 'hora']).reset_index(drop=True)


def procesar_csv_ema_diario(archivos_ema):
    """Agrega datos horarios EMA a diarios (suma pp por día)."""
    df_horario = procesar_csv_ema_horario(archivos_ema)
    if df_horario is None or df_horario.empty:
        return None
    df_diario = df_horario.groupby(['año', 'mes', 'dia'])['pp'].sum().reset_index()
    return df_diario.sort_values(['año', 'mes', 'dia']).reset_index(drop=True)


# ─────────────────────────────────────────────
# PROCESAMIENTO XLSX (EXPORTACIONES MAPDROP)
# ─────────────────────────────────────────────

def _leer_xlsx_diario(archivo):
    """Lee un xlsx con columnas [año, mes, dia, pp] — formato exportación MapDrop."""
    try:
        archivo.seek(0)
        df = pd.read_excel(archivo)
        df.columns = [c.lower().strip() for c in df.columns]
        cols_req = ['año', 'mes', 'dia', 'pp']
        if not all(c in df.columns for c in cols_req):
            print(f"XLSX {archivo.name}: columnas inesperadas {df.columns.tolist()}")
            return None
        df = df[cols_req].copy()
        df['pp'] = pd.to_numeric(df['pp'], errors='coerce').fillna(0)
        df.loc[df['pp'] < 0, 'pp'] = 0
        df = df.dropna(subset=['año', 'mes', 'dia'])
        df[['año', 'mes', 'dia']] = df[['año', 'mes', 'dia']].astype(int)
        archivo.seek(0)
        return df.sort_values(['año', 'mes', 'dia']).reset_index(drop=True)
    except Exception as e:
        print(f"Error leyendo XLSX {archivo.name}: {e}")
        try:
            archivo.seek(0)
        except Exception:
            pass
        return None


# ─────────────────────────────────────────────
# PROCESAMIENTO GENERAL — CON PRIORIDAD MULTI-FUENTE
# ─────────────────────────────────────────────

# Prioridad de fuentes (número menor = mayor confiabilidad):
#   TXT convencional: 1
#   CSV convencional: 2
#   XLSX:             3
#   EMA diario:       4
#
# Cuando un mismo día existe en varias fuentes, se conserva el de mayor prioridad.
# Esto permite complementar automáticamente una serie histórica:
#   Ej. TXT (1980-2014) + EMA (2016-2026) + CSV convencional (2020-2025)
#   → Serie 1980-2026, donde 2020-2025 usa CSV y el resto usa TXT/EMA.

def procesar_archivos(lista_archivos_subidos, modo='diario'):
    lista_df = []
    archivos_ema = []

    for archivo in lista_archivos_subidos:
        try:
            tipo_info = detectar_tipo_archivo(archivo)
            tipo = tipo_info['tipo']

            if tipo == 'txt':
                contenido = archivo.read().decode('utf-8')
                lineas_limpias = [l.strip() for l in contenido.split('\n') if l.strip()]
                df = pd.read_csv(io.StringIO('\n'.join(lineas_limpias)), sep=r'\s+', header=None)
                df = df.iloc[:, [0, 1, 2, 3]]
                df.columns = ['año', 'mes', 'dia', 'pp']
                archivo.seek(0)
                df['pp'] = df['pp'].astype(str).str.upper().replace({'S/D': '0', 'T': '0.05'})
                df['pp'] = pd.to_numeric(df['pp'], errors='coerce').fillna(0)
                df.loc[df['pp'] < 0, 'pp'] = 0
                df = df.dropna(subset=['año', 'mes'])
                df[['año', 'mes', 'dia']] = df[['año', 'mes', 'dia']].astype(int)
                df['_prioridad'] = 1
                lista_df.append(df)

            elif tipo == 'csv_ema':
                archivos_ema.append(archivo)

            elif tipo == 'xlsx':
                df = _leer_xlsx_diario(archivo)
                if df is not None:
                    df['_prioridad'] = 3
                    lista_df.append(df)

            else:  # csv_convencional
                df = pd.read_csv(archivo, skiprows=7, header=None, encoding='utf-8-sig')
                df = df.iloc[:, [0, 4]]
                df.columns = ['fecha_full', 'pp']
                df['fecha_full'] = pd.to_datetime(df['fecha_full'], errors='coerce')
                df['año'] = df['fecha_full'].dt.year
                df['mes'] = df['fecha_full'].dt.month
                df['dia'] = df['fecha_full'].dt.day
                df = df[['año', 'mes', 'dia', 'pp']]
                df['pp'] = df['pp'].astype(str).str.upper().replace({'S/D': '0', 'T': '0.05'})
                df['pp'] = pd.to_numeric(df['pp'], errors='coerce').fillna(0)
                df.loc[df['pp'] < 0, 'pp'] = 0
                df = df.dropna(subset=['año', 'mes'])
                df[['año', 'mes', 'dia']] = df[['año', 'mes', 'dia']].astype(int)
                df['_prioridad'] = 2
                lista_df.append(df)

        except Exception as e:
            print(f"Error en {archivo.name}: {e}")

    # Procesar todos los EMA juntos
    if archivos_ema:
        if modo == 'horario':
            return procesar_csv_ema_horario(archivos_ema)
        else:
            df_ema = procesar_csv_ema_diario(archivos_ema)
            if df_ema is not None:
                df_ema['_prioridad'] = 4
                lista_df.append(df_ema)

    if not lista_df:
        return None

    # Combinar con prioridad: menor número = fuente más confiable
    res = pd.concat(lista_df, ignore_index=True)
    res = res.sort_values(['año', 'mes', 'dia', '_prioridad'])
    res = res.drop_duplicates(subset=['año', 'mes', 'dia'], keep='first')
    res = res.drop(columns=['_prioridad'], errors='ignore')
    return res.sort_values(by=['año', 'mes', 'dia']).reset_index(drop=True)



# ─────────────────────────────────────────────
# RESUMEN DE FUENTES CARGADAS (para banner UI)
# ─────────────────────────────────────────────

_TIPO_LABELS = {
    'txt':              ('TXT Convencional',  '★★★★', 1),
    'csv_convencional': ('CSV Convencional',  '★★★',  2),
    'xlsx':             ('XLSX (MapDrop)',     '★★',   3),
    'csv_ema':          ('EMA Precipitación', '★',    4),
}

def obtener_resumen_fuentes(lista_archivos_subidos):
    """
    Analiza cada archivo subido y retorna:
    - fuentes: lista de dicts con nombre, tipo, prioridad, año_min, año_max
    - combinado: dict con año_min, año_max, n_fuentes de la serie final
    """
    import io as _io
    fuentes = []
    archivos_ema_temp = []

    for archivo in lista_archivos_subidos:
        try:
            archivo.seek(0)
            tipo_info = detectar_tipo_archivo(archivo)
            tipo = tipo_info['tipo']
            label, prioridad_str, prioridad_num = _TIPO_LABELS.get(tipo, (tipo, '?', 99))
            archivo.seek(0)

            if tipo == 'txt':
                contenido = archivo.read().decode('utf-8', errors='replace')
                lineas = [l.strip() for l in contenido.split('\n') if l.strip()]
                df_s = pd.read_csv(_io.StringIO('\n'.join(lineas)), sep=r'\s+', header=None, usecols=[0, 1, 2])
                df_s.columns = ['año', 'mes', 'dia']
                df_s = df_s.apply(pd.to_numeric, errors='coerce').dropna()
                año_min, año_max = int(df_s['año'].min()), int(df_s['año'].max())
                n_dias = len(df_s)

            elif tipo == 'csv_ema':
                archivos_ema_temp.append(archivo)
                archivo.seek(0)
                continue

            elif tipo == 'xlsx':
                df_s = _leer_xlsx_diario(archivo)
                if df_s is not None and not df_s.empty:
                    año_min, año_max = int(df_s['año'].min()), int(df_s['año'].max())
                    n_dias = len(df_s)
                else:
                    año_min, año_max, n_dias = 0, 0, 0

            else:  # csv_convencional
                df_s = pd.read_csv(archivo, skiprows=7, header=None, encoding='utf-8-sig', usecols=[0])
                df_s.columns = ['fecha_full']
                df_s['fecha_full'] = pd.to_datetime(df_s['fecha_full'], errors='coerce')
                df_s = df_s.dropna()
                if not df_s.empty:
                    año_min = int(df_s['fecha_full'].dt.year.min())
                    año_max = int(df_s['fecha_full'].dt.year.max())
                    n_dias = len(df_s)
                else:
                    año_min, año_max, n_dias = 0, 0, 0

            fuentes.append({
                'nombre': archivo.name,
                'tipo': label,
                'prioridad': prioridad_str,
                'prioridad_num': prioridad_num,
                'año_min': año_min,
                'año_max': año_max,
                'n_dias': n_dias,
            })
            archivo.seek(0)

        except Exception as e:
            print(f"obtener_resumen_fuentes — error en {archivo.name}: {e}")
            try: archivo.seek(0)
            except Exception: pass

    # Procesar EMAs agrupadas
    if archivos_ema_temp:
        try:
            for a in archivos_ema_temp: a.seek(0)
            df_ema = procesar_csv_ema_diario(archivos_ema_temp)
            if df_ema is not None and not df_ema.empty:
                nombres = ', '.join(a.name for a in archivos_ema_temp)
                fuentes.append({
                    'nombre': nombres,
                    'tipo': 'EMA Precipitación',
                    'prioridad': '★',
                    'prioridad_num': 4,
                    'año_min': int(df_ema['año'].min()),
                    'año_max': int(df_ema['año'].max()),
                    'n_dias': len(df_ema),
                })
            for a in archivos_ema_temp: a.seek(0)
        except Exception as e:
            print(f"obtener_resumen_fuentes — error EMA: {e}")

    fuentes_ord = sorted(fuentes, key=lambda x: x['prioridad_num'])
    if fuentes_ord:
        combinado = {
            'año_min': min(f['año_min'] for f in fuentes_ord if f['año_min'] > 0),
            'año_max': max(f['año_max'] for f in fuentes_ord if f['año_max'] > 0),
            'n_fuentes': len(fuentes_ord),
        }
    else:
        combinado = {'año_min': 0, 'año_max': 0, 'n_fuentes': 0}

    return fuentes_ord, combinado


# ─────────────────────────────────────────────
# FUNCIONES DE VALIDACIÓN Y MATRIZ
# ─────────────────────────────────────────────

def generar_resumen_validacion(df):
    resumen = df.groupby(['año', 'mes'])['dia'].nunique().unstack(fill_value=0)
    return resumen.rename(columns=MESES_NOMBRES)


def generar_matriz_maximos(df):
    if df is None or df.empty:
        return None
    df_max = df.groupby(['año', 'mes'])['pp'].max().reset_index()
    matriz = df_max.pivot(index='año', columns='mes', values='pp')
    return matriz.rename(columns=MESES_NOMBRES)


# ─────────────────────────────────────────────
# EXTRACCIÓN DE METADATOS DE ESTACIÓN
# ─────────────────────────────────────────────

def extraer_info_estacion(archivo, todos_los_archivos=None):
    info = {"Estación": "NO ENCONTRADA", "Departamento": "N/A",
            "Provincia": "N/A", "Distrito": "N/A", "Código": "N/A", "Tipo": "N/A"}

    def limpiar(valor):
        return valor.replace(':', '').replace('"', '').strip()

    def buscar_valor(partes, clave):
        for i, p in enumerate(partes):
            if clave in p.upper():
                if ':' in p:
                    val = limpiar(p.split(':', 1)[-1])
                    if val:
                        return val
                for j in range(i + 1, min(i + 3, len(partes))):
                    val = limpiar(partes[j])
                    if val:
                        return val
        return None

    def _leer_contenido(arch):
        arch.seek(0)
        raw = arch.getvalue()
        for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                return raw.decode(encoding).splitlines()
            except UnicodeDecodeError:
                continue
        return []

    def _parsear_info(contenido, info):
        for linea in contenido[:15]:
            partes = [p.strip() for p in linea.split(',')]
            linea_up = linea.upper()
            if "ESTACI" in linea_up and info["Estación"] == "NO ENCONTRADA":
                val = buscar_valor(partes, "ESTACI")
                if val:
                    info["Estación"] = val.upper()
            if "DEPARTAMENTO" in linea_up:
                val = buscar_valor(partes, "DEPARTAMENTO")
                if val:
                    info["Departamento"] = val.upper()
            if "PROVINCIA" in linea_up:
                val = buscar_valor(partes, "PROVINCIA")
                if val:
                    info["Provincia"] = val.upper()
            if "DISTRITO" in linea_up:
                val = buscar_valor(partes, "DISTRITO")
                if val:
                    info["Distrito"] = val.upper()
            if "DIGO" in linea_up:
                val = buscar_valor(partes, "DIGO")
                if val:
                    info["Código"] = val
            if "TIPO" in linea_up and info["Tipo"] == "N/A":
                val = buscar_valor(partes, "TIPO")
                if val:
                    info["Tipo"] = val.upper()
            if "LATITUD" in linea_up and "Latitud" not in info:
                val = buscar_valor(partes, "LATITUD")
                if val:
                    # Convertir grados-minutos-segundos a decimal si es necesario
                    try:
                        info["Latitud"] = float(val.replace(',', '.').split()[0])
                    except Exception:
                        info["Latitud"] = val
            if "LONGITUD" in linea_up and "Longitud" not in info:
                val = buscar_valor(partes, "LONGITUD")
                if val:
                    try:
                        info["Longitud"] = float(val.replace(',', '.').split()[0])
                    except Exception:
                        info["Longitud"] = val
        return info

    try:
        tipo_info = detectar_tipo_archivo(archivo)
        if tipo_info['tipo'] == 'xlsx':
            if todos_los_archivos:
                for otro in todos_los_archivos:
                    if otro.name.lower().endswith('.csv') or otro.name.lower().endswith('.txt'):
                        try:
                            contenido_csv = _leer_contenido(otro)
                            info = _parsear_info(contenido_csv, info)
                            otro.seek(0)
                            break
                        except Exception:
                            try:
                                otro.seek(0)
                            except Exception:
                                pass
            archivo.seek(0)
            return info

        contenido = _leer_contenido(archivo)
        primera_linea = contenido[0].strip() if contenido else ''
        es_txt_sin_cabecera = (archivo.name.lower().endswith('.txt') and
                               primera_linea and primera_linea[0].isdigit())
        if es_txt_sin_cabecera:
            if todos_los_archivos:
                for otro in todos_los_archivos:
                    if otro.name.lower().endswith('.csv'):
                        try:
                            contenido_csv = _leer_contenido(otro)
                            info = _parsear_info(contenido_csv, info)
                            otro.seek(0)
                            break
                        except Exception:
                            try:
                                otro.seek(0)
                            except Exception:
                                pass
            archivo.seek(0)
            return info
        info = _parsear_info(contenido, info)
        archivo.seek(0)
    except Exception:
        try:
            archivo.seek(0)
        except Exception:
            pass
    return info


# ─────────────────────────────────────────────
# GRÁFICOS DIARIOS
# ─────────────────────────────────────────────

def grafico_pp_max_anual(df, filtrar_ceros=False):
    if df is None or df.empty:
        return None, 0, 0
    df_anual = df.groupby('año')['pp'].max().reset_index()
    if filtrar_ceros:
        df_anual = df_anual[df_anual['pp'] > 0].reset_index(drop=True)
    # Percentiles completos — misma paleta que la tabla de umbrales
    u_p10  = df_anual['pp'].quantile(0.10)
    u_p25  = df_anual['pp'].quantile(0.25)
    u_medio = df_anual['pp'].quantile(0.50)  # P50
    u_p75  = df_anual['pp'].quantile(0.75)
    u_alto = df_anual['pp'].quantile(0.90)   # P90

    def _color(v):
        if v > u_alto:  return '#c0392b'  # rojo       > P90
        if v > u_p75:   return '#e67e22'  # naranja    P75-P90
        if v > u_medio: return '#d4a017'  # amarillo   P50-P75
        if v > u_p25:   return '#1a6b35'  # verde osc  P25-P50
        if v > u_p10:   return '#27ae60'  # verde clar P10-P25
        return '#2980b9'                  # azul       < P10

    colores = [_color(v) for v in df_anual['pp']]
    fig = go.Figure()
    fig.add_hline(y=u_alto, line_dash="dash", line_color="#c0392b",
                  annotation_text=f"Umbral Crítico P90 (> {u_alto:.1f} mm)",
                  annotation_position="top left",
                  annotation_font=dict(size=13, color="#c0392b"))
    fig.add_trace(go.Scatter(
        x=df_anual['año'], y=df_anual['pp'],
        mode='lines+markers',
        line=dict(color='rgba(150, 150, 150, 0.3)', width=1),
        marker=dict(size=10, color=colores, line=dict(width=1, color='DarkSlateGrey')),
        name="Máxima Anual",
        hovertemplate="<b>Año: %{x}</b><br>Precipitación: %{y} mm<extra></extra>"
    ))
    fig.update_layout(**BASE_LAYOUT, xaxis_title="Año", yaxis_title="PP Máx (mm)", hovermode="x")
    fig.update_xaxes(title_font=dict(size=14, color="#1a1a1a"), tickfont=dict(size=13, color="#1a1a1a"))
    fig.update_yaxes(title_font=dict(size=14, color="#1a1a1a"), tickfont=dict(size=13, color="#1a1a1a"))
    return fig, u_medio, u_alto


def grafico_boxplot(df):
    if df is None or df.empty:
        return None, "N/A"
    df_plot = df.copy()
    df_plot['Nombre Mes'] = df_plot['mes'].map(MESES_NOMBRES)
    resumen_mensual = df.groupby('mes')['pp'].median()
    mes_critico_num = resumen_mensual.idxmax()
    mes_critico_nombre = MESES_NOMBRES[mes_critico_num]
    fig = px.box(df_plot, x='Nombre Mes', y='pp', points="outliers",
                 category_orders={"Nombre Mes": list(MESES_NOMBRES.values())},
                 color='Nombre Mes', color_discrete_sequence=px.colors.qualitative.Bold,
                 labels={'pp': 'Lluvia (mm)', 'Nombre Mes': 'Mes'})
    fig.update_layout(**BASE_LAYOUT, showlegend=False)
    fig.update_xaxes(title_font=dict(size=14, color="#1a1a1a"), tickfont=dict(size=13, color="#1a1a1a"))
    fig.update_yaxes(title_font=dict(size=14, color="#1a1a1a"), tickfont=dict(size=13, color="#1a1a1a"))
    return fig, mes_critico_nombre


def grafico_histograma(df):
    if df is None or df.empty:
        return None, 0
    df_lluvia = df[df['pp'] > 0.1]
    media_intensidad = df_lluvia['pp'].mean()
    fig = px.histogram(df_lluvia, x='pp', nbins=50,
                       labels={'pp': 'Precipitación (mm)', 'count': 'Número de días'},
                       color_discrete_sequence=['#2ecc71'])
    fig.update_layout(**BASE_LAYOUT, showlegend=False)
    fig.update_xaxes(title_font=dict(size=14, color="#1a1a1a"), tickfont=dict(size=13, color="#1a1a1a"))
    fig.update_yaxes(title_font=dict(size=14, color="#1a1a1a"), tickfont=dict(size=13, color="#1a1a1a"))
    return fig, media_intensidad


# ─────────────────────────────────────────────
# GRÁFICOS Y MÉTRICAS HORARIAS EMA
# ─────────────────────────────────────────────

def calcular_metricas_horarias(df_horario):
    """Calcula indicadores estadísticos para datos horarios EMA."""
    if df_horario is None or df_horario.empty:
        return {}
    df_lluvia = df_horario[df_horario['pp'] > 0].copy()
    if df_lluvia.empty:
        return {}

    idx_max = df_lluvia['pp'].idxmax()
    max_pp_hora = df_lluvia.loc[idx_max, 'pp']
    max_fecha = (f"{int(df_lluvia.loc[idx_max, 'dia'])}/{int(df_lluvia.loc[idx_max, 'mes'])}"
                 f"/{int(df_lluvia.loc[idx_max, 'año'])} {int(df_lluvia.loc[idx_max, 'hora'])}:00h")

    intensidad_por_hora = df_lluvia.groupby('hora')['pp'].mean()
    hora_pico = int(intensidad_por_hora.idxmax())
    intensidad_hora_pico = round(intensidad_por_hora.max(), 2)

    p50_horario = round(df_lluvia['pp'].quantile(0.50), 2)
    p90_horario = round(df_lluvia['pp'].quantile(0.90), 2)
    media_horaria = round(df_lluvia['pp'].mean(), 2)

    eventos_p90 = len(df_lluvia[df_lluvia['pp'] > p90_horario])
    pct_p90 = round(eventos_p90 / len(df_lluvia) * 100, 1)

    return {
        'max_pp_hora': max_pp_hora,
        'max_fecha': max_fecha,
        'hora_pico': hora_pico,
        'intensidad_hora_pico': intensidad_hora_pico,
        'p50_horario': p50_horario,
        'p90_horario': p90_horario,
        'media_horaria': media_horaria,
        'eventos_p90': eventos_p90,
        'pct_p90': pct_p90,
    }


def grafico_eventos_horarios(df_horario):
    """Gráfico de dispersión temporal de eventos horarios con umbral P90."""
    if df_horario is None or df_horario.empty:
        return None, 0
    df_lluvia = df_horario[df_horario['pp'] > 0].copy()
    if df_lluvia.empty:
        return None, 0
    umbral = df_lluvia['pp'].quantile(0.90)
    df_lluvia['fecha_hora'] = pd.to_datetime(
        df_lluvia[['año', 'mes', 'dia']].rename(columns={'año': 'year', 'mes': 'month', 'dia': 'day'})
    ) + pd.to_timedelta(df_lluvia['hora'], unit='h')
    colores = ['#e74c3c' if v > umbral else '#2ecc71' for v in df_lluvia['pp']]
    fig = go.Figure()
    fig.add_hline(y=umbral, line_dash="dash", line_color="red",
                  annotation_text=f"Percentil 90 (> {umbral:.1f} mm/h)",
                  annotation_position="top left",
                  annotation_font=dict(size=13, color="red"))
    fig.add_trace(go.Scatter(
        x=df_lluvia['fecha_hora'], y=df_lluvia['pp'], mode='markers',
        marker=dict(size=6, color=colores, line=dict(width=0.5, color='DarkSlateGrey')),
        name="PP horaria",
        hovertemplate="<b>%{x}</b><br>Precipitación: %{y} mm/h<extra></extra>"
    ))
    fig.update_layout(**BASE_LAYOUT, xaxis_title="Fecha y hora",
                      yaxis_title="PP (mm/h)", hovermode="x")
    fig.update_xaxes(title_font=dict(size=14, color="#1a1a1a"), tickfont=dict(size=13, color="#1a1a1a"))
    fig.update_yaxes(title_font=dict(size=14, color="#1a1a1a"), tickfont=dict(size=13, color="#1a1a1a"))
    return fig, umbral


def grafico_intensidad_por_hora(df_horario):
    """Gráfico de intensidad promedio por hora del día (0-23h)."""
    if df_horario is None or df_horario.empty:
        return None
    df_lluvia = df_horario[df_horario['pp'] > 0].copy()
    if df_lluvia.empty:
        return None
    intensidad = df_lluvia.groupby('hora')['pp'].mean().reset_index()
    intensidad.columns = ['hora', 'pp_media']
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=intensidad['hora'], y=intensidad['pp_media'],
        marker_color='#7fd0e0',
        hovertemplate="<b>%{x}:00h</b><br>Intensidad media: %{y:.2f} mm/h<extra></extra>"
    ))
    layout = {**BASE_LAYOUT}
    layout['xaxis'] = {**BASE_LAYOUT['xaxis'], 'tickmode': 'linear', 'tick0': 0, 'dtick': 1,
                       'title': 'Hora del día'}
    layout['yaxis'] = {**BASE_LAYOUT['yaxis'], 'title': 'Intensidad media (mm/h)'}
    fig.update_layout(**layout)
    return fig

# ─────────────────────────────────────────────
# ANÁLISIS MULTI-ESTACIÓN
# ─────────────────────────────────────────────

def analizar_multiples_estaciones(lista_grupos):
    """
    Recibe lista de dicts con:
      { 'nombre', 'lat', 'lon', 'codigo', 'df' }
    Retorna DataFrame resumen con estadísticos por estación.
    """
    import numpy as np
    filas = []
    for g in lista_grupos:
        df = g.get('df')
        if df is None or df.empty:
            continue
        df_anual = df.groupby('año')['pp'].max().reset_index()
        n_años = len(df_anual)
        pp_max = round(df['pp'].max(), 1)
        media_anual = round(df.groupby('año')['pp'].sum().mean(), 1)
        p50 = round(df_anual['pp'].quantile(0.50), 1)
        p90 = round(df_anual['pp'].quantile(0.90), 1)
        año_min = int(df['año'].min())
        año_max = int(df['año'].max())

        filas.append({
            'Estación':        g.get('nombre', 'N/A'),
            'Código':          g.get('codigo', 'N/A'),
            'Latitud':         g.get('lat', None),
            'Longitud':        g.get('lon', None),
            'Período':         f"{año_min}–{año_max}",
            'N° años':         n_años,
            'PP Máx abs (mm)': pp_max,
            'PP Media anual (mm)': media_anual,
            'P50 (mm)':        p50,
            'P90 (mm)':        p90,
        })

    if not filas:
        return None
    return pd.DataFrame(filas)