import streamlit as st
import analisis_ppmaximas as ana
import pandas as pd
import io

# 1. Configuración de página (SIEMPRE debe ser lo primero que ve Streamlit)
st.set_page_config(page_title="HidroAnálisis SENAMHI", layout="wide")

# 2. Título principal
st.title("📊 Procesador de Precipitaciones Máximas")

# 3. Barra Lateral - Parte Superior
st.sidebar.title("🌊 HidroTool Punchana")
st.sidebar.markdown("---")

# Subidor de archivos
archivos = st.sidebar.file_uploader("Subir archivos (TXT y CSV)", type=['csv', 'txt'], accept_multiple_files=True)

st.sidebar.markdown("---")

# 4. Sección de Apoyo (Esta puede estar fuera porque no depende de los datos)
st.sidebar.subheader("☕ Apoya este proyecto")
st.sidebar.write("Esta herramienta es gratuita. Si te sirvió, puedes apoyar su mantenimiento:")
st.sidebar.markdown("[👉 Invítame un café (PayPal/Card)](https://www.buymeacoffee.com/tu_usuario)")
st.sidebar.info("📱 Yape/Plin: **9XX XXX XXX**")

# 5. Lógica de procesamiento
if archivos:
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
        **Autora:** Brenda  
        **Idea Original:** Análisis de peligros por inundación en Punchana.  
        **Colaboración:** Desarrollado con el apoyo de IA (Gemini).
        """)
        st.sidebar.caption(f"Versión 1.0 | Datos procesados de {anio_inicio} a {anio_fin}")

        # Generación de Matriz y Pestañas
        df_matriz = ana.generar_matriz_maximos(df_todo)
        tab1, tab2, tab3 = st.tabs(["📅 Matriz Mensual", "📄 Datos Diarios", "📈 Gráficos Estadísticos"])
        
        with tab1:
            st.subheader("Matriz de Precipitaciones Máximas Mensuales")
            st.dataframe(df_matriz, use_container_width=True)
            tobol = io.BytesIO()
            df_matriz.to_excel(tobol, index=True)
            st.download_button("📗 Descargar Matriz Excel", data=tobol.getvalue(), file_name="Matriz_PP.xlsx")
            
        with tab2:
            st.subheader("Compendio de Datos Diarios Unificados")
            st.dataframe(df_todo, use_container_width=True)
            
        with tab3:
            st.header("📈 ¿Cómo leer estos resultados?")
            st.info("Utiliza estos paneles para entender el comportamiento de las lluvias.")

            max_valor = df_todo['pp'].max()
            mes_peligro_num = df_todo.loc[df_todo['pp'].idxmax(), 'mes']
            meses_nombres = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio',
                             7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
            mes_nombre_max = meses_nombres[mes_peligro_num]

            f1, f2, f3, f4 = ana.generar_graficos(df_todo)

            col1, col2 = st.columns(2)
            with col1:
                with st.expander("🔍 EXPLICACIÓN: El historial de tormentas"):
                    st.write(f"Muestra la lluvia más fuerte de cada año desde {anio_inicio} hasta {anio_fin}.")
                st.plotly_chart(f1, use_container_width=True)

            with col2:
                with st.expander("🔍 EXPLICACIÓN: Los meses de mayor riesgo"):
                    st.write(f"Récord histórico en {total_anios} años: {max_valor} mm en {mes_nombre_max}.")
                st.plotly_chart(f2, use_container_width=True)
            
            col3, col4 = st.columns(2)
            with col3: st.plotly_chart(f3, use_container_width=True)
            with col4: st.plotly_chart(f4, use_container_width=True)
    else:
        st.error("No se pudieron procesar los archivos.")
else:
    st.info("👈 Por favor, sube los archivos TXT y CSV en la barra lateral para comenzar.")
    st.sidebar.warning("Esperando datos para mostrar versión...")