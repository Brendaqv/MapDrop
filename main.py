import streamlit as st
import analisis_ppmaximas as ana
import analisis_temperatura as temp
import pandas as pd
import numpy as np
import senamhi_stations as sna
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
        content: "📂 Arrastra aquí tus archivos .csv, .txt o .xlsx";
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
    st.image("LOGO.jpg", use_container_width=True)
    st.caption("<p style='text-align: center; color: gray; font-size: 0.8rem; margin-top: -5px'>Territorio, datos y conocimiento</p>", unsafe_allow_html=True)
    st.markdown("---")

    # ── SISTEMA DINÁMICO MULTI-ESTACIÓN ──
    # Cada "slot" es un uploader independiente con su propia key.
    # El usuario puede agregar tantos slots como estaciones quiera comparar.
    import io as _io

    if 'n_slots' not in st.session_state:
        st.session_state.n_slots = 1
    if 'archivos_acumulados' not in st.session_state:
        st.session_state.archivos_acumulados = {}

    # Renderizar un uploader por slot
    for slot_i in range(st.session_state.n_slots):
        # Label dinámico: muestra nombre de estación si ya hay archivos en este slot
        archivos_slot = [v for v in st.session_state.archivos_acumulados.values()
                         if isinstance(v, dict) and v.get('slot') == slot_i]
        if archivos_slot and st.session_state.n_slots > 1:
            try:
                primer = archivos_slot[0]
                buf_label = _io.BytesIO(primer['data'])
                buf_label.name = primer['name']
                meta_label = ana.extraer_info_estacion(buf_label)
                nombre_label = meta_label.get('Estación', '')
                label = f"📂 {nombre_label}" if nombre_label and nombre_label != 'NO ENCONTRADA' else f"📂 Estación {slot_i + 1}"
            except Exception:
                label = f"📂 Estación {slot_i + 1}"
        elif st.session_state.n_slots > 1:
            label = f"📂 Estación {slot_i + 1}"
        else:
            label = ""

        nuevos_slot = st.file_uploader(
            label,
            type=['csv', 'txt', 'xlsx'],
            accept_multiple_files=True,
            key=f"uploader_slot_{slot_i}",
        )
        if nuevos_slot:
            for a in nuevos_slot:
                a.seek(0)
                # Clave slot_N/nombre — evita colisión entre estaciones con mismo nombre de archivo
                clave = f"slot_{slot_i}/{a.name}"
                st.session_state.archivos_acumulados[clave] = {
                    'data': a.read(),
                    'name': a.name,
                    'slot': slot_i,
                }
                a.seek(0)

    # Botones: agregar slot y limpiar todo
    col_add, col_clear = st.columns([1, 1])
    with col_add:
        if st.button("➕ Agregar estación", use_container_width=True):
            st.session_state.n_slots += 1
            st.rerun()
    with col_clear:
        if st.button("🗑️ Limpiar todo", use_container_width=True):
            st.session_state.archivos_acumulados = {}
            st.session_state.n_slots = 1
            st.rerun()

    # Resumen de archivos acumulados
    n_acum = len(st.session_state.archivos_acumulados)
    if n_acum > 0:
        st.caption(f"📂 {n_acum} archivo(s) acumulado(s) en total")

    # Reconstruir lista de archivos desde session_state
    archivos = []
    for clave, info in st.session_state.archivos_acumulados.items():
        if isinstance(info, dict):
            buf = _io.BytesIO(info['data'])
            buf.name = info['name']
        else:
            # Compatibilidad con formato antiguo
            buf = _io.BytesIO(info)
            buf.name = clave
        archivos.append(buf)

    # ── BUSCADOR DE ESTACIONES SENAMHI ──
    st.markdown("---")
    st.sidebar.subheader("🔍 Buscar Estación SENAMHI")
    _query = st.text_input("", placeholder="Nombre o código (ej: HUACHOS, 113067)", key="buscador_estacion")
    if _query and len(_query) >= 2:
        _estaciones = sna.cargar_estaciones()
        _results = sna.buscar_estaciones(_query, _estaciones)
        if _results:
            for _e in _results:
                _info = sna.get_info_estacion(_e)
                with st.expander(f"📍 {_info['nombre']} — {_info['categoria']}", expanded=False):
                    st.markdown(
                        f"**Código:** {_info['codigo']}  \n"
                        f"**Tipo:** {_info['tipo']} · {_info['estado']}  \n"
                        f"**Variables:** {_info['variables']}  \n"
                        f"**Coordenadas:** {_info['lat']:.4f}, {_info['lon']:.4f}"
                    )
                    st.link_button("🌐 Abrir en SENAMHI", _info['url'], use_container_width=True)
                    if _info['es_ema']:
                        st.caption("📡 Estación automática — genera datos horarios compatibles con MapDrop")
        else:
            st.caption("Sin resultados. Intenta con otro nombre o código.")

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

    metadata = ana.extraer_info_estacion(archivos[0], todos_los_archivos=archivos)

    # ── Detectar cuántas estaciones hay para mostrar el panel correcto ──
    # Agrupar archivos por nombre de estación (lectura rápida de cabecera)
    # Construir mapa slot→nombre para TXT (usa nombre del CSV del mismo slot)
    _slot_nombre = {}
    _slot_meta = {}
    for _clave, _info in st.session_state.archivos_acumulados.items():
        if not isinstance(_info, dict): continue
        _slot_i = _info.get('slot', 0)
        _nombre_arch = _info.get('name', '')
        if not _nombre_arch.lower().endswith('.txt'):
            try:
                _buf_tmp = _io.BytesIO(_info['data'])
                _buf_tmp.name = _nombre_arch
                _meta_tmp = ana.extraer_info_estacion(_buf_tmp)
                _nom_tmp = _meta_tmp.get('Estación', '')
                if _nom_tmp and _nom_tmp != 'NO ENCONTRADA':
                    _slot_nombre[_slot_i] = _nom_tmp
                    _slot_meta[_slot_i] = _meta_tmp
            except Exception:
                pass

    _grupos_preview = {}
    for _a in archivos:
        try:
            _a.seek(0)
            _tipo_a = ana.detectar_tipo_archivo(_a)['tipo']
            _a.seek(0)
            if _tipo_a == 'txt':
                # Buscar slot del archivo para heredar nombre de su estación
                _slot_del_txt = None
                for _clave, _info in st.session_state.archivos_acumulados.items():
                    if isinstance(_info, dict) and _info.get('name') == _a.name:
                        _slot_del_txt = _info.get('slot', 0)
                        break
                if _slot_del_txt is not None and _slot_del_txt in _slot_nombre:
                    _nom = _slot_nombre[_slot_del_txt]
                    _meta = _slot_meta[_slot_del_txt]
                else:
                    _nom = _a.name.rsplit('.', 1)[0].upper()
                    _meta = {'Departamento': '—', 'Provincia': '—', 'Distrito': '—'}
            else:
                _meta = ana.extraer_info_estacion(_a, todos_los_archivos=archivos)
                _nom = _meta.get('Estación', 'DESCONOCIDA')
            _a.seek(0)
            if _nom not in _grupos_preview:
                _grupos_preview[_nom] = {'meta': _meta, 'n': 0, 'tipo': _tipo_a}
            _grupos_preview[_nom]['n'] += 1
        except Exception:
            try: _a.seek(0)
            except Exception: pass

    _tipo_label = {'txt': 'TXT Convencional', 'csv_convencional': 'CSV Convencional',
                   'csv_ema': 'EMA (Automática)', 'xlsx': 'XLSX (MapDrop)'}

    if len(_grupos_preview) <= 1:
        # ── Panel de estación única ──
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
    else:
        # ── Panel multi-estación: tarjetas ──
        st.markdown(f"""
        <div style="font-size:0.75rem; color:#3d7a5a; font-weight:700; text-transform:uppercase;
                    letter-spacing:1px; margin-bottom:8px;">
            📍 {len(_grupos_preview)} estaciones cargadas
        </div>""", unsafe_allow_html=True)

        cols = st.columns(len(_grupos_preview))
        for col, (nom, info) in zip(cols, _grupos_preview.items()):
            meta = info['meta']
            tipo = _tipo_label.get(info['tipo'], info['tipo'])
            n_arch = info['n']
            with col:
                st.markdown(f"""
                <div style="background:#f4faf7; border-left:4px solid #6db38a; border-radius:8px;
                            padding:12px 16px; margin-bottom:1rem; height:100%;">
                    <div style="font-size:1rem; font-weight:800; color:#1a1a1a; margin-bottom:6px;">
                        {nom}
                    </div>
                    <div style="font-size:0.78rem; color:#3d7a5a; font-weight:600; margin-bottom:4px;">
                        {tipo}
                    </div>
                    <div style="font-size:0.78rem; color:#555; margin-bottom:2px;">
                        📁 {n_arch} archivo(s)
                    </div>
                    <div style="font-size:0.78rem; color:#555;">
                        {meta.get('Departamento','—')} · {meta.get('Provincia','—')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- BANNER DE FUENTES (expander colapsado) ---
    if len(archivos) > 1:
        fuentes_resumen, combinado = ana.obtener_resumen_fuentes(archivos)
        if fuentes_resumen:
            with st.expander(
                f"🗂️ Ver fuentes cargadas — {combinado['n_fuentes']} archivos · "
                f"Serie {combinado['año_min']}–{combinado['año_max']}",
                expanded=False
            ):
                filas = ""
                for f in fuentes_resumen:
                    periodo = f"{f['año_min']} — {f['año_max']}" if f['año_min'] > 0 else "—"
                    filas += f"""
                    <tr>
                        <td style="padding:6px 12px;font-size:0.82rem;color:#1a1a1a;border-bottom:1px solid #e0e0e0;">{f['nombre']}</td>
                        <td style="padding:6px 12px;font-size:0.82rem;color:#3d7a5a;font-weight:600;border-bottom:1px solid #e0e0e0;">{f['tipo']}</td>
                        <td style="padding:6px 12px;font-size:0.82rem;color:#1a1a1a;border-bottom:1px solid #e0e0e0;">{periodo}</td>
                        <td style="padding:6px 12px;font-size:0.82rem;color:#e67e22;border-bottom:1px solid #e0e0e0;">{f['prioridad']}</td>
                    </tr>"""
                st.markdown(f"""
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="background:#dff0ec;">
                            <th style="padding:6px 12px;font-size:0.75rem;color:#2e4d31;text-align:left;font-weight:700;">Archivo</th>
                            <th style="padding:6px 12px;font-size:0.75rem;color:#2e4d31;text-align:left;font-weight:700;">Tipo</th>
                            <th style="padding:6px 12px;font-size:0.75rem;color:#2e4d31;text-align:left;font-weight:700;">Período</th>
                            <th style="padding:6px 12px;font-size:0.75rem;color:#2e4d31;text-align:left;font-weight:700;">Prioridad</th>
                        </tr>
                    </thead>
                    <tbody>{filas}
                        <tr style="background:#2e4d31;">
                            <td colspan="2" style="padding:7px 12px;font-size:0.82rem;color:#fff;font-weight:700;">📊 Serie combinada resultante</td>
                            <td style="padding:7px 12px;font-size:0.82rem;color:#6db38a;font-weight:700;">{combinado['año_min']} — {combinado['año_max']}</td>
                            <td style="padding:7px 12px;font-size:0.82rem;color:#6db38a;font-weight:700;">{combinado['n_fuentes']} fuentes</td>
                        </tr>
                    </tbody>
                </table>
                <div style="font-size:0.72rem;color:#888;margin-top:8px;">
                    ★★★★ mayor confiabilidad · Cuando un día existe en varias fuentes, se conserva el de mayor prioridad.
                </div>""", unsafe_allow_html=True)

    # --- DETECCIÓN DE TIPO DE ARCHIVO ---
    archivos_ema = [a for a in archivos if ana.detectar_tipo_archivo(a)['tipo'] == 'csv_ema']
    es_ema = len(archivos_ema) > 0

    # Detectar archivos de temperatura
    for a in archivos:
        try: a.seek(0)
        except Exception: pass
    archivos_temp = [a for a in archivos if temp.es_archivo_temperatura(a)]
    es_temperatura = len(archivos_temp) > 0

    modo_analisis = 'diario'
    if es_ema:
        st.info(
            f"📡 **Se detectaron {len(archivos_ema)} archivo(s) de estación automática (EMA)** — registros por hora (mm/h).\n\n"
            "¿Cómo deseas realizar el análisis?"
        )
        col1, col2 = st.columns(2)
        with col1:
            btn_diario = st.button("📅 Agregar a diario y analizar", use_container_width=True)
        with col2:
            btn_horario = st.button("⏱️ Análisis diario + horario", use_container_width=True)

        if "modo_ema" not in st.session_state:
            st.session_state.modo_ema = None
        if btn_diario:
            st.session_state.modo_ema = 'diario'
        if btn_horario:
            st.session_state.modo_ema = 'horario'

        modo_analisis = st.session_state.get('modo_ema', None)
        if modo_analisis is None:
            st.stop()

    # --- PROCESAMIENTO DE DATOS ---
    # Detectar si hay múltiples estaciones ANTES de procesar
    # para evitar mezclar datos de estaciones distintas en df_todo
    _grupos_slots = {}
    for _a in archivos:
        try:
            _a.seek(0)
            _t = ana.detectar_tipo_archivo(_a)['tipo']
            _a.seek(0)
            # Obtener slot del archivo desde session_state
            _slot = 0
            for _c, _i in st.session_state.get('archivos_acumulados', {}).items():
                if isinstance(_i, dict) and _i.get('name') == _a.name:
                    _slot = _i.get('slot', 0)
                    break
            if _slot not in _grupos_slots:
                _grupos_slots[_slot] = []
            _grupos_slots[_slot].append(_a)
            _a.seek(0)
        except Exception:
            try: _a.seek(0)
            except Exception: pass

    # Si hay más de un slot → procesar solo el slot 0 como "estación activa"
    # El resumen comparativo usa grupos_estaciones para las demás
    if len(_grupos_slots) > 1:
        _archivos_activos = _grupos_slots.get(0, archivos)
        for _a in _archivos_activos: _a.seek(0)
        df_todo = ana.procesar_archivos(_archivos_activos, modo='diario')
    else:
        df_todo = ana.procesar_archivos(archivos, modo='diario')

    # Para modo horario, también calcular serie horaria completa
    if es_ema and modo_analisis == 'horario':
        for a in archivos_ema:
            a.seek(0)
        df_horario_ema = ana.procesar_csv_ema_horario(archivos_ema)
    else:
        df_horario_ema = None

    df_diario = df_todo

    if df_todo is not None:
        anio_inicio = int(df_todo['año'].min())
        anio_fin = int(df_todo['año'].max())
        total_anios = anio_fin - anio_inicio + 1

        # --- SECCIÓN DE CRÉDITOS ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ Desarrollo y Autoría")
        st.sidebar.write("""
        **Autora:** Brenda Quiroz   
        **Colaboración:** Desarrollado con el apoyo de IA (Claude).
        """)
        st.sidebar.caption("Versión 2.0 | 2026")

        # Generación de Matriz y Pestañas
        df_matriz = ana.generar_matriz_maximos(df_todo)

        # --- NUEVO DISEÑO DE PESTAÑAS ---
        # Tab 1: Validación
        # Tab 2: Indicadores PP Diaria (métricas + gráficos)
        # Tab 3: Indicadores PP Horaria (solo si hay EMA en modo horario)
        # Tab 4: Temperatura y Clima (solo si hay archivos de temperatura)

        # ── Detección y agrupación de múltiples estaciones ──
        # Lee la cabecera de cada CSV para identificar a qué estación pertenece.
        # TXT sin cabecera usan el nombre del archivo como identificador.
        # Paso 1: construir mapa slot→nombre desde los CSVs (que sí tienen metadatos)
        _slot_nombre_map = {}
        _slot_meta_map = {}
        for _clave, _info in st.session_state.archivos_acumulados.items():
            if not isinstance(_info, dict): continue
            _slot_i = _info.get('slot', 0)
            _nombre_arch = _info.get('name', '')
            if not _nombre_arch.lower().endswith('.txt'):
                try:
                    _buf_tmp = _io.BytesIO(_info['data'])
                    _buf_tmp.name = _nombre_arch
                    _meta_tmp = ana.extraer_info_estacion(_buf_tmp)
                    _nom_tmp = _meta_tmp.get('Estación', '')
                    if _nom_tmp and _nom_tmp != 'NO ENCONTRADA':
                        _slot_nombre_map[_slot_i] = _nom_tmp
                        _slot_meta_map[_slot_i] = _meta_tmp
                except Exception:
                    pass

        # Paso 2: agrupar archivos por estación
        grupos_raw = {}  # nombre_estacion → lista de archivos
        for a in archivos:
            try:
                a.seek(0)
                tipo_a = ana.detectar_tipo_archivo(a)['tipo']
                a.seek(0)
                if tipo_a == 'txt':
                    # TXT hereda nombre del CSV del mismo slot
                    _slot_del_txt = None
                    for _clave, _info in st.session_state.archivos_acumulados.items():
                        if isinstance(_info, dict) and _info.get('name') == a.name:
                            _slot_del_txt = _info.get('slot', 0)
                            break
                    if _slot_del_txt is not None and _slot_del_txt in _slot_nombre_map:
                        nombre_a = _slot_nombre_map[_slot_del_txt]
                        meta_a = _slot_meta_map[_slot_del_txt]
                    else:
                        nombre_a = a.name.rsplit('.', 1)[0].upper()
                        meta_a = {'Código': '', 'Departamento': 'N/A', 'Provincia': 'N/A', 'Distrito': 'N/A'}
                elif tipo_a == 'csv_ema':
                    meta_a = ana.extraer_info_estacion(a, todos_los_archivos=archivos)
                    nombre_a = meta_a.get('Estación', a.name.rsplit('.', 1)[0].upper())
                    a.seek(0)
                else:
                    meta_a = ana.extraer_info_estacion(a, todos_los_archivos=archivos)
                    nombre_a = meta_a.get('Estación', 'DESCONOCIDA')
                    a.seek(0)

                if nombre_a not in grupos_raw:
                    grupos_raw[nombre_a] = {'archivos': [], 'meta': meta_a}
                grupos_raw[nombre_a]['archivos'].append(a)
                a.seek(0)
            except Exception:
                try: a.seek(0)
                except Exception: pass

        # Procesar cada grupo de estación
        grupos_estaciones = {}
        for nombre_e, grupo in grupos_raw.items():
            try:
                for a in grupo['archivos']: a.seek(0)
                df_e = ana.procesar_archivos(grupo['archivos'], modo='diario')
                if df_e is not None and not df_e.empty:
                    grupos_estaciones[nombre_e] = {
                        'nombre': nombre_e,
                        'codigo': grupo['meta'].get('Código', ''),
                        'lat': grupo['meta'].get('Latitud', None),
                        'lon': grupo['meta'].get('Longitud', None),
                        'df': df_e,
                    }
                for a in grupo['archivos']: a.seek(0)
            except Exception:
                pass

        es_multi = len(grupos_estaciones) > 1

        # ── RESUMEN COMPARATIVO debajo de tarjetas (antes de pestañas) ──
        if es_multi:
            st.markdown("---")
            st.markdown("### 📊 Resumen de Estaciones")
            _lista_grupos = list(grupos_estaciones.values())
            _df_multi = ana.analizar_multiples_estaciones(_lista_grupos)
            if _df_multi is not None and not _df_multi.empty:
                st.dataframe(_df_multi.set_index('Estación'), use_container_width=True)
                st.info(
                    "💡 Con las columnas **Latitud** y **Longitud** puedes llevar estos valores a QGIS "
                    "para generar mapas de isolíneas de precipitación por región — "
                    "funcionalidad que pronto integraremos."
                )
                _buf_multi = io.BytesIO()
                with pd.ExcelWriter(_buf_multi, engine='xlsxwriter') as _writer:
                    _df_multi.to_excel(_writer, index=False, sheet_name='Comparacion_Estaciones')
                _buf_multi.seek(0)
                st.download_button(
                    label="📥 Descargar tabla comparativa (.xlsx)",
                    data=_buf_multi.getvalue(),
                    file_name="MapDrop_Comparacion_Estaciones.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            st.markdown("---")

        # Comparar Estaciones aparece debajo de las tarjetas, no como pestaña
        tab_labels = ["🕵️ Validación de datos", "📊 Indicadores PP Diaria"]
        if es_ema and modo_analisis == 'horario':
            tab_labels.append("⏱️ Indicadores PP Horaria")
        if es_temperatura:
            tab_labels.append("🌡️ Temperatura y Clima")

        tabs = st.tabs(tab_labels)
        tab1 = tabs[0]
        tab2 = tabs[1]
        tab3 = tabs[2] if (es_ema and modo_analisis == 'horario') else None
        # tab_temp: índice explícito para evitar conflicto con otros tabs
        if es_temperatura:
            idx_temp = 2 + (1 if (es_ema and modo_analisis == 'horario') else 0)
            tab_temp = tabs[idx_temp] if idx_temp < len(tabs) else None
        else:
            tab_temp = None

        # ═══════════════════════════════════════════════════
        # TAB 1 — VALIDACIÓN DE DATOS
        # ═══════════════════════════════════════════════════
        with tab1:
            st.subheader("🕵️ Valida los datos cargados")
            st.write("Si ves casillas en rojo significa que hay días del mes que no tienen registro, es importante que lo verifiques pues podría afectar la precisión del análisis.")

            df_validacion = ana.generar_resumen_validacion(df_todo)

            # Nombres de meses sincronizados con MESES_NOMBRES del módulo
            meses_dict = {
                'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Ago': 8, 'Set': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12
            }

            def destacar_faltantes(row):
                styles = [''] * len(row)
                try:
                    anio = int(row.name)
                except (ValueError, TypeError):
                    anio = 2024
                for i, (col_nombre, valor) in enumerate(row.items()):
                    if col_nombre in meses_dict:
                        mes_num = meses_dict[col_nombre]
                        dias_reales = calendar.monthrange(anio, mes_num)[1]
                        if valor < dias_reales:
                            styles[i] = 'background-color: #ffcccc; color: #842029'
                return styles

            st.dataframe(df_validacion.style.apply(destacar_faltantes, axis=1), use_container_width=True)

            st.subheader("📥 Exportar datos")
            st.write("Descarga la serie completa de datos diarios procesados en formato Excel.")

            buffer_datos = io.BytesIO()
            with pd.ExcelWriter(buffer_datos, engine='xlsxwriter') as writer:
                sheet = 'Datos_Horarios' if es_ema and modo_analisis == 'horario' else 'Datos_Diarios'
                df_todo.to_excel(writer, index=False, sheet_name=sheet)
            buffer_datos.seek(0)

            # Ícono y nombre dinámicos según tipo de datos
            es_horario_ema = es_ema and modo_analisis == 'horario'
            label_descarga = "⏱️ Excel de Datos Horarios" if es_horario_ema else "📊 Excel de Datos Diarios"
            filename_descarga = f"{'Datos_Horarios' if es_horario_ema else 'Datos_Diarios'}_{metadata['Estación']}.xlsx"

            st.download_button(
                label=label_descarga,
                data=buffer_datos.getvalue(),
                file_name=filename_descarga,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        # ═══════════════════════════════════════════════════
        # TAB 2 — INDICADORES PP DIARIA (métricas + gráficos)
        # ═══════════════════════════════════════════════════
        with tab2:
            st.subheader("📊 Precipitaciones Máximas Mensuales")
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

            # ── Opciones de cálculo ──
            col_chk1, col_chk2 = st.columns(2)
            with col_chk1:
                solo_con_lluvia = st.checkbox(
                    "☔ Solo años con lluvia registrada (PP máx > 0)",
                    value=True,
                    help=(
                        "Excluye los años donde la precipitación máxima diaria registrada fue 0 mm. "
                        "Estos años suelen corresponder a períodos sin datos o sin eventos de lluvia, "
                        "y distorsionan los percentiles hacia abajo.\n\n"
                        "✅ Recomendado en casi todos los casos."
                    )
                )
            with col_chk2:
                excluir_maximo = st.checkbox(
                    "⚙️ Excluir el valor máximo histórico",
                    value=False,
                    help=(
                        "El valor máximo absoluto siempre se muestra en métricas y gráficos — "
                        "esta opción solo afecta el cálculo de percentiles (P10–P90).\n\n"
                        "✅ Útil para caracterización climática en series con eventos extremos aislados.\n\n"
                        "❌ No recomendado para evaluación de peligros o EVAR."
                    )
                )

            # Percentiles — cálculo completo con rangos
            df_anual_tab2 = df_diario.groupby('año')['pp'].max().reset_index()
            n_años_serie = len(df_anual_tab2)
            pp_max_abs = df_anual_tab2['pp'].max()

            # Filtrar años sin lluvia si se solicita
            notas_exclusion = []
            if solo_con_lluvia:
                n_antes = len(df_anual_tab2)
                df_anual_tab2 = df_anual_tab2[df_anual_tab2['pp'] > 0].reset_index(drop=True)
                n_excluidos = n_antes - len(df_anual_tab2)
                if n_excluidos > 0:
                    notas_exclusion.append(f"☔ {n_excluidos} año(s) con PP máx = 0 excluidos del cálculo de percentiles.")

            # Serie para percentiles: con o sin el máximo histórico
            if excluir_maximo:
                idx_max = df_anual_tab2['pp'].idxmax()
                df_perc = df_anual_tab2.drop(index=idx_max).reset_index(drop=True)
                notas_exclusion.append(f"⚙️ Valor máximo histórico ({pp_max_abs:.1f} mm) excluido. Serie usada: {len(df_perc)} de {n_años_serie} años.")
            else:
                df_perc = df_anual_tab2.copy()
                nota_exclusion = None

            n_perc = len(df_perc)
            p10_tab2 = round(df_perc['pp'].quantile(0.10), 1)
            p25_tab2 = round(df_perc['pp'].quantile(0.25), 1)
            p50_tab2 = round(df_perc['pp'].quantile(0.50), 1)
            p75_tab2 = round(df_perc['pp'].quantile(0.75), 1)
            p90_tab2 = round(df_perc['pp'].quantile(0.90), 1)
            pct_años_sobre_p90 = round(len(df_anual_tab2[df_anual_tab2['pp'] > p90_tab2]) / n_años_serie * 100, 1)
            n_años_sobre_p90 = len(df_anual_tab2[df_anual_tab2['pp'] > p90_tab2])

            for _nota in notas_exclusion:
                st.caption(_nota)

            # Frases en lenguaje natural con rangos completos
            frase_bajo_p10 = f"En 1 de cada 10 años la máxima diaria no supera los <strong>{p10_tab2} mm</strong> — año excepcionalmente seco en términos de eventos extremos."
            frase_p10_p25  = f"La máxima diaria se mueve entre <strong>{p10_tab2} y {p25_tab2} mm</strong> en el 15% de los años."
            frase_p25_p50  = f"La máxima diaria se mueve entre <strong>{p25_tab2} y {p50_tab2} mm</strong> en el 25% de los años — rango bajo-típico."
            frase_p50_p75  = f"La máxima diaria se mueve entre <strong>{p50_tab2} y {p75_tab2} mm</strong> en el 25% de los años — rango alto-típico."
            frase_p75_p90  = f"La máxima diaria se mueve entre <strong>{p75_tab2} y {p90_tab2} mm</strong> en el 15% de los años — por encima de lo habitual."
            frase_sobre_p90 = f"Solo <strong>{n_años_sobre_p90} de {n_años_serie} años</strong> superaron los <strong>{p90_tab2} mm</strong> — evento de alta magnitud y baja frecuencia."

            st.markdown(f"""
            <div style="background:#f4faf7; border:1px solid #c8e6d4; border-radius:10px; padding:1rem 1.5rem; margin-bottom:1rem;">
                <div style="font-size:0.72rem; font-weight:700; color:#3d7a5a; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.8rem;">
                    📐 Umbrales estadísticos de precipitación máxima diaria — Rangos por frecuencia de ocurrencia
                </div>
                <table style="width:100%; border-collapse:collapse; font-size:0.87rem;">
                    <thead>
                        <tr style="background:#dff0ec;">
                            <th style="padding:7px 12px; text-align:left; color:#2e4d31; font-weight:700; border-bottom:2px solid #b2d8c8; width:22%;">Rango</th>
                            <th style="padding:7px 12px; text-align:center; color:#2e4d31; font-weight:700; border-bottom:2px solid #b2d8c8; width:18%;">Valores (mm)</th>
                            <th style="padding:7px 12px; text-align:left; color:#2e4d31; font-weight:700; border-bottom:2px solid #b2d8c8;">¿Qué significa para esta estación?</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom:1px solid #e8f4ef; background:#f0f7ff;">
                            <td style="padding:7px 12px; color:#2980b9; font-weight:700;">Por debajo del P10</td>
                            <td style="padding:7px 12px; text-align:center; color:#2980b9; font-weight:700;">&lt; {p10_tab2} mm</td>
                            <td style="padding:7px 12px; color:#555;">{frase_bajo_p10}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e8f4ef;">
                            <td style="padding:7px 12px; color:#27ae60; font-weight:700;">P10 – P25</td>
                            <td style="padding:7px 12px; text-align:center; color:#27ae60; font-weight:700;">{p10_tab2} – {p25_tab2} mm</td>
                            <td style="padding:7px 12px; color:#555;">{frase_p10_p25}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e8f4ef; background:#fafffe;">
                            <td style="padding:7px 12px; color:#1a6b35; font-weight:700;">P25 – P50</td>
                            <td style="padding:7px 12px; text-align:center; color:#1a6b35; font-weight:700;">{p25_tab2} – {p50_tab2} mm</td>
                            <td style="padding:7px 12px; color:#555;">{frase_p25_p50}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e8f4ef;">
                            <td style="padding:7px 12px; color:#d4a017; font-weight:700;">P50 – P75 <span style="font-size:0.75rem; color:#888; font-weight:400;">(rango central)</span></td>
                            <td style="padding:7px 12px; text-align:center; color:#d4a017; font-weight:700;">{p50_tab2} – {p75_tab2} mm</td>
                            <td style="padding:7px 12px; color:#555;">{frase_p50_p75}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e8f4ef; background:#fafffe;">
                            <td style="padding:7px 12px; color:#e67e22; font-weight:700;">P75 – P90</td>
                            <td style="padding:7px 12px; text-align:center; color:#e67e22; font-weight:700;">{p75_tab2} – {p90_tab2} mm</td>
                            <td style="padding:7px 12px; color:#555;">{frase_p75_p90}</td>
                        </tr>
                        <tr style="background:#fff5f5;">
                            <td style="padding:7px 12px; color:#c0392b; font-weight:700;">Por encima del P90</td>
                            <td style="padding:7px 12px; text-align:center; color:#c0392b; font-weight:700;">&gt; {p90_tab2} mm</td>
                            <td style="padding:7px 12px; color:#555;">{frase_sobre_p90}</td>
                        </tr>
                    </tbody>
                </table>
                <div style="font-size:0.75rem; color:#888; margin-top:8px;">
                    ⚠️ Estos umbrales describen el comportamiento histórico de la estación. Para estimación de caudales de diseño o evaluación de peligros, utiliza el Análisis de Frecuencias (Gumbel) — disponible en MapDrop v3.0.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)

            with st.expander("📖 ¿Qué significan estos umbrales? — Fundamento metodológico"):
                st.markdown(
                    "En el análisis de frecuencias hidrológicas (OMM, 2009, Cap. 27), un **umbral de precipitación** "
                    "es un valor de referencia estadístico que permite clasificar los registros históricos según su "
                    "magnitud y frecuencia de ocurrencia. MapDrop calcula dos umbrales a partir de la serie histórica cargada:\n\n"
                    "* **Percentil 50 (Mediana):** Significa que el 50% de los años registró una precipitación máxima "
                    "anual igual o inferior a este valor. Representa el comportamiento habitual de la estación.\n"
                    "* **Percentil 90:** Significa que solo el 10% de los años superó este valor. Corresponde a un "
                    "evento de baja frecuencia de ocurrencia y alta magnitud (OMM, 2009, Cap. 28).\n\n"
                    "Estos umbrales permiten identificar qué años presentaron precipitaciones máximas dentro del rango "
                    "habitual y cuáles se alejaron significativamente de ese comportamiento.\n\n"
                    "**Consideraciones metodológicas:**\n"
                    "* Con series menores a 15 años, los percentiles son estadísticamente inestables.\n"
                    "* Este método no reemplaza el análisis de frecuencias con distribuciones probabilísticas "
                    "(Gumbel, Log-Pearson III, GEV) para estimar períodos de retorno formales.\n"
                    "* No incorpora información fisiográfica que pueda condicionar la respuesta hidrológica real.\n\n"
                    "**Referencia:** Organización Meteorológica Mundial. (2009). *Guía de prácticas hidrológicas* "
                    "(6.ª ed., OMM-N° 168, Cap. 27–28). OMM. "
                    "[📄 Descargar libro](https://www.academia.edu/28131870/GUIDE_YDROLOGICAL_PRACTICES_ADQUISICI%C3%93N_Y_PROCESO_DE_DATOS_AN%C3%81LISIS_PREDICCI%C3%93N_Y_OTRAS_APLICACIONES_GU%C3%8DA_DE_PR%C3%81CTICAS_HIDROL%C3%93GICAS_Bienvenido)"
                )

            # --- MATRIZ Y DESCARGA ---
            st.divider()
            st.write("Haz clic en el botón de abajo para obtener la matriz completa en formato Excel.")

            tobol = io.BytesIO()
            with pd.ExcelWriter(tobol, engine='xlsxwriter') as writer:
                df_matriz.to_excel(writer, index=True, sheet_name='Matriz_PP_Max')
            tobol.seek(0)

            st.download_button(
                label="📗 Descargar tabla de Precipitaciones Máximas (.xlsx)",
                data=tobol.getvalue(),
                file_name=f"Matriz_PP_Max_{metadata['Estación']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            st.divider()

            # --- GRÁFICOS (integrados en esta misma pestaña) ---
            f1_dinamico, umbral_medio, umbral_alto = ana.grafico_pp_max_anual(df_todo, filtrar_ceros=solo_con_lluvia)
            f2_boxplot, mes_habitual = ana.grafico_boxplot(df_todo)
            f3_hist, intensidad_media = ana.grafico_histograma(df_todo)
            max_historico = df_todo['pp'].max()
            anio_max = df_todo.loc[df_todo['pp'].idxmax(), 'año']
            veces_promedio = max_historico / umbral_medio if umbral_medio > 0 else 0
            eventos_criticos = len(df_todo[df_todo['pp'] > umbral_alto])

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
                    "**Consideraciones metodológicas:**\n"
                    "* Con series menores a 15 años, los percentiles son estadísticamente inestables.\n"
                    "* Este método no reemplaza el análisis de frecuencias con distribuciones probabilísticas "
                    "(Gumbel, Log-Pearson III, GEV) para estimar períodos de retorno formales.\n"
                    "* No incorpora información fisiográfica que pueda condicionar la respuesta hidrológica real.\n\n"
                    "**Referencia:** Organización Meteorológica Mundial. (2009). *Guía de prácticas hidrológicas* "
                    "(6.ª ed., OMM-N° 168, Cap. 27–28). OMM. "
                    "[📄 Descargar libro](https://www.academia.edu/28131870/GUIDE_YDROLOGICAL_PRACTICES_ADQUISICI%C3%93N_Y_PROCESO_DE_DATOS_AN%C3%81LISIS_PREDICCI%C3%93N_Y_OTRAS_APLICACIONES_GU%C3%8DA_DE_PR%C3%81CTICAS_HIDROL%C3%93GICAS_Bienvenido)"
                )

            st.warning(
                "⚠️ **Limitaciones del análisis**\n\n"
                "Los umbrales se calculan a partir de la propia serie cargada. **Series con menos de 15–20 años "
                "de registro pueden producir umbrales estadísticamente inestables**, subestimando o sobreestimando "
                "el comportamiento real de la zona.\n\n"
                "Los resultados son de **carácter exploratorio**. Su interpretación y aplicación en decisiones "
                "técnicas requiere la revisión de un profesional especializado en hidrología o ingeniería hidráulica."
            )

            # ── Fila 1: Máximas anuales | Boxplot ──
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown(f"### Precipitaciones Máximas Anuales")
                st.caption(f"P50: **{umbral_medio:.1f} mm** · P90: **{umbral_alto:.1f} mm** · Máx: **{max_historico:.1f} mm** ({int(anio_max)}) · Eventos >P90: **{eventos_criticos}**")
                st.plotly_chart(f1_dinamico, use_container_width=True)
                with st.expander("🔍 ¿Cómo interpretar este gráfico?"):
                    st.markdown(
                        "Precipitación máxima en 24 h por año.\n\n"
                        "* 🟢 **Verde:** dentro del comportamiento habitual (< P50).\n"
                        "* 🟡 **Amarillo:** entre P50 y P90.\n"
                        "* 🔴 **Rojo:** supera el P90 — evento de baja frecuencia y alta magnitud.\n\n"
                        "La línea roja punteada marca el Percentil 90 de la serie."
                    )
            with col_g2:
                st.markdown(f"### Variabilidad Mensual de Precipitaciones")
                st.caption(f"Mes con mayor magnitud: **{mes_habitual}** · Puntos = registros sobre el rango intercuartílico.")
                st.plotly_chart(f2_boxplot, use_container_width=True)
                with st.expander("🔍 ¿Cómo interpretar este gráfico?"):
                    st.markdown(
                        "Distribución de precipitaciones diarias por mes en toda la serie.\n\n"
                        "* **Línea central:** mediana · **Bordes:** P25–P75 · **Bigotes:** rango sin atípicos.\n"
                        "* **Puntos aislados:** registros de alta magnitud dentro del mes."
                    )

            st.divider()

            # ── Fila 2: Histograma ancho ──
            st.markdown(f"### Distribución de Frecuencias de Precipitación Diaria — {anio_inicio} al {anio_fin}")
            st.caption(f"Precipitación media en días con registro > 0.1 mm: **{intensidad_media:.1f} mm/día** · Los valores hacia la derecha corresponden a eventos de baja frecuencia y alta magnitud.")
            st.plotly_chart(f3_hist, use_container_width=True)
            with st.expander("🔍 ¿Cómo interpretar este gráfico?"):
                st.markdown(
                    "Frecuencia de distintos rangos de precipitación diaria (solo días > 0.1 mm).\n\n"
                    "* Barras altas a la izquierda = lluvias de baja magnitud frecuentes.\n"
                    "* Barras bajas a la derecha = eventos de alta magnitud y baja frecuencia.\n\n"
                    "Estos valores extremos alimentan el análisis de frecuencias para caudales de diseño (OMM, 2009)."
                )

        # ═══════════════════════════════════════════════════
        # TAB 3 — INDICADORES PP HORARIA (solo EMA horario)
        # ═══════════════════════════════════════════════════
        if tab3 is not None:
            with tab3:
                st.markdown("### ⏱️ Análisis Horario — Estación EMA")

                if df_horario_ema is not None and not df_horario_ema.empty:
                    metricas = ana.calcular_metricas_horarias(df_horario_ema)

                    if metricas:
                        st.markdown(f"""
                        <div class="mapdrop-metrics-row" style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:1rem;">
                            <div class="metric-card">
                                <div class="metric-tooltip">El valor de precipitación horaria más alto registrado en toda la serie. Representa el evento de mayor intensidad en una hora.</div>
                                <div class="metric-icon">⚡</div>
                                <div class="metric-label">Máxima Horaria Histórica</div>
                                <div class="metric-value">{metricas['max_pp_hora']} mm/h</div>
                                <div class="metric-sub">📅 {metricas['max_fecha']}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-tooltip">Hora del día en que, en promedio, se registran las precipitaciones de mayor intensidad en la estación.</div>
                                <div class="metric-icon">🕐</div>
                                <div class="metric-label">Hora Pico de Intensidad</div>
                                <div class="metric-value">{metricas['hora_pico']}:00 h</div>
                                <div class="metric-sub">Intensidad media: {metricas['intensidad_hora_pico']} mm/h</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-tooltip">Promedio de precipitación en todas las horas con registro mayor a 0 mm/h. Indica la intensidad típica de un evento horario en la estación.</div>
                                <div class="metric-icon">💧</div>
                                <div class="metric-label">Intensidad Media Horaria</div>
                                <div class="metric-value">{metricas['media_horaria']} mm/h</div>
                                <div class="metric-sub">En horas con precipitación > 0</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown(f"""
                        <div class="mapdrop-metrics-row" style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:1rem;">
                            <div class="metric-card">
                                <div class="metric-tooltip">El 50% de las horas con lluvia registró una precipitación igual o inferior a este valor. Representa la intensidad horaria habitual.</div>
                                <div class="metric-icon">📏</div>
                                <div class="metric-label">Percentil 50 Horario</div>
                                <div class="metric-value">{metricas['p50_horario']} mm/h</div>
                                <div class="metric-sub">Intensidad horaria habitual</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-tooltip">Solo el 10% de las horas con lluvia superó este valor. Corresponde a eventos de alta intensidad y baja frecuencia horaria.</div>
                                <div class="metric-icon">⚠️</div>
                                <div class="metric-label">Percentil 90 Horario</div>
                                <div class="metric-value">{metricas['p90_horario']} mm/h</div>
                                <div class="metric-sub">Solo el 10% de las horas lo superó</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-tooltip">Porcentaje de horas con lluvia que superaron el Percentil 90 horario. Indica qué tan frecuentes son los eventos de alta intensidad.</div>
                                <div class="metric-icon">📈</div>
                                <div class="metric-label">Horas sobre P90</div>
                                <div class="metric-value">{metricas['pct_p90']}%</div>
                                <div class="metric-sub">Umbral: {metricas['p90_horario']} mm/h · {metricas['eventos_p90']} horas</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.divider()

                        col_h1, col_h2 = st.columns(2)
                        with col_h1:
                            st.markdown("#### Eventos Horarios de Precipitación")
                            st.caption("Cada punto con lluvia > 0 mm/h. Rojos superan el P90 horario.")
                            fig_horario, umbral_horario = ana.grafico_eventos_horarios(df_horario_ema)
                            if fig_horario:
                                st.plotly_chart(fig_horario, use_container_width=True)
                                with st.expander("🔍 ¿Cómo interpretar?"):
                                    st.markdown(
                                        "* 🟢 **Verde:** comportamiento habitual.\n"
                                        "* 🔴 **Rojo:** supera el P90 horario — evento de alta intensidad.\n\n"
                                        "Los datos EMA registran precipitación acumulada cada hora."
                                    )
                        with col_h2:
                            st.markdown("#### Intensidad Media por Hora del Día")
                            st.caption("¿A qué hora llueve con mayor intensidad?")
                            fig_hora_dia = ana.grafico_intensidad_por_hora(df_horario_ema)
                            if fig_hora_dia:
                                st.plotly_chart(fig_hora_dia, use_container_width=True)
                                with st.expander("🔍 ¿Cómo interpretar?"):
                                    st.markdown(
                                        "Intensidad promedio por hora sobre todos los registros con lluvia > 0.\n\n"
                                        "La barra más alta indica la hora de mayor intensidad histórica."
                                    )
                else:
                    st.warning("No se encontraron datos horarios EMA para analizar.")

        # ═══════════════════════════════════════════════════
        # TAB TEMPERATURA Y CLIMA
        # ═══════════════════════════════════════════════════
        if tab_temp is not None:
            with tab_temp:
                st.subheader("🌡️ Temperatura y Clima")

                for a in archivos_temp:
                    a.seek(0)
                df_temp = temp.procesar_multiples_temperatura(archivos_temp)

                if df_temp is not None and not df_temp.empty:
                    df_mensual = temp.calcular_estadisticos_mensuales(df_temp, df_pp=df_todo)
                    metricas_t = temp.calcular_metricas_globales(df_temp)

                    anio_t_ini = metricas_t.get('anio_inicio', '')
                    anio_t_fin = metricas_t.get('anio_fin', '')

                    # ── MÉTRICAS GLOBALES ──
                    st.markdown(f"""
                    <div class="mapdrop-metrics-row" style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:16px; margin-bottom:1rem;">
                        <div class="metric-card">
                            <div class="metric-tooltip">Promedio de temperatura media diaria ((Tmax+Tmin)/2) calculado sobre toda la serie histórica cargada.</div>
                            <div class="metric-icon">🌡️</div>
                            <div class="metric-label">Temperatura Media Anual</div>
                            <div class="metric-value">{metricas_t.get('tmedia_anual', '—')} °C</div>
                            <div class="metric-sub">Serie {anio_t_ini}–{anio_t_fin}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-tooltip">Valor máximo absoluto de temperatura registrado en cualquier día de la serie histórica.</div>
                            <div class="metric-icon">🔴</div>
                            <div class="metric-label">Tmax Absoluta Histórica</div>
                            <div class="metric-value">{metricas_t.get('tmax_abs', '—')} °C</div>
                            <div class="metric-sub">Mes más cálido: {metricas_t.get('mes_calido', '—')}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-tooltip">Valor mínimo absoluto de temperatura registrado en cualquier día de la serie histórica.</div>
                            <div class="metric-icon">🔵</div>
                            <div class="metric-label">Tmin Absoluta Histórica</div>
                            <div class="metric-value">{metricas_t.get('tmin_abs', '—')} °C</div>
                            <div class="metric-sub">Mes más fresco: {metricas_t.get('mes_fresco', '—')}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-tooltip">Promedio de humedad relativa diaria sobre toda la serie histórica cargada.</div>
                            <div class="metric-icon">💧</div>
                            <div class="metric-label">Humedad Relativa Media</div>
                            <div class="metric-value">{metricas_t.get('hr_media', '—')} %</div>
                            <div class="metric-sub">Media histórica anual</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.divider()

                    # ── Métricas de viento (solo si EMA met) ──
                    if metricas_t.get('tiene_viento'):
                        st.markdown(f"""
                        <div class="mapdrop-metrics-row" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:1rem;">
                            <div class="metric-card">
                                <div class="metric-tooltip">Promedio de velocidad del viento registrada hora a hora, agregada a diario.</div>
                                <div class="metric-icon">💨</div>
                                <div class="metric-label">Velocidad Media del Viento</div>
                                <div class="metric-value">{metricas_t.get('vel_media', '—')} m/s</div>
                                <div class="metric-sub">Media histórica diaria</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-tooltip">Valor más alto de velocidad media diaria en toda la serie.</div>
                                <div class="metric-icon">🌬️</div>
                                <div class="metric-label">Velocidad Máxima Registrada</div>
                                <div class="metric-value">{metricas_t.get('vel_max', '—')} m/s</div>
                                <div class="metric-sub">Máximo de la serie</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-tooltip">Mes con mayor velocidad media del viento sobre toda la serie.</div>
                                <div class="metric-icon">📅</div>
                                <div class="metric-label">Mes más Ventoso</div>
                                <div class="metric-value">{metricas_t.get('mes_ventoso', '—')}</div>
                                <div class="metric-sub">Mayor velocidad media mensual</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.divider()

                    # ── Fila 1: Temperatura | Ombrotérmico ──
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        st.markdown("### Temperatura Máxima y Mínima Mensual")
                        st.caption("🔴 Tmax · 🔵 Tmin · Naranja punteado: Tmedia · Área: rango térmico diario")
                        fig_t = temp.grafico_temperatura_mensual(df_mensual)
                        if fig_t:
                            st.plotly_chart(fig_t, use_container_width=True)
                        with st.expander("🔍 ¿Cómo interpretar?"):
                            st.markdown(
                                "Promedio mensual de Tmax y Tmin sobre todos los años de la serie.\n\n"
                                "El área sombreada es el rango térmico diario típico del mes.\n"
                                "Rango estrecho = temperatura estable. Rango amplio = mayor oscilación diaria."
                            )
                    with col_t2:
                        st.markdown("### Diagrama Ombrotérmico Walter-Lieth")
                        st.caption("🔵 Período húmedo (PP > 2T) · 🟠 Período seco (PP < 2T)")
                        fig_ombo = temp.grafico_ombrotermica(df_mensual)
                        if fig_ombo:
                            st.plotly_chart(fig_ombo, use_container_width=True)
                        with st.expander("🔍 ¿Cómo interpretar?"):
                            st.markdown(
                                "Temperatura media y precipitación mensual simultáneamente.\n\n"
                                "Convención: escala PP = 2 × escala T (10°C = 20 mm).\n"
                                "* 🔵 **Húmedo:** PP > 2T · 🟠 **Seco:** PP < 2T.\n\n"
                                "Ref: Walter & Lieth (1960). *Klimadiagramm-Weltatlas*."
                            )

                    st.divider()

                    # ── Fila 2: HR | Viento (o HR ancho si no hay viento) ──
                    fig_hr     = temp.grafico_hr_mensual(df_mensual)
                    fig_viento = temp.grafico_viento_mensual(df_mensual) if metricas_t.get('tiene_viento') else None

                    if fig_viento:
                        col_t3, col_t4 = st.columns(2)
                        with col_t3:
                            st.markdown("### Humedad Relativa Media Mensual")
                            st.caption("🔵 ≥ 70% (húmedo) · 🟠 60–70% · 🔴 < 60% (seco)")
                            if fig_hr:
                                st.plotly_chart(fig_hr, use_container_width=True)
                            with st.expander("🔍 ¿Cómo interpretar?"):
                                st.markdown("Promedio mensual de HR. La línea punteada = 70%, umbral de ambiente húmedo.")
                        with col_t4:
                            st.markdown("### Velocidad Media del Viento Mensual")
                            st.caption("Verde oscuro = meses sobre 120% de la media anual")
                            st.plotly_chart(fig_viento, use_container_width=True)
                            with st.expander("🔍 ¿Cómo interpretar?"):
                                st.markdown("Velocidad media mensual (m/s). Línea punteada = media anual histórica.")
                    else:
                        st.markdown(f"### Humedad Relativa Media Mensual — {anio_t_ini} al {anio_t_fin}")
                        st.caption("🔵 ≥ 70% (húmedo) · 🟠 60–70% · 🔴 < 60% (seco)")
                        if fig_hr:
                            st.plotly_chart(fig_hr, use_container_width=True)
                        with st.expander("🔍 ¿Cómo interpretar?"):
                            st.markdown("Promedio mensual de HR. La línea punteada = 70%, umbral de ambiente húmedo.")

                    st.divider()

                    # ── TABLA RESUMEN MENSUAL ──
                    st.markdown("### Tabla de Estadísticos Mensuales")
                    df_tabla = df_mensual[['nombre_mes', 'tmax_med', 'tmin_med', 'tmedia', 'hr_med', 'pp_total_med']].copy()
                    df_tabla.columns = ['Mes', 'Tmax media (°C)', 'Tmin media (°C)', 'Tmedia (°C)', 'HR media (%)', 'PP total media (mm)']
                    st.dataframe(df_tabla.set_index('Mes'), use_container_width=True)

                    # ── DESCARGA EXCEL ──
                    buffer_temp = io.BytesIO()
                    with pd.ExcelWriter(buffer_temp, engine='xlsxwriter') as writer:
                        df_temp.to_excel(writer, index=False, sheet_name='Datos_Diarios_Temp')
                        df_tabla.to_excel(writer, index=False, sheet_name='Resumen_Mensual')
                    buffer_temp.seek(0)

                    st.download_button(
                        label="🌡️ Descargar Excel — Temperatura y Clima",
                        data=buffer_temp.getvalue(),
                        file_name=f"Temperatura_{metadata['Estación']}_{anio_t_ini}_{anio_t_fin}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                else:
                    st.warning("No se pudieron procesar los archivos de temperatura. Verifica que el formato sea el correcto (CSV SENAMHI con columnas MAX, MIN, HR).")

        # ═══════════════════════════════════════════════════
        # TAB COMPARAR ESTACIONES
        # ═══════════════════════════════════════════════════
    else:
        st.error("No se pudieron procesar los archivos.")
else:
    # Landing page
    st.markdown("<h1 style='text-align: center; margin-top: -2rem;'>💧 MapDrop</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray; font-size: 1.2rem;'>Procesamiento inteligente de datos hidrometeorológicos</p>", unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h3 style='color:#2e4d31; font-size:1.4rem;'>¿Qué hace MapDrop?</h3>", unsafe_allow_html=True)
        st.markdown("Es una herramienta diseñada por **MapLecture** para automatizar la gestión de datos del SENAMHI:")
        st.markdown("* **Estandarización:** Convierte archivos TXT, CSV y XLSX a un formato limpio y listo para analizar.")
        st.markdown("* **Complementación automática:** Combina múltiples fuentes (TXT histórico, estaciones automáticas EMA, convencionales) priorizando la fuente más confiable cuando se superponen.")
        st.markdown("* **Cálculo automático:** Genera matrices de precipitaciones máximas, estadísticos e indicadores de temperatura, humedad y viento al instante.")
        st.markdown("* **Verificación de datos:** Identifica días sin registro en tu serie para que sepas si los datos están completos antes de usarlos.")

    with col2:
        st.markdown("<h3 style='color:#2e4d31; font-size:1.4rem;'>¿Cómo usarla?</h3>", unsafe_allow_html=True)
        st.markdown("1. **Busca tu estación:** Usa el buscador del panel izquierdo para encontrar tu estación por nombre o código. Desde ahí puedes ir directo a la página de descarga del SENAMHI.")
        st.markdown("2. **Carga los datos:** Arrastra tus archivos al panel izquierdo (TXT, CSV o XLSX). Puedes combinar varios archivos de la misma estación.")
        st.markdown("3. **MapDrop combina automáticamente** múltiples fuentes y prioriza los datos convencionales sobre los de estaciones automáticas (EMA) cuando coinciden en fecha.")
        st.markdown("4. **Analiza:** Navega por las pestañas para ver la validación, indicadores de precipitación, temperatura y gráficos.")
        st.markdown("5. **Descarga:** Exporta tus resultados directamente a Excel.")

    st.markdown("---")
    st.info("👈 **Comienza ahora:** Sube tus archivos en la barra lateral para activar el análisis.")