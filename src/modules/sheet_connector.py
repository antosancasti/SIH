import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

class SheetConnector:
    """
    Agente: DevOps y Data Specialist
    Responsabilidad: Conectar con Google Sheets a través de st.secrets de manera segura,
    sin solicitar intervención manual.
    """
    SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]

    @staticmethod
    def _get_mock_data():
        """
        Retorna datos de prueba (Prueba de Extracción) si no hay credenciales configuradas.
        """
        data = [
            {"SKU": "STEREN-001", "Nombre": "Fuente de Poder A", "Especificaciones": "Entrada: 500mA | Salida: 5V \n Uso ultra rápido comercial"},
            {"SKU": "STEREN-002", "Nombre": "Fuente de Poder B", "Especificaciones": "Entrada: 0.5A - Salida: 5000mV \n Súper eficiente"},
            {"SKU": "STEREN-003", "Nombre": "Cable USB", "Especificaciones": "Longitud: 100cm | Corriente: 2A"},
            {"SKU": "STEREN-004", "Nombre": "Cable Type C", "Especificaciones": "Longitud: 1m - Corriente: 2000mA"},
            {"SKU": "STEREN-005", "Nombre": "Bluetooth Adapter", "Especificaciones": "Frecuencia: 2400MHz | Alcance: 10m"}
        ]
        return pd.DataFrame(data)

    @classmethod
    def load_data(cls):
        """
        Intenta cargar datos desde Sheets usando configuraciones en secreto.
        De lo contrario, usa datos de prueba.
        """
        has_secrets = "gcp_service_account" in st.secrets and "sheet_settings" in st.secrets
        
        if not has_secrets:
            # Fallback a la prueba de extracción solicitada
            st.warning("⚠️ No se encontraron credenciales GCP o URL del Sheet en st.secrets. Mostrando Prueba de Extracción (Mock).")
            return cls._get_mock_data()
        
        try:
            creds_dict = dict(st.secrets["gcp_service_account"])
            # Ajuste en caso de keys de Streamlit
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, cls.SCOPE)
            client = gspread.authorize(creds)
            
            sheet_url = st.secrets["sheet_settings"]["spreadsheet_url"]
            sheet = client.open_by_url(sheet_url).sheet1
            
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error al conectar con Google Sheets: {str(e)}")
            st.info("Asegúrate de que la Service Account tenga permisos de Lector en el Google Sheet.")
            return cls._get_mock_data()
