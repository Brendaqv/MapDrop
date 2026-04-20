import pandas as pd
import io
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Referencia de meses (consistente con analisis_ppmaximas)
MESES_NOMBRES = {
    1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Oct', 11: 'Nov', 12: 'Dic'
}

BASE_LAYOUT = dict(
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family="Arial, sans-serif", size=14, color="#1a1a1a"),
    xaxis=dict(showgrid=True, gridcolor='#eeeeee', linecolor='#cccccc',
               tickfont=dict(size=13, color="#1a1a1a"),
               title_font=dict(size=14, color="#1a1a1a")),
    yaxis=dict(showgrid=True, gridcolor='#eeeeee', linecolor='#cccccc',
               tickfont=dict(size=13, color="#1a1a1a"),
               title_font=dict(size=14, color="#1a1a1a")),
    margin=dict(l=60, r=60, t=50, b=60),
    hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial"),
)


# ─────────────────────────────────────────────
# DETECCIÓN DE ARCHIVO DE TEMPERATURA
# ─────────────────────────────────────────────

def es_archivo_temperatura(archivo):
    """
    Detecta si un CSV contiene datos de temperatura SENAMHI.
    Cubre: CSV convencional (HUMEDAD RELATIVA) y EMA Meteorológica (HUMEDAD %).
    """
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
        lineas = texto.splitlines()[:10]
        texto_cabecera = ' '.join(lineas).upper()
        tiene_temp = 'TEMPERATURA' in texto_cabecera
        tiene_hr = 'HUMEDAD RELATIVA' in texto_cabecera or 'HUMEDAD' in texto_cabecera
        return tiene_temp and tiene_hr
    except Exception:
        try:
            archivo.seek(0)
        except Exception:
            pass
        return False


def es_ema_meteorologica(archivo):
    """Distingue EMA meteorológica (horaria) de CSV convencional (diaria)."""
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
        lineas = texto.splitlines()[:10]
        texto_cabecera = ' '.join(lineas).upper()
        return 'EMA' in texto_cabecera and 'HORA' in texto_cabecera
    except Exception:
        try:
            archivo.seek(0)
        except Exception:
            pass
        return False


# ─────────────────────────────────────────────
# PROCESAMIENTO DE SERIE HISTÓRICA DE TEMPERATURA
# ─────────────────────────────────────────────

def procesar_csv_temperatura(archivo):
    """
    Lee un CSV de temperatura SENAMHI (formato CP-Meteorológica).
    Formato cabecera:
      Fila 1-5: metadata
      Fila 6: AÑO / MES / DÍA, TEMPERATURA (°C), HUMEDAD RELATIVA (%), PRECIPITACIÓN (mm/día)
      Fila 7: MAX, MIN, TOTAL
      Fila 8+: 2025-06-01, 32.8, 23.4, 74.3, 0.0

    Retorna DataFrame con columnas: año, mes, dia, tmax, tmin, hr, pp
    """
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

        # Encontrar fila de inicio de datos (primera que empieza con año numérico)
        inicio = 7
        for i, linea in enumerate(lineas):
            partes = linea.strip().split(',')
            if len(partes) >= 4 and partes[0].strip()[:4].isdigit():
                inicio = i
                break

        df = pd.read_csv(
            io.StringIO('\n'.join(lineas[inicio:])),
            header=None,
            names=['fecha', 'tmax', 'tmin', 'hr', 'pp'],
            usecols=[0, 1, 2, 3, 4]
        )

        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['año'] = df['fecha'].dt.year
        df['mes'] = df['fecha'].dt.month
        df['dia'] = df['fecha'].dt.day

        for col in ['tmax', 'tmin', 'hr', 'pp']:
            df[col] = df[col].astype(str).str.upper().replace({'S/D': None, 'T': '0.05'})
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.dropna(subset=['año', 'mes', 'dia', 'tmax'])  # tmin puede ser S/D
        df[['año', 'mes', 'dia']] = df[['año', 'mes', 'dia']].astype(int)

        return df[['año', 'mes', 'dia', 'tmax', 'tmin', 'hr', 'pp']].reset_index(drop=True)

    except Exception as e:
        print(f"Error procesando temperatura: {e}")
        try:
            archivo.seek(0)
        except Exception:
            pass
        return None


def procesar_csv_ema_temperatura(archivo):
    """
    Lee CSV EMA Meteorológica SENAMHI (horario) y agrega a diario.
    Columnas: AÑO/MES/DÍA, HORA, TEMPERATURA, PRECIPITACIÓN, HUMEDAD, DIR_VIENTO, VEL_VIENTO
    Retorna: año, mes, dia, tmax, tmin, hr, pp, vel_viento_med
    """
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
        for i, linea in enumerate(lineas):
            partes = linea.strip().split(',')
            if len(partes) >= 4 and '/' in partes[0] and partes[0][:4].isdigit():
                inicio = i
                break
        df = pd.read_csv(io.StringIO('\n'.join(lineas[inicio:])), header=None)
        col_names = ['fecha', 'hora', 'temp', 'pp_h', 'hr', 'dir_v', 'vel_v']
        df = df.iloc[:, :len(col_names)]
        df.columns = col_names[:df.shape[1]]
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['año'] = df['fecha'].dt.year
        df['mes']  = df['fecha'].dt.month
        df['dia']  = df['fecha'].dt.day
        for col in ['temp', 'pp_h', 'hr', 'vel_v']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.upper().replace({'S/D': None, 'T': '0.05'})
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=['año', 'mes', 'dia', 'temp'])
        df[['año', 'mes', 'dia']] = df[['año', 'mes', 'dia']].astype(int)
        agg_dict = {
            'tmax': ('temp', 'max'),
            'tmin': ('temp', 'min'),
            'hr':   ('hr',   'mean'),
            'pp':   ('pp_h', 'sum'),
        }
        if 'vel_v' in df.columns:
            agg_dict['vel_viento_med'] = ('vel_v', 'mean')
        df_diario = df.groupby(['año', 'mes', 'dia']).agg(**agg_dict).reset_index()
        return df_diario.sort_values(['año', 'mes', 'dia']).reset_index(drop=True)
    except Exception as e:
        print(f"Error procesando EMA temperatura: {e}")
        try:
            archivo.seek(0)
        except Exception:
            pass
        return None


def procesar_multiples_temperatura(archivos_temp):
    """
    Combina múltiples archivos de temperatura en una sola serie diaria.
    Soporta CSV convencional CP-Meteorológica y EMA Meteorológica (horaria).
    """
    lista = []
    for archivo in archivos_temp:
        try: archivo.seek(0)
        except Exception: pass
        if es_ema_meteorologica(archivo):
            df = procesar_csv_ema_temperatura(archivo)
        else:
            try: archivo.seek(0)
            except Exception: pass
            df = procesar_csv_temperatura(archivo)
        if df is not None and not df.empty:
            lista.append(df)
    if not lista:
        return None
    resultado = pd.concat(lista, ignore_index=True)
    resultado = resultado.drop_duplicates(subset=['año', 'mes', 'dia'], keep='first')
    return resultado.sort_values(['año', 'mes', 'dia']).reset_index(drop=True)


# ─────────────────────────────────────────────
# ESTADÍSTICOS MENSUALES
# ─────────────────────────────────────────────

def calcular_estadisticos_mensuales(df, df_pp=None):
    """
    Calcula estadísticos mensuales multianuales.
    df_pp: serie PP priorizada (df_todo). Si se pasa, la usa para el ombrotérmico
           en lugar de la PP del archivo de temperatura, evitando inconsistencias.
    """
    if df is None or df.empty:
        return None

    agg_dict = {
        'tmax_med': ('tmax', 'mean'),
        'tmin_med': ('tmin', 'mean'),
        'hr_med':   ('hr',   'mean'),
    }
    if 'vel_viento_med' in df.columns:
        agg_dict['vel_viento_med'] = ('vel_viento_med', 'mean')

    resumen = df.groupby('mes').agg(**agg_dict).reset_index()
    resumen['tmedia'] = (resumen['tmax_med'] + resumen['tmin_med']) / 2

    # PP para ombrotérmico: usa df_pp si disponible
    fuente_pp = df_pp if (df_pp is not None and not df_pp.empty and 'pp' in df_pp.columns) else df
    n_años_pp = fuente_pp['año'].nunique() if 'año' in fuente_pp.columns else 1
    pp_por_mes = fuente_pp.groupby('mes')['pp'].sum()
    resumen['pp_total_med'] = resumen['mes'].map(pp_por_mes / max(n_años_pp, 1)).fillna(0)

    resumen['nombre_mes'] = resumen['mes'].map(MESES_NOMBRES)

    cols_round = ['tmax_med', 'tmin_med', 'tmedia', 'hr_med', 'pp_total_med']
    if 'vel_viento_med' in resumen.columns:
        cols_round.append('vel_viento_med')
    for col in cols_round:
        resumen[col] = resumen[col].round(1)

    return resumen


def calcular_metricas_globales(df):
    """
    Retorna dict con métricas globales de la serie de temperatura.
    """
    if df is None or df.empty:
        return {}

    tmax_abs = df['tmax'].max()
    tmin_abs = df['tmin'].min()
    tmedia_anual = ((df['tmax'] + df['tmin']) / 2).mean()
    hr_media = df['hr'].mean()

    # Mes más cálido y más fresco (por Tmax media)
    por_mes = df.groupby('mes')['tmax'].mean()
    mes_calido = MESES_NOMBRES[por_mes.idxmax()]
    mes_fresco = MESES_NOMBRES[por_mes.idxmin()]

    anio_inicio = int(df['año'].min())
    anio_fin = int(df['año'].max())

    tiene_viento = 'vel_viento_med' in df.columns
    if tiene_viento:
        vel_media   = round(df['vel_viento_med'].mean(), 1)
        vel_max     = round(df['vel_viento_med'].max(), 1)
        por_mes_v   = df.groupby('mes')['vel_viento_med'].mean()
        mes_ventoso = MESES_NOMBRES[por_mes_v.idxmax()]
    else:
        vel_media = vel_max = mes_ventoso = None

    return {
        'tmax_abs': round(tmax_abs, 1),
        'tmin_abs': round(tmin_abs, 1),
        'tmedia_anual': round(tmedia_anual, 1),
        'hr_media': round(hr_media, 1),
        'mes_calido': mes_calido,
        'mes_fresco': mes_fresco,
        'anio_inicio': anio_inicio,
        'anio_fin': anio_fin,
        'n_años': anio_fin - anio_inicio + 1,
        'tiene_viento': tiene_viento,
        'vel_media': vel_media,
        'vel_max': vel_max,
        'mes_ventoso': mes_ventoso,
    }


# ─────────────────────────────────────────────
# GRÁFICO 1 — TEMPERATURA MÁXIMA Y MÍNIMA MENSUAL
# ─────────────────────────────────────────────

def grafico_temperatura_mensual(df_mensual):
    """
    Doble línea: Tmax media mensual (rojo) y Tmin media mensual (azul).
    Área sombreada entre ambas curvas = rango térmico diario.
    """
    if df_mensual is None or df_mensual.empty:
        return None

    meses = df_mensual['nombre_mes'].tolist()

    fig = go.Figure()

    # Área entre Tmax y Tmin
    fig.add_trace(go.Scatter(
        x=meses + meses[::-1],
        y=df_mensual['tmax_med'].tolist() + df_mensual['tmin_med'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(255, 180, 50, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        showlegend=True,
        name='Rango térmico diario',
        hoverinfo='skip',
    ))

    # Línea Tmax
    fig.add_trace(go.Scatter(
        x=meses, y=df_mensual['tmax_med'],
        mode='lines+markers',
        name='Tmax media (°C)',
        line=dict(color='#e74c3c', width=2.5),
        marker=dict(size=8, color='#e74c3c'),
        hovertemplate='Tmax: %{y:.1f} °C<extra></extra>'
    ))

    # Línea Tmedia
    fig.add_trace(go.Scatter(
        x=meses, y=df_mensual['tmedia'],
        mode='lines+markers',
        name='Tmedia (°C)',
        line=dict(color='#f39c12', width=1.5, dash='dot'),
        marker=dict(size=6, color='#f39c12'),
        hovertemplate='Tmedia: %{y:.1f} °C<extra></extra>'
    ))

    # Línea Tmin
    fig.add_trace(go.Scatter(
        x=meses, y=df_mensual['tmin_med'],
        mode='lines+markers',
        name='Tmin media (°C)',
        line=dict(color='#2980b9', width=2.5),
        marker=dict(size=8, color='#2980b9'),
        hovertemplate='Tmin: %{y:.1f} °C<extra></extra>'
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        xaxis_title='Mes',
        yaxis_title='Temperatura (°C)',
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
            font=dict(size=12, color='#1a1a1a'),
        ),
        hovermode='x unified',
    )
    fig.update_xaxes(title_font=dict(size=14, color='#1a1a1a'), tickfont=dict(size=13, color='#1a1a1a'))
    fig.update_yaxes(title_font=dict(size=14, color='#1a1a1a'), tickfont=dict(size=13, color='#1a1a1a'))

    return fig


# ─────────────────────────────────────────────
# GRÁFICO 2 — DIAGRAMA OMBROTÉRMICO WALTER-LIETH
# ─────────────────────────────────────────────

def grafico_ombrotermica(df_mensual):
    """
    Diagrama ombrotérmico de Walter-Lieth.
    Convención: escala PP = 2 × escala T (eje izquierdo T °C, eje derecho PP mm).
    Período seco: PP < 2T (área punteada/naranja).
    Período húmedo: PP > 2T (área azul).
    """
    if df_mensual is None or df_mensual.empty:
        return None

    meses = df_mensual['nombre_mes'].tolist()
    tmedia = df_mensual['tmedia'].tolist()
    pp = df_mensual['pp_total_med'].tolist()

    # Walter-Lieth: PP escala = 2 × T escala
    # Para comparar en el mismo eje: convertir PP a "equivalente T" dividiendo por 2
    pp_equiv = [p / 2 for p in pp]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # ── Área húmeda (PP/2 > T) ──
    pp_humedo = [pp_equiv[i] if pp_equiv[i] > tmedia[i] else tmedia[i] for i in range(len(meses))]
    fig.add_trace(go.Scatter(
        x=meses + meses[::-1],
        y=pp_humedo + tmedia[::-1],
        fill='toself',
        fillcolor='rgba(41, 128, 185, 0.25)',
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=True,
        name='Período húmedo (PP > 2T)',
        hoverinfo='skip',
    ), secondary_y=False)

    # ── Área seca (T > PP/2) ──
    t_seco = [tmedia[i] if tmedia[i] > pp_equiv[i] else pp_equiv[i] for i in range(len(meses))]
    fig.add_trace(go.Scatter(
        x=meses + meses[::-1],
        y=t_seco + pp_humedo[::-1],
        fill='toself',
        fillcolor='rgba(230, 126, 34, 0.20)',
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=True,
        name='Período seco (PP < 2T)',
        hoverinfo='skip',
    ), secondary_y=False)

    # ── Línea de temperatura media ──
    fig.add_trace(go.Scatter(
        x=meses, y=tmedia,
        mode='lines+markers',
        name='Temperatura media (°C)',
        line=dict(color='#e74c3c', width=2.5),
        marker=dict(size=7, color='#e74c3c'),
        hovertemplate='<b>%{x}</b><br>Tmedia: %{y:.1f} °C<extra></extra>'
    ), secondary_y=False)

    # ── Barras de precipitación (eje derecho) ──
    fig.add_trace(go.Bar(
        x=meses, y=pp,
        name='Precipitación media (mm)',
        marker_color='rgba(41, 128, 185, 0.5)',
        marker_line=dict(color='#2980b9', width=1),
        hovertemplate='<b>%{x}</b><br>PP media: %{y:.1f} mm<extra></extra>'
    ), secondary_y=True)

    # Layout
    t_min_plot = min(tmedia) - 3
    t_max_plot = max(tmedia) + 5
    pp_max_plot = (t_max_plot) * 2  # mantiene proporción Walter-Lieth

    _axis = dict(
        showgrid=True, gridcolor='#eeeeee', linecolor='#cccccc',
        tickfont=dict(size=13, color='#1a1a1a'),
        title_font=dict(size=14, color='#1a1a1a'),
    )

    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=13, color="#1a1a1a"),
        margin=dict(l=60, r=70, t=50, b=60),
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial", font_color="#1a1a1a"),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
            font=dict(size=12, color='#1a1a1a'),
        ),
        hovermode='x unified',
        barmode='overlay',
    )

    fig.update_yaxes(
        title_text='Temperatura media (°C)',
        range=[t_min_plot, t_max_plot],
        showgrid=True, gridcolor='#eeeeee',
        tickfont=dict(size=13, color='#1a1a1a'),
        title_font=dict(size=14, color='#1a1a1a'),
        secondary_y=False
    )
    fig.update_yaxes(
        title_text='Precipitación media mensual (mm)',
        range=[0, pp_max_plot],
        showgrid=False,
        tickfont=dict(size=13, color='#1a1a1a'),
        title_font=dict(size=14, color='#1a1a1a'),
        secondary_y=True
    )
    fig.update_xaxes(
        title_text='Mes',
        showgrid=True, gridcolor='#eeeeee',
        linecolor='#cccccc',
        tickfont=dict(size=13, color='#1a1a1a'),
        title_font=dict(size=14, color='#1a1a1a'),
    )

    return fig


# ─────────────────────────────────────────────
# GRÁFICO 3 — HUMEDAD RELATIVA MENSUAL
# ─────────────────────────────────────────────

def grafico_hr_mensual(df_mensual):
    """Gráfico de barras de humedad relativa media mensual."""
    if df_mensual is None or df_mensual.empty:
        return None

    meses = df_mensual['nombre_mes'].tolist()
    hr = df_mensual['hr_med'].tolist()

    colores = ['#2980b9' if h >= 70 else '#f39c12' if h >= 60 else '#e74c3c' for h in hr]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=meses, y=hr,
        marker_color=colores,
        marker_line=dict(color='#cccccc', width=0.5),
        hovertemplate='<b>%{x}</b><br>HR media: %{y:.1f} %<extra></extra>'
    ))

    # Scatter trace siempre renderiza encima de las barras (add_shape no lo hace)
    fig.add_trace(go.Scatter(
        x=meses + [meses[-1]],
        y=[70] * len(meses) + [70],
        mode='lines',
        line=dict(color='#2980b9', width=1.5, dash='dash'),
        showlegend=False,
        hoverinfo='skip',
    ))
    fig.add_annotation(
        x=meses[-1],
        y=73,
        text='── 70% húmedo',
        showarrow=False,
        font=dict(size=11, color='#2980b9'),
        bgcolor='rgba(255,255,255,0.9)',
        borderpad=3,
    )

    fig.update_layout(
        **BASE_LAYOUT,
        xaxis_title='Mes',
        yaxis_title='Humedad relativa media (%)',
        showlegend=False,
    )
    fig.update_xaxes(title_font=dict(size=14, color='#1a1a1a'), tickfont=dict(size=13, color='#1a1a1a'))
    fig.update_yaxes(range=[0, 105], showgrid=True, gridcolor='#eeeeee',
                     title_font=dict(size=14, color='#1a1a1a'), tickfont=dict(size=13, color='#1a1a1a'))

    return fig

# ─────────────────────────────────────────────
# GRÁFICO 4 — VELOCIDAD DE VIENTO MENSUAL
# ─────────────────────────────────────────────

def grafico_viento_mensual(df_mensual):
    """Gráfico de barras de velocidad media del viento por mes (m/s)."""
    if df_mensual is None or df_mensual.empty:
        return None
    if 'vel_viento_med' not in df_mensual.columns:
        return None
    df_v = df_mensual.dropna(subset=['vel_viento_med'])
    if df_v.empty:
        return None

    meses    = df_v['nombre_mes'].tolist()
    vel      = df_v['vel_viento_med'].tolist()
    vel_med  = sum(vel) / len(vel)

    colores = ['#2e4d31' if v >= vel_med * 1.2 else '#6db38a' if v >= vel_med else '#b2d8c8'
               for v in vel]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=meses, y=vel,
        marker_color=colores,
        marker_line=dict(color='#cccccc', width=0.5),
        hovertemplate='<b>%{x}</b><br>Velocidad media: %{y:.1f} m/s<extra></extra>'
    ))
    fig.add_hline(
        y=vel_med, line_dash='dash', line_color='#3d7a5a',
        annotation_text=f'Media: {vel_med:.1f} m/s',
        annotation_position='top left',
        annotation_font=dict(size=12, color='#3d7a5a')
    )
    layout = {**BASE_LAYOUT}
    layout['xaxis'] = {**BASE_LAYOUT['xaxis'], 'title': 'Mes'}
    layout['yaxis'] = {**BASE_LAYOUT['yaxis'], 'title': 'Velocidad media (m/s)'}
    fig.update_layout(**layout, showlegend=False)
    fig.update_xaxes(title_font=dict(size=14, color='#1a1a1a'), tickfont=dict(size=13, color='#1a1a1a'))
    fig.update_yaxes(title_font=dict(size=14, color='#1a1a1a'), tickfont=dict(size=13, color='#1a1a1a'))
    return fig