import re
import pandas as pd

class DataNormalizer:
    """
    Agente: Data Specialist
    Responsabilidad: Referencia Técnica Pura, Parsing de Precisión y Normalización de Unidades.
    """

    @staticmethod
    def _parse_attributes(text):
        """
        Extrae atributos separados por pipes (|), guiones (-) o saltos de línea (\n).
        """
        if pd.isna(text) or not isinstance(text, str):
            return []
        
        # Separar por pipe, salto de línea, o guion estructurado rodeado de espacios
        parts = re.split(r'\||\n| - ', text)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _normalize_unit(value_str):
        """
        Normaliza unidades estándar. Convierte sub-unidades como mA a A, mV a V.
        Extrae los valores numéricos y la unidad.
        """
        value_str = value_str.lower().replace(' ', '')
        
        # Patrón para número y una unidad potencial
        match = re.search(r'([\d\.]+)([a-z]+)', value_str)
        if not match:
            return value_str
        
        val, unit = match.groups()
        try:
            val = float(val)
        except ValueError:
            return value_str
            
        unit_map = {
            'ma': ('a', 0.001),
            'mv': ('v', 0.001),
            'mw': ('w', 0.001),
            'ka': ('a', 1000),
            'kv': ('v', 1000),
            'kw': ('w', 1000),
            'hz': ('hz', 1),
            'khz': ('hz', 1000),
            'mhz': ('hz', 1000000),
            'ghz': ('hz', 1000000000),
            'cm': ('m', 0.01),
            'mm': ('m', 0.001),
        }
        
        if unit in unit_map:
            base_unit, multiplier = unit_map[unit]
            normalized_val = val * multiplier
            # Remover cero decimal si es entero
            if normalized_val.is_integer():
                normalized_val = int(normalized_val)
            return f"{normalized_val}{base_unit}"
            
        return f"{val}{unit}"

    @classmethod
    def clean_specifications(cls, specs_text):
        """
        Toma un texto de especificaciones, lo parsea, y normaliza sus unidades.
        Elimina ruido comercial asumiendo que el ruido no tiene números ni unidades reconocibles.
        (Versión base muy agresiva para extraer características medibles).
        """
        attributes = cls._parse_attributes(specs_text)
        cleaned = []
        for attr in attributes:
            # Buscamos normalizar componentes dentro del atributo (ej: "Entrada: 500mA")
            # Divide en palabras/tokens simples
            tokens = attr.split()
            normalized_tokens = []
            for t in tokens:
                # Si luce como valor técnico (número pegado a letra o simplemente un número)
                if any(char.isdigit() for char in t):
                    normalized_tokens.append(cls._normalize_unit(t))
                else:
                    normalized_tokens.append(t)
            cleaned.append(" ".join(normalized_tokens))
        return " | ".join(cleaned)

    @classmethod
    def process_dataframe(cls, df, target_columns):
        """
        Aplica limpieza y normalización atómica a las columnas objetivo del DataFrame.
        """
        df_clean = df.copy()
        for col in target_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(cls.clean_specifications)
        return df_clean
