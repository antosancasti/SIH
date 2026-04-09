import re
import pandas as pd

class DataNormalizer:
    """
    Agente: Data Specialist
    Responsabilidad: Expandir el bloque de especificaciones en múltiples columnas para permitir
    una verdadera matriz comparativa side-by-side.
    """

    @staticmethod
    def _parse_attributes(text):
        """
        Extrae atributos separados por pipes (|).
        """
        if pd.isna(text) or not isinstance(text, str):
            return []
        
        parts = re.split(r'\|', text)
        return [p.strip() for p in parts if p.strip()]

    @classmethod
    def process_dataframe(cls, df, target_columns):
        """
        Toma la columna de especificaciones (ej: "Alimentación: 24V | Lúmenes: 650")
        y la expande en múltiples columnas dinámicas hacia la derecha.
        """
        df_clean = df.copy()
        
        for col in target_columns:
            if col not in df_clean.columns:
                continue
                
            expanded_rows = []
            for index, row in df_clean.iterrows():
                specs_text = row[col]
                attributes = cls._parse_attributes(specs_text)
                
                # Convertimos la fila en diccionario
                row_dict = row.to_dict()
                
                for attr in attributes:
                    if ":" in attr:
                        key, val = attr.split(":", 1)
                        # Limpiar basura publicitaria como "*** DESCRIPCIÓN TÉCNICA... *** - "
                        if " - " in key:
                            key = key.split(" - ")[-1]
                        
                        key = key.replace("*", "").replace("DESCRIPCIÓN TÉCNICA", "").replace("(Sitio Oficial)", "").strip()
                        if not key:
                            key = "Atributo"
                            
                        row_dict[key] = val.strip()
                
                expanded_rows.append(row_dict)
                
            # Sobreescribimos el dataframe con las nuevas columnas expandidas
            df_clean = pd.DataFrame(expanded_rows)
            # Removemos la columna gigante original para dejar limpio el comparador
            df_clean = df_clean.drop(columns=[col])
            
        return df_clean
