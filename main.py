import streamlit as st
import analisis_ppmaximas as ana
import pandas as pd
import io
import calendar


# 1. Configuración de página (SIEMPRE debe ser lo primero que ve Streamlit)
st.set_page_config(
    page_title="MapLecture", 
    page_icon="💧", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilos personalizados (Paleta MapLecture)
st.markdown("""
    <style>

    /* === FORZAR TEMA CLARO COMPLETO (Windows/Mac/Linux) === */

    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"], .main, .block-container {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }

    /* Reducir espacio superior */
    .block-container {
        padding-top: 2rem !important;
    }
    [data-testid="stAppViewBlockContainer"] {
        padding-top: 2rem !important;
    }
    header[data-testid="stHeader"] {
        height: 0rem !important;
        min-height: 0rem !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebarContent"] {
        background-color: #f0f7f4 !important;
        border-right: 1px solid #e0e0e0 !important;
        color: #1a1a1a !important;
        min-width: 250px !important;
        max-width: 300px !important;
    }

    [data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
        margin-top: -1.5rem !important;
    }

    [data-testid="stSidebarUserContent"] .stMarkdown,
    [data-testid="stSidebarUserContent"] .stImage {
        margin-bottom: -10px;
    }

    /* Forzar color oscuro solo en texto de contenido, NO en gráficos */
    .stApp > header, .stApp > div > div > div > div,
    [data-testid="stMainBlockContainer"] p,
    [data-testid="stMainBlockContainer"] li,
    [data-testid="stMainBlockContainer"] span:not([class*="plotly"]),
    [data-testid="stMainBlockContainer"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #1a1a1a !important;
    }

    /* Excepciones */
    a, [data-testid="stMarkdownContainer"] a { color: #1155cc !important; }

    /* Botones de acción */
    .stButton > button {
        background-color: #6db38a !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
    }
    .stButton > button:hover {
        background-color: #3d7a5a !important;
    }

    /* Botones de descarga */
    .stDownloadButton > button {
        background-color: #f4faf7 !important;
        color: #3d7a5a !important;
        border: 1.5px solid #6db38a !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
    }
    .stDownloadButton > button:hover {
        background-color: #dff0ec !important;
    }

    /* Link buttons del sidebar */
    .stLinkButton > a {
        background-color: #dff0ec !important;
        color: #3d7a5a !important;
        border: 1.5px solid #b2d8c8 !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        text-decoration: none !important;
    }
    .stLinkButton > a:hover {
        background-color: #b2d8c8 !important;
        color: #2e4d31 !important;
    }
    h1, h2, h3,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: #2e4d31 !important;
    }

    /* Tabs */
    .stTabs [aria-selected="true"] {
        color: #2e4d31 !important;
        border-bottom-color: #2e4d31 !important;
    }

    /* Métricas */
    [data-testid="stMetric"] { background-color: #ffffff !important; }
    [data-testid="stMetricValue"] { color: #1a1a1a !important; }
    [data-testid="stMetricLabel"] { color: #555555 !important; }

    /* Expanders */
    [data-testid="stExpander"],
    [data-testid="stExpander"] * { background-color: #ffffff !important; }

    /* Alertas / Info boxes */
    [data-testid="stAlert"] {
        background-color: #eef4ff !important;
        color: #1a1a1a !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"],
    [data-testid="stFileUploaderDropzone"] {
        background-color: #f9f9f9 !important;
        padding-top: 0rem;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] { display: none; }
    [data-testid="stFileUploaderDropzone"]::before {
        content: "📂 Arrastra aquí tus archivos .csv o .txt";
        display: block;
        text-align: center;
        padding: 20px;
        color: #1f77b4 !important;
        font-weight: bold;
    }
    [data-testid="stFileUploaderDropzone"] button { display: none; }

    /* Tamaño de fuente base */
    .stApp p, .stApp li, .stApp label,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li {
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }

    </style>
    """, unsafe_allow_html=True)


# 3. Barra Lateral - Parte Superior
with st.sidebar:
    # Cargar el logo local (Asegúrate de que el archivo se llame LOGO.jpg en tu carpeta)
    st.image("LOGO.jpg", use_container_width=True)
    st.caption("<p style='text-align: center; color: gray; font-size: 0.8rem; margin-top: -5px'>Educación y Geografía Aplicada</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Subidor de archivos
    archivos = st.file_uploader("", type=['csv', 'txt'], accept_multiple_files=True)

     # 4. Sección de Apoyo (Esta puede estar fuera porque no depende de los datos)
    url_whatsapp = "https://wa.me/51986688805?text=Hola%20MapLecture,%20quiero%20apoyar%20el%20proyecto%20MapDrop"
    url_buymeacoffee = "https://buymeacoffee.com/maplecture"
    st.sidebar.subheader("☕ Apoya este proyecto")
    st.sidebar.write("Esta herramienta es gratuita. Si te sirvió, puedes apoyar su mantenimiento:")
    st.link_button("👉 Invítame un café (PayPal/Card)", url_buymeacoffee, use_container_width=True)
    st.link_button("👉 Donar por Yape/Plin (WhatsApp)", url_whatsapp, use_container_width=True)

    
# 5. Lógica de procesamiento
if archivos:
    # Header pequeño — solo visible cuando hay datos cargados
    st.markdown(
        "<div style='display:flex; align-items:center; gap:10px; margin-bottom:0.3rem;'>"
        "<span style='font-size:1.6rem;'>💧</span>"
        "<span style='font-size:1.4rem; font-weight:700; color:#3d7a5a; letter-spacing:1px;'>MapDrop</span>"
        "<span style='font-size:0.9rem; color:#888; margin-left:4px;'>| Procesamiento hidrometeorológico · MapLecture</span>"
        "</div>",
        unsafe_allow_html=True
    )
    st.markdown("<hr style='margin-top:0; margin-bottom:1rem; border-color:#dff0ec;'>", unsafe_allow_html=True)

    # Obtenemos la metadata del primer archivo de la lista
    metadata = ana.extraer_info_estacion(archivos[0], todos_los_archivos=archivos)

    # Bloque de estación — jerarquía visual unificada
    st.markdown(f"""
    <div style="background:#f4faf7; border-left:4px solid #6db38a; border-radius:8px; padding:14px 20px; margin-bottom:1rem;">
        <div style="font-size:0.75rem; color:#3d7a5a; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;">
            📍 Estación activa
        </div>
        <div style="font-size:1.5rem; font-weight:800; color:#1a1a1a; margin-bottom:8px;">
            {metadata['Estación']}
        </div>
        <div style="display:flex; gap:40px; font-size:0.9rem; color:#555;">
            <div><span style="font-weight:600; color:#2e4d31;">Departamento:</span>&nbsp; {metadata['Departamento']}</div>
            <div><span style="font-weight:600; color:#2e4d31;">Provincia / Distrito:</span>&nbsp; {metadata['Provincia']} / {metadata['Distrito']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- PROCESAMIENTO DE DATOS ---
    df_todo = ana.procesar_archivos(archivos)
    
    if df_todo is not None:
        # AQUÍ calculamos los años (ahora sí existen)
        anio_inicio = int(df_todo['año'].min())
        anio_fin = int(df_todo['año'].max())
        total_anios = anio_fin - anio_inicio + 1
        
        # --- SECCIÓN DE CRÉDITOS (Movida aquí adentro para que no dé error) ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ Desarrollo y Autoría")
        st.sidebar.write(f"""
        **Autora:** Brenda Quiroz   
        **Colaboración:** Desarrollado con el apoyo de IA (Gemini).
        """)

        st.sidebar.caption(f"Versión 1.0 | Datos de {anio_inicio} a {anio_fin}")

        # Generación de Matriz y Pestañas
        df_matriz = ana.generar_matriz_maximos(df_todo)

        tab1, tab2, tab3 = st.tabs(["🕵️ Validación de datos", "📅 Estadística de datos", "📈 Análisis Gráfico"])
        
        with tab1:
            st.subheader("🕵️ Valida los datos cargados")
            st.write("Si ves casillas en rojo significa que hay días del mes que no tienen registro, es importante que lo verifiques pues podría afectar la precisión del análisis .")

            # Llamamos a la nueva función
            df_validacion = ana.generar_resumen_validacion(df_todo)
            
            # Aplicamos un estilo visual: Rojo si faltan muchos días, Verde si está completo
            
            def destacar_faltantes(row):
                # Crear una lista de estilos vacíos del mismo largo que la fila
                styles = [''] * len(row)
                
                # El nombre de la fila suele ser el Año si es el índice
                try:
                    anio = int(row.name)
                except (ValueError, TypeError):
                    anio = 2024  # Año por defecto si hay error
                
                # Lista de meses para comparar (ajusta según tus columnas)
                meses_dict = {
                    'Ene': 1, 'Feb': 2, 'Marz': 3, 'Abr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12
                }

                for i, (col_nombre, valor) in enumerate(row.items()):
                    if col_nombre in meses_dict:
                        mes_num = meses_dict[col_nombre]
                        # Obtener días exactos del mes/año (considera bisiestos)
                        dias_reales = calendar.monthrange(anio, mes_num)[1]
                        
                        # Si faltan días (es mayor a 0 pero menor al total del mes)
                        if valor < dias_reales:
                            styles[i] = 'background-color: #ffcccc; color: #842029'
                            
                return styles

            st.dataframe(df_validacion.style.apply(destacar_faltantes, axis=1), use_container_width=True)
       
           # --- NUEVA SECCIÓN DE DESCARGA (Reemplaza la visualización de datos) ---
            st.subheader("📥 Exportar datos")
            st.write("Descarga la serie completa de datos diarios procesados en formato Excel.")
            
            # Preparar el archivo Excel en memoria
            buffer_datos = io.BytesIO()
            with pd.ExcelWriter(buffer_datos, engine='xlsxwriter') as writer:
                df_todo.to_excel(writer, index=False, sheet_name='Datos_Diarios')
            buffer_datos.seek(0)
            
            st.download_button(
                label="Excel de Datos Diarios",
                data=buffer_datos.getvalue(),
                file_name=f"Datos_Diarios_{metadata['Estación']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                icon="📊"
            )

        with tab2:
            st.subheader("📅 Precipitaciones Máximas Mensuales")
            with st.expander("ℹ️ ¿Para qué sirve esta información?"):
                st.markdown("""
                La **precipitación máxima en 24 horas** es el valor más alto registrado en un día dentro de cada mes.
                Según la *Guía de Prácticas Hidrológicas* de la OMM (Cap. 27 y 28), esta serie es la base del
                **análisis de frecuencias**, que permite estimar con qué probabilidad se repite un evento extremo
                y calcular su **período de retorno** (cada cuántos años se espera que ocurra).

                Sus principales aplicaciones son:
                * **Identificación de eventos extremos:** Detectar años con tormentas excepcionales vinculadas
                  a fenómenos como El Niño, usando los percentiles de la serie histórica como umbrales de referencia.
                * **Ingeniería y diseño hidráulico:** Es el insumo directo para calcular caudales de diseño en
                  cunetas, alcantarillas y defensas ribereñas mediante distribuciones probabilísticas (Gumbel, Log-Pearson III).
                * **Gestión del riesgo (EVAR):** Permite estimar la probabilidad de ocurrencia de inundaciones
                  o activaciones de quebradas para un período de retorno dado (10, 25, 50 o 100 años).
                """)
                st.markdown(
                    "**Fuente:** Organización Meteorológica Mundial. (2009). *Guía de prácticas hidrológicas* "
                    "(6.ª ed., OMM-N° 168, Cap. 27–28). OMM. "
                    "[📄 Descargar libro](https://www.academia.edu/28131870/GUIDE_YDROLOGICAL_PRACTICES_ADQUISICI%C3%93N_Y_PROCESO_DE_DATOS_AN%C3%81LISIS_PREDICCI%C3%93N_Y_OTRAS_APLICACIONES_GU%C3%8DA_DE_PR%C3%81CTICAS_HIDROL%C3%93GICAS_Bienvenido)"
                )

            # --- CÁLCULOS ESTADÍSTICOS HISTÓRICOS ---
            # 1. Precipitación Máxima Absoluta y su fecha
            max_val = df_todo['pp'].max()
            idx_max = df_todo['pp'].idxmax()
            
            col_fecha = next((c for c in df_todo.columns if c.lower() == 'fecha'), None)
            if col_fecha:
                fecha_obj = df_todo.loc[idx_max, col_fecha]
                try:
                    fecha_max_str = fecha_obj.strftime('%d/%m/%Y')
                except (AttributeError, ValueError):
                    fecha_max_str = str(fecha_obj)
            else:
                try:
                    d = df_todo.loc[idx_max]
                    fecha_max_str = f"{int(d['dia'])}/{int(d['mes'])}/{int(d['año'])}"
                except (KeyError, ValueError, TypeError):
                    fecha_max_str = "No disponible"

            lluvia_anual_total = df_todo.groupby('año')['pp'].sum()
            promedio_anual = lluvia_anual_total.mean()
            media_diaria = df_todo['pp'].mean()

            # --- TARJETAS DE MÉTRICAS CON TOOLTIP ---
            st.markdown("""
            <style>
            .mapdrop-metrics-row .metric-card {
                background: #f4faf7;
                border: 1px solid #c8e6d4;
                border-radius: 10px;
                padding: 18px 20px 14px 20px;
                position: relative;
                cursor: default;
                transition: box-shadow 0.2s;
                overflow: visible;
            }
            .mapdrop-metrics-row .metric-card:hover { box-shadow: 0 3px 12px rgba(61,122,90,0.15); }
            .mapdrop-metrics-row .metric-icon { font-size: 1.5rem; margin-bottom: 4px; }
            .mapdrop-metrics-row .metric-label {
                font-size: 0.78rem;
                color: #3d7a5a;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 2px;
            }
            .mapdrop-metrics-row .metric-value {
                font-size: 1.9rem;
                font-weight: 800;
                color: #1a1a1a;
                line-height: 1.1;
            }
            .mapdrop-metrics-row .metric-sub {
                font-size: 0.78rem;
                color: #888;
                margin-top: 4px;
            }
            .mapdrop-metrics-row .metric-tooltip {
                visibility: hidden;
                opacity: 0;
                background: #2e4d31;
                color: #fff;
                font-size: 0.8rem;
                line-height: 1.5;
                border-radius: 8px;
                padding: 10px 13px;
                position: absolute;
                z-index: 9999;
                bottom: 110%;
                left: 50%;
                transform: translateX(-50%);
                width: 240px;
                box-shadow: 0 4px 14px rgba(0,0,0,0.2);
                transition: opacity 0.2s;
                pointer-events: none;
            }
            .mapdrop-metrics-row .metric-card:hover .metric-tooltip {
                visibility: visible;
                opacity: 1;
            }
            </style>
            <div class="mapdrop-metrics-row"></div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="mapdrop-metrics-row" style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:1rem;">
                <div class="metric-card">
                    <div class="metric-tooltip">El valor de precipitación más alto registrado en un solo día (24 h) en toda la historia de la estación. Representa el evento extremo más severo detectado.</div>
                    <div class="metric-icon">🌧️</div>
                    <div class="metric-label">Máxima Histórica</div>
                    <div class="metric-value">{max_val} mm</div>
                    <div class="metric-sub">📅 Fecha: {fecha_max_str}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-tooltip">Promedio de la lluvia total acumulada por año. Indica cuánta precipitación se espera en la estación durante un año completo normal.</div>
                    <div class="metric-icon">📊</div>
                    <div class="metric-label">Precipitación Media Anual</div>
                    <div class="metric-value">{promedio_anual:.1f} mm</div>
                    <div class="metric-sub">Total acumulado promedio por año</div>
                </div>
                <div class="metric-card">
                    <div class="metric-tooltip">Promedio de todos los registros diarios, incluyendo días sin lluvia (0 mm). Refleja la intensidad diaria habitual de la estación.</div>
                    <div class="metric-icon">🗓️</div>
                    <div class="metric-label">Precipitación Media Diaria</div>
                    <div class="metric-value">{media_diaria:.2f} mm</div>
                    <div class="metric-sub">Promedio de todos los días de la serie</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)

            # --- MATRIZ Y DESCARGA ---
            st.divider()
            st.write("Haz clic en el botón de abajo para obtener la matriz completa en formato Excel.")
            
            # Preparamos el Excel de la Matriz
            tobol = io.BytesIO()
            with pd.ExcelWriter(tobol, engine='xlsxwriter') as writer:
                df_matriz.to_excel(writer, index=True, sheet_name='Matriz_PP_Max')
            tobol.seek(0)
            
            st.download_button(
                label="📗 Descargar tabla de Precipitaciones Máximas (.xlsx)",
                data=tobol.getvalue(),
                file_name=f"Matriz_PP_Max_{metadata['Estación']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True # Botón grande y profesional
            )


            
        with tab3:
            # --- CÁLCULOS ---
            f1_dinamico, umbral_medio, umbral_alto = ana.grafico_pp_max_anual(df_todo)
            f2_boxplot, mes_habitual = ana.grafico_boxplot(df_todo)
            f3_hist, intensidad_media = ana.grafico_histograma(df_todo)
            max_historico = df_todo['pp'].max()
            anio_max = df_todo.loc[df_todo['pp'].idxmax(), 'año']
            veces_promedio = max_historico / umbral_medio if umbral_medio > 0 else 0
            eventos_criticos = len(df_todo[df_todo['pp'] > umbral_alto])

            # --- EXPANDER UNIFICADO: CONTEXTO + METODOLOGÍA ---
            with st.expander("📖 ¿Qué son los umbrales de precipitación y cómo los calcula MapDrop?"):
                st.markdown(
                    "En el análisis de frecuencias hidrológicas (OMM, 2009, Cap. 27), un **umbral de precipitación** "
                    "es un valor de referencia estadístico que permite clasificar los registros históricos según su "
                    "magnitud y frecuencia de ocurrencia.\n\n"
                    "MapDrop calcula dos umbrales a partir de la serie histórica cargada:\n\n"
                    "* **Percentil 50 (Mediana):** Significa que el 50% de los años registró una precipitación máxima "
                    "anual igual o inferior a este valor. Representa el comportamiento habitual de la estación.\n"
                    "* **Percentil 90:** Significa que solo el 10% de los años superó este valor. Corresponde a un "
                    "evento de baja frecuencia de ocurrencia y alta magnitud (OMM, 2009, Cap. 28).\n\n"
                    "Estos umbrales permiten identificar visualmente qué años presentaron precipitaciones máximas "
                    "dentro del rango habitual y cuáles se alejaron significativamente de ese comportamiento.\n\n"
                    "**Consideraciones metodológicas:**\n"
                    "* Con series menores a 15 años, los percentiles son estadísticamente inestables.\n"
                    "* Este método no reemplaza el análisis de frecuencias con distribuciones probabilísticas "
                    "(Gumbel, Log-Pearson III, GEV) para estimar períodos de retorno formales.\n"
                    "* No incorpora información fisiográfica que pueda condicionar la respuesta hidrológica real.\n\n"
                    "**Referencia:** Organización Meteorológica Mundial. (2009). *Guía de prácticas hidrológicas* "
                    "(6.ª ed., OMM-N° 168, Cap. 27–28). OMM. "
                    "[📄 Descargar libro](https://www.academia.edu/28131870/GUIDE_YDROLOGICAL_PRACTICES_ADQUISICI%C3%93N_Y_PROCESO_DE_DATOS_AN%C3%81LISIS_PREDICCI%C3%93N_Y_OTRAS_APLICACIONES_GU%C3%8DA_DE_PR%C3%81CTICAS_HIDROL%C3%93GICAS_Bienvenido)"
                )

            # --- AVISO DE LIMITACIONES ---
            st.warning(
                "⚠️ **Limitaciones del análisis**\n\n"
                "Los umbrales se calculan a partir de la propia serie cargada. **Series con menos de 15–20 años "
                "de registro pueden producir umbrales estadísticamente inestables**, subestimando o sobreestimando "
                "el comportamiento real de la zona.\n\n"
                "Los resultados son de **carácter exploratorio**. Su interpretación y aplicación en decisiones "
                "técnicas requiere la revisión de un profesional especializado en hidrología o ingeniería hidráulica."
            )

            # --- GRÁFICO 1: MÁXIMAS ANUALES ---
            st.markdown(f"### Precipitaciones Máximas Anuales — {anio_inicio} al {anio_fin}")
            st.caption(
                f"Percentil 50: **{umbral_medio:.1f} mm** · "
                f"Percentil 90 (línea roja): **{umbral_alto:.1f} mm** · "
                f"Máximo histórico: **{max_historico:.1f} mm** ({int(anio_max)}) · "
                f"Eventos sobre Percentil 90: **{eventos_criticos}**"
            )
            st.plotly_chart(f1_dinamico, use_container_width=True)
            with st.expander("🔍 ¿Cómo interpretar este gráfico?"):
                st.markdown(
                    "Este gráfico muestra la **precipitación máxima registrada en 24 horas por año**. "
                    "Cada punto representa el valor más alto de un día dentro de ese año.\n\n"
                    "**¿Qué significan los colores?**\n"
                    "* 🟢 **Verde:** El año estuvo dentro del comportamiento habitual (por debajo del Percentil 50).\n"
                    "* 🟡 **Amarillo:** El año superó la mediana pero no alcanzó el Percentil 90. Precipitación por encima de lo habitual.\n"
                    "* 🔴 **Rojo:** El año superó el Percentil 90. Evento de baja frecuencia de ocurrencia y alta magnitud.\n\n"
                    "**¿Qué es la línea roja punteada?**\n"
                    "Representa el **Percentil 90** de la serie. Los años con punto rojo por encima de esa línea "
                    "son los eventos de mayor magnitud registrados en la estación.\n\n"
                    "**¿Qué observar?** Identifica si los eventos de alta magnitud se concentran en algún período "
                    "o si se distribuyen a lo largo de toda la serie. Esto puede indicar variabilidad climática interanual."
                )

            st.divider()

            # --- GRÁFICO 2: BOXPLOT MENSUAL ---
            st.markdown(f"### Variabilidad Mensual de Precipitaciones — {anio_inicio} al {anio_fin}")
            st.caption(
                f"Mes con mayor magnitud de precipitación: **{mes_habitual}** · "
                "Los puntos aislados sobre las cajas representan registros diarios que superan el rango intercuartílico del mes."
            )
            st.plotly_chart(f2_boxplot, use_container_width=True)
            with st.expander("🔍 ¿Cómo interpretar este gráfico?"):
                st.markdown(
                    "Este gráfico muestra la **distribución de las precipitaciones diarias por mes** a lo largo "
                    "de toda la serie histórica. Permite identificar qué meses concentran las lluvias de mayor magnitud.\n\n"
                    "**¿Qué representa cada caja?**\n"
                    "* La **línea central** de la caja es la mediana del mes: el 50% de los días registró "
                    "precipitaciones por debajo de ese valor.\n"
                    "* Los **bordes de la caja** representan el rango intercuartílico (Percentil 25 al 75): "
                    "donde se concentra el 50% central de los datos del mes.\n"
                    "* Las **líneas que se extienden** (bigotes) muestran el rango general sin considerar valores atípicos.\n"
                    "* Los **puntos aislados** fuera de la caja son registros diarios que superaron el rango "
                    "esperado para ese mes — eventos de alta magnitud dentro del mes.\n\n"
                    "**¿Qué observar?** Los meses con cajas más altas y puntos aislados frecuentes son los de "
                    "mayor variabilidad. Estos corresponden al período de mayor actividad pluviométrica de la estación."
                )

            st.divider()

            # --- GRÁFICO 3: HISTOGRAMA ---
            st.markdown(f"### Distribución de Frecuencias de Precipitación Diaria — {anio_inicio} al {anio_fin}")
            st.caption(
                f"Precipitación media en días con registro > 0.1 mm: **{intensidad_media:.1f} mm/día** · "
                "Los valores hacia la derecha corresponden a eventos de baja frecuencia y alta magnitud."
            )
            st.plotly_chart(f3_hist, use_container_width=True)
            with st.expander("🔍 ¿Cómo interpretar este gráfico?"):
                st.markdown(
                    "Este gráfico muestra **con qué frecuencia se repiten distintos rangos de precipitación diaria** "
                    "en la serie histórica. Solo incluye días con precipitación mayor a 0.1 mm.\n\n"
                    "**¿Cómo leerlo?**\n"
                    "* El **eje horizontal** representa la cantidad de precipitación en mm/día.\n"
                    "* El **eje vertical** indica cuántos días de la serie registraron ese rango de precipitación.\n"
                    "* Las barras más altas hacia la izquierda indican que la estación registra frecuentemente "
                    "precipitaciones de baja magnitud.\n"
                    "* Las barras hacia la derecha — aunque bajas — representan eventos de alta magnitud y "
                    "baja frecuencia de ocurrencia.\n\n"
                    "**¿Qué observar?** Si la distribución se extiende con barras hacia la derecha, "
                    "la estación tiene historial de eventos de precipitación de alta magnitud. "
                    "Estos valores extremos son los que alimentan el análisis de frecuencias "
                    "para el cálculo de caudales de diseño (OMM, 2009, Cap. 28)."
                )
                
    else:
        st.error("No se pudieron procesar los archivos.")
else:
    # 1. Título con diseño limpio
    st.markdown("<h1 style='text-align: center; margin-top: -2rem;'>💧 MapDrop</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray; font-size: 1.2rem;'>Procesamiento inteligente de datos hidrometeorológicos</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 2. Columnas para explicar "Qué hace" y "Cómo usarla"
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 style='color:#2e4d31; font-size:1.4rem;'>¿Qué hace MapDrop?</h3>", unsafe_allow_html=True)
        st.markdown("Es una herramienta diseñada por **MapLecture** para automatizar la gestión de datos del SENAMHI:")
        st.markdown("* **Estandarización:** Convierte archivos TXT y CSV convencionales a un formato limpio.")
        st.markdown("* **Cálculo Automático:** Genera matrices de precipitaciones máximas mensuales y diarias al instante.")
        st.markdown("* **Auditoría:** Evalúa la calidad de tu serie de datos mediante semáforos de completitud.")

    with col2:
        st.markdown("<h3 style='color:#2e4d31; font-size:1.4rem;'>¿Cómo usarla?</h3>", unsafe_allow_html=True)
        st.markdown("1. **Prepara tus archivos:** Ten a la mano tus descargas del **SENAMHI**. Puedes obtener datos desde:")
        st.markdown("   * [Web de Datos Hidrometeorológicos (Convencionales)](https://www.senamhi.gob.pe/site/descarga-datos/)")
        st.markdown("   * [Buscador de Estaciones (Histórico)](https://www.senamhi.gob.pe/?p=estaciones)")
        st.markdown("2. **Carga los datos:** Usa el panel lateral izquierdo para arrastrar uno o varios archivos.")
        st.markdown("3. **Analiza:** Navega por las pestañas para ver la matriz, los gráficos y la validación.")
        st.markdown("4. **Descarga:** Exporta tus resultados directamente a Excel o CSV.")

    st.markdown("---")
    st.info("👈 **Comienza ahora:** Sube tus archivos en la barra lateral para activar el análisis.")