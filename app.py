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
# Tonos: Azul Corporativo (#002855), Azul Claro (#00A8E1), Fondo (#F4F6F9)
st.markdown("""
    <style>
    /* Tipografía moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Fondo principal corporativo claro */
    .stApp {
        background-color: #F8F9FA;
        color: #212529;
    }
    
    /* Sidebar oscuro para contraste elegante */
    [data-testid="stSidebar"] {
        background-color: #002855 !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    /* Títulos principales */
    h1, h2, h3 {
        color: #002855 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    
    /* Detalles / Acentos */
    .st-emotion-cache-10trblm {
        color: #00A8E1 !important;
    }
    
    /* Estilo de Dataframes para comparativas limpias */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        background-color: #FFFFFF;
    }
    
    /* Alerta elegante */
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
        
    # Detectar columna de especificaciones dinámicamente
    specs_col = None
    for col in df_raw.columns:
        if "especificacion" in col.lower() or "caracteristica" in col.lower():
            specs_col = col
            break
            
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
    # Ignoramos filas con el nombre del modelo
    if row.name in ["Nombre", "SKU", "MODELO", "Modelo"]:
        return [''] * len(row)
        
    if len(row.dropna().unique()) > 1:
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
    mode = st.sidebar.radio("", ("📊 Benchmarking", "🎯 Matcher Pro"))

    # DETECCIÓN DINÁMICA DE LA COLUMNA IDENTIFICADORA
    # Buscamos qué columna usar como título de la comparativa
    id_candidates = ["MODELO", "Modelo", "SKU", "Nombre", "PRODUCTO", "Producto"]
    model_col = None
    for cand in id_candidates:
        if cand in df.columns:
            model_col = cand
            break
    
    # Si no hay ninguna obvia, tomamos la primera columna categórica
    if not model_col and len(df.columns) > 0:
        model_col = df.columns[0]

    # Preparamos el display poniendo al modelo como índice para que al trasponer queden arriba
    if model_col:
        df_display = df.set_index(model_col)
        # Limpiar índice de nulos para no romper selectboxes
        df_display = df_display[df_display.index.notnull()]
    else:
        df_display = df

    if "Benchmarking" in mode:
        st.markdown("### 📊 Benchmarking Técnico")
        st.write("Selecciona los SKUs o Modelos que deseas alinear para comparar sus especificaciones.")
        
        selected_indices = st.multiselect(
            "Modelos a cruzar:",
            options=df_display.index.astype(str).tolist(),
            default=df_display.index.astype(str).tolist()[:3] if len(df_display) >= 3 else df_display.index.astype(str).tolist()
        )
        
        if selected_indices:
            # Filtrar cuidando el tipo de dato
            df_filtered = df_display.loc[df_display.index.astype(str).isin(selected_indices)]
            
            # Matriz transpuesta
            df_transposed = df_filtered.T
            
            st.markdown("<br><h5>Comparativa Visual Analítica</h5>", unsafe_allow_html=True)
            st.caption("Las especificaciones resaltadas en azul claro indican que existen diferencias técnicas entre los productos seleccionados.")
            
            st.dataframe(
                df_transposed.style.apply(highlight_differences, axis=1),
                use_container_width=True,
                height=500
            )
            
            with st.expander("Inspeccionar datos en vista original (Sin transposición)"):
                st.dataframe(df_filtered, use_container_width=True)

    elif "Matcher Pro" in mode:
        st.markdown("### 🎯 Matcher Pro")
        st.write("Inserta parámetros de búsqueda técnicos (o copia texto con ruido) para encontrar su equivalente en nuestro catálogo.")
        
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


if __name__ == "__main__":
    main()
