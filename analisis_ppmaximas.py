import pandas as pd
import io
import plotly.express as px

def procesar_archivos(lista_archivos_subidos):
    lista_df = []
    for archivo in lista_archivos_subidos:
        try:
            nombre = archivo.name.lower()
            # LECTURA DEL TXT
            if nombre.endswith('.txt'):
                contenido = archivo.read().decode('utf-8')
                lineas_limpias = [l.strip() for l in contenido.split('\n') if l.strip()]
                df = pd.read_csv(io.StringIO('\n'.join(lineas_limpias)), sep=r'\s+', header=None)
                df = df.iloc[:, [0, 1, 2, 3]]
                df.columns = ['año', 'mes', 'dia', 'pp']
                archivo.seek(0)
            # LECTURA DEL CSV
            else:
                df = pd.read_csv(archivo, skiprows=8, header=None)
                df = df.iloc[:, [0, 4]]
                df.columns = ['fecha_full', 'pp']
                df['fecha_full'] = pd.to_datetime(df['fecha_full'], errors='coerce')
                df['año'] = df['fecha_full'].dt.year
                df['mes'] = df['fecha_full'].dt.month
                df['dia'] = df['fecha_full'].dt.day
                df = df[['año', 'mes', 'dia', 'pp']]

            # LIMPIEZA
            df['pp'] = df['pp'].astype(str).str.upper().replace('S/D', '0').replace('T', '0.05')
            df['pp'] = pd.to_numeric(df['pp'], errors='coerce').fillna(0)
            df.loc[df['pp'] < 0, 'pp'] = 0
            df = df.dropna(subset=['año', 'mes'])
            df[['año', 'mes', 'dia']] = df[['año', 'mes', 'dia']].astype(int)
            lista_df.append(df)
        except Exception as e:
            print(f"Error en {archivo.name}: {e}")

    if not lista_df: return None
    res = pd.concat(lista_df, ignore_index=True).drop_duplicates(subset=['año', 'mes', 'dia'])
    return res.sort_values(by=['año', 'mes', 'dia']).reset_index(drop=True)

def generar_matriz_maximos(df):
    if df is None or df.empty: return None
    df_max = df.groupby(['año', 'mes'])['pp'].max().reset_index()
    matriz = df_max.pivot(index='año', columns='mes', values='pp')
    meses = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun',
             7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
    return matriz.rename(columns=meses)

def generar_graficos(df):
    if df is None or df.empty: return None, None, None, None
    
    # 1. Gráfico de Tendencia (Línea)
    df_anual = df.groupby('año')['pp'].max().reset_index()
    fig_linea = px.line(df_anual, x='año', y='pp', title='📈 Máximas Precipitaciones Anuales (Histórico)',
                        markers=True, labels={'pp':'PP Máx (mm)', 'año':'Año'})
    
    # 2. Boxplot Mensual (Estacionalidad)
    meses_nombres = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun',
                     7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
    df_plot = df.copy()
    df_plot['Nombre Mes'] = df_plot['mes'].map(meses_nombres)
    fig_box = px.box(df_plot, x='Nombre Mes', y='pp', title='📊 Variabilidad Estacional de Lluvias (Boxplot)',
                     category_orders={"Nombre Mes": list(meses_nombres.values())},
                     color='Nombre Mes', labels={'pp':'Lluvia (mm)'})
    
    # 3. Histograma de Frecuencias (Distribución)
    # Útil para ver qué tan comunes son las lluvias fuertes (> 50mm)
    fig_hist = px.histogram(df[df['pp'] > 0], x='pp', nbins=50, 
                            title='📉 Distribución de Frecuencias (¿Cuántas veces llueve X cantidad?)',
                            labels={'pp':'Precipitación (mm)', 'count':'Frecuencia (Días)'},
                            color_discrete_sequence=['#00CC96'])

    # 4. Gráfico de Dispersión Temporal (Todos los datos)
    fig_scatter = px.scatter(df, x='año', y='pp', color='mes',
                             title='☁️ Dispersión Histórica de Eventos Diarios',
                             labels={'pp':'Lluvia Diaria (mm)', 'año':'Año'},
                             color_continuous_scale=px.colors.sequential.Viridis)
    
    return fig_linea, fig_box, fig_hist, fig_scatter