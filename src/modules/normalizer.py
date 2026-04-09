import re
import pandas as pd

class DataNormalizer:
    @staticmethod
    def _parse_attributes(text):
        if pd.isna(text) or not isinstance(text, str):
            return []
        parts = re.split(r'\||\n', text)
        return [p.strip() for p in parts if p.strip()]

    @classmethod
    def process_dataframe(cls, df, target_columns):
        df_clean = df.copy()
        
        for col in target_columns:
            if col not in df_clean.columns:
                continue
                
            expanded_rows = []
            for index, row in df_clean.iterrows():
                specs_text = row[col]
                attributes = cls._parse_attributes(specs_text)
                
                row_dict = row.to_dict()
                
                # Para evitar borrar todo si no parseamos nada
                parsed_something = False
                extra_features = []
                
                for attr in attributes:
                    attr_cl = attr.replace("*", "").replace("DESCRIPCIÓN TÉCNICA", "").replace("(Sitio Oficial)", "").strip()
                    if attr_cl.startswith("- "):
                        attr_cl = attr_cl[2:].strip()
                    if attr_cl.startswith("-"):
                        attr_cl = attr_cl[1:].strip()
                    
                    if not attr_cl:
                        continue
                        
                    if ":" in attr_cl:
                        key, val = attr_cl.split(":", 1)
                        if " - " in key:
                            key = key.split(" - ")[-1]
                        
                        key = key.strip()
                        if not key:
                            continue
                            
                        val = val.strip()
                        # Normalizar valores vacios a un guion
                        if not val: val = "-"
                        row_dict[key] = val
                        parsed_something = True
                    else:
                        extra_features.append(attr_cl)
                        
                if extra_features:
                    row_dict["📝 Otras Características Técnicas"] = " • " + " \n • ".join(extra_features)
                    parsed_something = True
                
                if not parsed_something:
                    row_dict["Specs_Crudo"] = specs_text
                        
                expanded_rows.append(row_dict)
                
            df_clean = pd.DataFrame(expanded_rows)
            df_clean = df_clean.drop(columns=[col])
            
        return df_clean
