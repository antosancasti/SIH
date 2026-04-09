# VERSION: 4 - ETL Preprocessed Data Fetching
import streamlit as st
import pandas as pd
from thefuzz import process
from src.modules.sheet_connector import SheetConnector

st.set_page_config(
    page_title="Steren Intelligence Hub",
    page_icon="🟦",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    # En esta versión 4, ya NO parseamos aquí. El Master ETL Agent 
    # ya hizo el trabajo duro de normalizar y limpiar con Regex.
    # Así ahorramos miles de ms en el Frontend web.
    df = SheetConnector.load_clean_data()
    return df

def highlight_differences(row):
    """
    Resalta (highlight) la celda si las especificaciones son asimétricas (diferentes).
    Fondo sutil azul claro de Steren para llamar la atención elegantemente.
    """
    if row.name in ["Nombre", "SKU", "MODELO", "Modelo", "PRODUCTO"]:
        return [''] * len(row)
        
    unique_vals = [str(x).strip() for x in row.dropna().unique() if str(x).strip() != '']
    if len(unique_vals) > 1:
        return ['background-color: #E6F6FD; color: #002855; font-weight: bold; border-left: 3px solid #00A8E1'] * len(row)
    return [''] * len(row)

def main():
    st.markdown("<h1>Steren <span style='color: #00A8E1;'>Intelligence Hub</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.1em; color: #555;'>Herramienta matriz de cruce técnico de información corporativa (Datos ETL Pre-procesados).</p>", unsafe_allow_html=True)

    with st.spinner("Sincronizando con base de datos maestra STEREN_CLEAN_DB..."):
        df = fetch_and_prepare_data()

    if df.empty:
        st.warning("La base de datos está vacía. Por favor corre el flujo del Master Agent (tools/master_agent.py).")
        return

    st.sidebar.markdown("<h2>Herramientas</h2>", unsafe_allow_html=True)
    mode = st.sidebar.radio("", ("📊 Benchmarking", "🎯 Matcher Pro"), key="main_sidebar_mode")

    id_candidates = ["MODELO", "Modelo", "SKU", "Nombre", "PRODUCTO", "Producto"]
    model_col = None
    for cand in id_candidates:
        if cand in df.columns:
            model_col = cand
            break
    
    if not model_col and len(df.columns) > 0:
        model_col = df.columns[0]

    # --- PIVOT PARA RESTAURAR LA MATRIZ DE BENCHMARKING DE FORMA DINÁMICA ---
    # Si la base de datos viene en formato Vertical (Unpivoted) para que no sea estorbosa en Sheets,
    # la convertimos de vuelta a matriz ancha (Pivoted) en memoria RAM para la gráfica.
    if "Atributo Tecnico" in df.columns and "Valor" in df.columns and model_col:
        try:
            df = df.pivot_table(index=model_col, columns="Atributo Tecnico", values="Valor", aggfunc='first').reset_index()
        except:
            pass


    if model_col:
        df_display = df.set_index(model_col)
        df_display = df_display[df_display.index.notnull()]
        df_display = df_display[df_display.index != ""]
        df_display = df_display[~df_display.index.duplicated(keep='first')]
        df_display = df_display.loc[:, ~df_display.columns.duplicated(keep='first')]
    else:
        df_display = df

    if "Benchmarking" in mode:
        st.markdown("### 📊 Benchmarking Técnico")
        st.write("Selecciona los modelos a comparar. **Nota:** Estos datos han sido estandarizados automáticamente por IA (Normalización de Unidades + NLP).")
        
        all_models = df_display.index.astype(str).tolist()
        default_selection = all_models[:3] if len(all_models) >= 3 else all_models
        
        selected_indices = st.multiselect(
            "Modelos a cruzar:",
            options=all_models,
            default=default_selection
        )
        
        if selected_indices:
            df_filtered = df_display.loc[df_display.index.astype(str).isin(selected_indices)]
            df_transposed = df_filtered.T
            df_transposed = df_transposed.dropna(how='all')
            
            # Limpiar filas donde todos sean '-' o vacíos
            df_transposed = df_transposed[~df_transposed.apply(lambda row: all(str(val).strip() in ['-', '', 'nan'] for val in row), axis=1)]
            
            st.markdown("<br><h5>Comparativa Visual Analítica</h5>", unsafe_allow_html=True)
            st.caption("Las especificaciones resaltadas en azul claro indican que existen diferencias técnicas entre los productos.")
            
            st.dataframe(
                df_transposed.style.apply(highlight_differences, axis=1),
                use_container_width=False,
                height=700
            )
            
            with st.expander("Inspeccionar datos en crudo (Matriz Limpia)"):
                st.dataframe(df_filtered, use_container_width=True)
        else:
            st.info("👈 Por favor, selecciona al menos un modelo en la caja superior para iniciar la comparativa.")

    elif "Matcher Pro" in mode:
        st.markdown("### 🎯 Matcher Pro")
        st.write("Búsqueda Fuzzy sobre el corpus de descripciones técnicas procesadas.")
        
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
