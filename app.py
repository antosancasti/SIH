# VERSION: 2 - Cache Invalidation
import streamlit as st
import pandas as pd
from thefuzz import process
from src.modules.sheet_connector import SheetConnector
from src.modules.normalizer import DataNormalizer

# Configuración de página: Tema profesional Steren (Claro/Corporativo)
st.set_page_config(
    page_title="Steren Intelligence Hub",
    page_icon="🟦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS para Diseño PREMIUM STEREN
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #F8F9FA;
        color: #212529;
    }
    
    [data-testid="stSidebar"] {
        background-color: #002855 !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    h1, h2, h3 {
        color: #002855 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    
    .st-emotion-cache-10trblm {
        color: #00A8E1 !important;
    }
    
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        background-color: #FFFFFF;
    }
    
    .stAlert {
        border-radius: 8px;
        border-left: 5px solid #00A8E1;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def fetch_and_prepare_data():
    df_raw = SheetConnector.load_data()
    if df_raw.empty:
        return df_raw
    
    # 1. Quitar espacios accidentales en los nombres de las columnas (ej: "MODELO " a "MODELO")
    df_raw.columns = df_raw.columns.astype(str).str.strip()
        
    # 2. Detectar columna de especificaciones dinámicamente
    specs_col = None
    for col in df_raw.columns:
        if "especificacion" in col.lower() or "caracteristica" in col.lower():
            specs_col = col
            break
            
    # 3. La magia del Normalizador (Desglosar la cadena gigante en múltiples columnas reales)
    if specs_col:
        df_clean = DataNormalizer.process_dataframe(df_raw, [specs_col])
    else:
        df_clean = df_raw.copy()
        
    return df_clean

def highlight_differences(row):
    """
    Resalta (highlight) la celda si las especificaciones son asimétricas (diferentes).
    Fondo sutil azul claro de Steren para llamar la atención elegantemente.
    """
    if row.name in ["Nombre", "SKU", "MODELO", "Modelo", "PRODUCTO"]:
        return [''] * len(row)
        
    # Eliminamos nulos/vacíos para ver si realmente hay una diferencia
    unique_vals = [str(x).strip() for x in row.dropna().unique() if str(x).strip() != '']
    if len(unique_vals) > 1:
        return ['background-color: #E6F6FD; color: #002855; font-weight: bold; border-left: 3px solid #00A8E1'] * len(row)
    return [''] * len(row)

def main():
    st.markdown("<h1>Steren <span style='color: #00A8E1;'>Intelligence Hub</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.1em; color: #555;'>Herramienta matriz de cruce técnico de información corporativa.</p>", unsafe_allow_html=True)

    with st.spinner("Sincronizando con matriz de datos..."):
        df = fetch_and_prepare_data()

    if df.empty:
        st.warning("No se encontraron datos.")
        return

    st.sidebar.markdown("<h2>Herramientas</h2>", unsafe_allow_html=True)
    mode = st.sidebar.radio("", ("📊 Benchmarking", "🎯 Matcher Pro"), key="main_sidebar_mode")

    # DETECCIÓN DINÁMICA DE LA COLUMNA IDENTIFICADORA (El Nombre del Modelo)
    id_candidates = ["MODELO", "Modelo", "SKU", "Nombre", "PRODUCTO", "Producto"]
    model_col = None
    for cand in id_candidates:
        if cand in df.columns:
            model_col = cand
            break
    
    if not model_col and len(df.columns) > 0:
        model_col = df.columns[0]

    # Asignar el índice y descartar filas completamente vacías en el modelo
    if model_col:
        df_display = df.set_index(model_col)
        # Limpiar filas donde el modelo esté en blanco (NaN o string vacío)
        df_display = df_display[df_display.index.notnull()]
        df_display = df_display[df_display.index != ""]
    else:
        df_display = df

    if "Benchmarking" in mode:
        st.markdown("### 📊 Benchmarking Técnico")
        st.write("Selecciona los SKUs o Modelos que deseas alinear para comparar sus especificaciones lado a lado.")
        
        all_models = df_display.index.astype(str).tolist()
        # Escoger predeterminadamente los primeros 3 (o menos)
        default_selection = all_models[:3] if len(all_models) >= 3 else all_models
        
        selected_indices = st.multiselect(
            "Modelos a cruzar:",
            options=all_models,
            default=default_selection
        )
        
        if selected_indices:
            # Filtrar por los modelos exactos
            df_filtered = df_display.loc[df_display.index.astype(str).isin(selected_indices)]
            
            # MATRIZ TRANSPUESTA
            # Al hacer .T, nuestras columnas recién creadas por el normalizador se vuelven las filas perfectas
            df_transposed = df_filtered.T
            
            # Quitar filas que solo digan NaN o None en todo para los modelos seleccionados
            df_transposed = df_transposed.dropna(how='all')
            
            st.markdown("<br><h5>Comparativa Visual Analítica</h5>", unsafe_allow_html=True)
            st.caption("Las especificaciones resaltadas en azul claro indican que existen diferencias técnicas entre los productos.")
            
            st.dataframe(
                df_transposed.style.apply(highlight_differences, axis=1),
                use_container_width=True,
                height=700
            )
            
            with st.expander("Inspeccionar datos en crudo (Base de Datos)"):
                st.dataframe(df_filtered, use_container_width=True)
        else:
            st.info("👈 Por favor, selecciona al menos un modelo en la caja superior para iniciar la comparativa.")

    elif "Matcher Pro" in mode:
        st.markdown("### 🎯 Matcher Pro")
        st.write("Inserta parámetros de búsqueda técnicos (o copia texto con ruido) para localizar productos.")
        
        search_corpus = df.astype(str).agg(' | '.join, axis=1).tolist()
        search_query = st.text_input("Ingresa parámetros técnicos a buscar:")
        
        if search_query:
            matches = process.extract(search_query, search_corpus, limit=5)
            st.markdown("<hr>", unsafe_allow_html=True)
            for match, score in matches:
                color = "#00A8E1" if score > 70 else ("#FFB81C" if score > 40 else "#C0C0C0")
                st.markdown(f"""
                <div style="border-left: 5px solid {color}; padding-left: 15px; margin-bottom: 20px; background-color: white; padding: 15px; border-radius: 0 8px 8px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h4 style="margin:0; color: #002855;">Relevancia: {score}%</h4>
                    <p style="margin-top:5px; color: #444; font-size: 0.9em;">{match}</p>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
