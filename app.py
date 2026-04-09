import streamlit as st
import pandas as pd
from thefuzz import process
from src.modules.sheet_connector import SheetConnector
from src.modules.normalizer import DataNormalizer

# Configuración de página de alto rendimiento y tono sobrio
st.set_page_config(
    page_title="Steren Intelligence Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilización inyectada para diseño profesional/sobrio
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .css-1d391kg {
        background-color: #1E2129;
    }
    h1, h2, h3 {
        color: #00ADEF !important; /* Azul Steren aprox */
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def fetch_and_prepare_data():
    """
    Obtiene los datos y aplica la normalización atómica (Data Specialist cacheada).
    """
    df_raw = SheetConnector.load_data()
    # Asume que la columna es 'Especificaciones', ajustable según los datos reales
    if "Especificaciones" in df_raw.columns:
        df_clean = DataNormalizer.process_dataframe(df_raw, ["Especificaciones"])
    else:
        df_clean = df_raw.copy()
    return df_clean

def highlight_differences(row):
    """
    Resalta (highlight) la celda entera si no todos los valores en la fila son idénticos.
    (útil para transposición de benchmarking).
    """
    if len(row.unique()) > 1:
        return ['background-color: #4A154B; color: white'] * len(row)
    return [''] * len(row)

def main():
    st.title("Steren Intelligence Hub ⚡")
    st.markdown("Plataforma de Consulta Masiva y Referencia Técnica Pura.")

    # Carga de datos
    with st.spinner("Sincronizando con base de datos e inyectando Data Specialist..."):
        df = fetch_and_prepare_data()

    if df.empty:
        st.warning("No se encontraron datos.")
        return

    st.sidebar.header("🛡️ Especialista en Herramientas")
    mode = st.sidebar.radio("Selecciona Modo Operativo:", 
                            ("Consulta / Benchmarking", "Matcher Pro"))

    # Configuración de columnas clave
    # Si tenemos 'SKU' lo usaremos de índice si es posible
    if "SKU" in df.columns:
        df_display = df.set_index("SKU")
    else:
        df_display = df

    if mode == "Consulta / Benchmarking":
        st.header("📊 Benchmarking Mode")
        st.write("Selecciona productos de la tabla para compararlos side-by-side.")
        
        # Filtro de selección múltiple (hasta límite visual sano)
        selected_indices = st.multiselect(
            "Selecciona Modelos a Comparar",
            options=df_display.index.tolist(),
            default=df_display.index.tolist()[:3] if len(df_display) >= 3 else df_display.index.tolist()
        )
        
        if selected_indices:
            df_filtered = df_display.loc[selected_indices]
            
            # Matriz transpuesta para side-by-side
            df_transposed = df_filtered.T
            
            # Aplicar estilo de resaltado
            st.markdown("### Comparativa Side-by-Side")
            st.caption("Las filas subrayadas resaltan especificaciones asimétricas entre los productos.")
            st.dataframe(
                df_transposed.style.apply(highlight_differences, axis=1),
                use_container_width=True,
                height=600
            )
            
            with st.expander("Ver tabla en formato crudo sin transposición"):
                st.dataframe(df_filtered, use_container_width=True)

    elif mode == "Matcher Pro":
        st.header("🎯 Matcher Pro")
        st.markdown("Encuentra productos por descripciones o parámetros técnicos que pueden estar mal escritos o tener variaciones (Ej. competencia).")
        
        # Opciones para buscar
        # Juntamos texto descriptivo
        if 'Nombre' in df.columns and 'Especificaciones' in df.columns:
            search_corpus = (df['SKU'].astype(str) + " - " + 
                             df['Nombre'].astype(str) + " | " + 
                             df['Especificaciones'].astype(str)).tolist()
        else:
            search_corpus = df.astype(str).agg(' '.join, axis=1).tolist()
            
        search_query = st.text_input("Ingresa parámetros a buscar (Ej. cable tipo C rápido 5V 1A):")
        
        if search_query:
            # Uso de TheFuzz
            matches = process.extract(search_query, search_corpus, limit=5)
            
            st.subheader("Resultados de Equivalencia (Regex + Fuzz):")
            for match, score in matches:
                if score > 60:
                    st.success(f"Coincidencia: {score}% \n\n {match}")
                elif score > 40:
                    st.warning(f"Coincidencia: {score}% \n\n {match}")
                else:
                    st.error(f"Coincidencia: {score}% \n\n {match}")
                    
            st.caption("El score indica la probabilidad de equivalencia evaluando parámetros normalizados.")

if __name__ == "__main__":
    main()
