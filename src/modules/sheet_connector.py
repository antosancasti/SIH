import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

class SheetConnector:
    """
    Agente: DevOps y Data Specialist
    Responsabilidad: Conectar con Google Sheets a través de st.secrets de manera segura.
    Nueva Arquitectura: Ahora extrae DIRECTAMENTE la DB limpia pre-procesada por ETL Agent
    para un rendimiento web extremo.
    """
    SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]

    @classmethod
    def load_clean_data(cls):
        """
        Carga explícitamente la pestaña STEREN_CLEAN_DB generada por el Master Agent.
        """
        has_secrets = "gcp_service_account" in st.secrets and "sheet_settings" in st.secrets
        
        if not has_secrets:
            st.warning("⚠️ Sin credenciales GCP. Configura st.secrets.")
            return pd.DataFrame()
        
        try:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, cls.SCOPE)
            client = gspread.authorize(creds)
            
            sheet_url = st.secrets["sheet_settings"]["spreadsheet_url"]
            spreadsheet = client.open_by_url(sheet_url)
            
            try:
                ws_clean = spreadsheet.worksheet("STEREN_CLEAN_DB")
                records = ws_clean.get_all_records()
                df = pd.DataFrame(records)
                return df
            except gspread.exceptions.WorksheetNotFound:
                st.error("❌ STEREN_CLEAN_DB no existe. Por favor, ejecuta primero el Master Agent (tools/master_agent.py).")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Error al conectar con Google Sheets: {str(e)}")
            return pd.DataFrame()
