import re
import pandas as pd
import unicodedata

class DataNormalizer:
    @staticmethod
    def _limpiar_acentos(texto):
        texto = unicodedata.normalize('NFD', str(texto))
        return texto.encode('ascii', 'ignore').decode('utf-8')

    @staticmethod
    def _estandarizar_unidades(valor):
        """Estandariza unidades comunes para que todas las métricas sean uniformes"""
        val_lower = str(valor).lower().strip()
        
        # Regex para normalizar Miliamperios
        if re.search(r'ma\b|miliamp|mili\s?amp', val_lower):
            numero = re.search(r'([\d\.]+)', val_lower)
            if numero: return f"{numero.group(1)} mA"
            
        # Regex para Voltajes
        if re.search(r'v\b|volt|vca|vcc', val_lower):
            numero = re.search(r'([\d\.]+)', val_lower)
            tipo = "Vca" if "ca" in val_lower or "ac" in val_lower else ("Vcc" if "cc" in val_lower or "dc" in val_lower else "V")
            if numero: return f"{numero.group(1)} {tipo}"
            
        # Frecuencia
        if re.search(r'hz|hertz', val_lower):
            numero = re.search(r'([\d\.]+)', val_lower)
            unidad = "GHz" if "ghz" in val_lower else ("MHz" if "mhz" in val_lower else "Hz")
            if numero: return f"{numero.group(1)} {unidad}"
            
        # Dimensiones / Distancia
        if re.search(r'cm|centimetros|metros|mm|milimetros', val_lower):
            numero = re.search(r'([\d\.]+)', val_lower)
            unidad = "mm" if "mm" in val_lower or "mili" in val_lower else ("cm" if "cm" in val_lower or "centi" in val_lower else "m")
            if numero: return f"{numero.group(1)} {unidad}"
            
        return valor.strip()

    @staticmethod
    def _parse_attributes(text):
        if pd.isna(text) or not isinstance(text, str):
            return []
        
        # Separar primero por saltos de línea y tuberías
        parts = re.split(r'\||\n', text)
        
        final_parts = []
        for p in parts:
            p = p.strip()
            if not p: continue
            
            # Sub-separar por guiones intermedios que fungen como separadores de lista
            # ej "100 pulgadas - Fácil de limpiar - Rápido"
            subparts = re.split(r'\s+-\s+', p)
            final_parts.extend(subparts)
            
        return [p.strip() for p in final_parts if p.strip()]

    @classmethod
    def process_dataframe(cls, df, target_columns):
        df_clean = df.copy()
        
        for col in target_columns:
            if col not in df_clean.columns: continue
                
            expanded_rows = []
            for index, row in df_clean.iterrows():
                specs_text = row[col]
                attributes = cls._parse_attributes(specs_text)
                row_dict = row.to_dict()
                
                parsed_something = False
                extra_features = []
                
                for attr in attributes:
                    attr_cl = attr.replace("*", "").replace("DESCRIPCIÓN TÉCNICA", "").replace("(Sitio Oficial)", "").strip()
                    attr_cl = re.sub(r'^-+\s*', '', attr_cl)
                    
                    if not attr_cl:
                        continue
                        
                    match = re.match(r'^([^:]+):\s+(.*)$', attr_cl)
                    if match:
                        key = match.group(1)
                        val = match.group(2)
                        if " - " in key:
                            key = key.split(" - ")[-1]
                        
                        key = cls._limpiar_acentos(key.strip().title())
                        if not key or len(key) > 60:
                            extra_features.append(attr_cl)
                            continue
                            
                        val = cls._estandarizar_unidades(val)
                        if not val: val = "-"
                        
                        row_dict[key] = val
                        parsed_something = True
                    else:
                        if len(attr_cl) > 3:
                            key_booleana = cls._limpiar_acentos(attr_cl.strip().title())
                            if len(key_booleana) < 60:
                                row_dict[key_booleana] = "Sí"
                                parsed_something = True
                            else:
                                extra_features.append(attr_cl)
                        
                if extra_features:
                    row_dict["Otras Caracteristicas Adicionales"] = " \n> ".join(extra_features)
                    parsed_something = True
                
                if not parsed_something:
                     if pd.isna(specs_text) or str(specs_text).strip() == "":
                         row_dict["Revisión"] = "Falta información técnica oficial"
                     else:
                         row_dict["Info Cruda"] = specs_text
                        
                expanded_rows.append(row_dict)
                
            df_clean = pd.DataFrame(expanded_rows)
            
        df_clean = df_clean.loc[:, ~df_clean.columns.str.contains('^Unnamed')]
        return df_clean
