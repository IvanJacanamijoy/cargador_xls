# app/utils/logger.py
import logging
import sys
from pathlib import Path

# Crear directorio de logs si no existe
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado
    
    Args:
        name: Nombre del logger (normalmente __name__)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicados
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo
    file_handler = logging.FileHandler(LOG_DIR / f"{name.split('.')[-1]}.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


# app/utils/validators.py
import re
from typing import Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Validator:
    """Validadores personalizados para datos"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida formato de teléfono (flexible)"""
        if not phone:
            return True  # Opcional
        
        # Remover caracteres especiales
        clean_phone = re.sub(r'[^\d+]', '', phone)
        return len(clean_phone) >= 7  # Mínimo 7 dígitos
    
    @staticmethod
    def validate_string(value: Optional[str], min_length: int = 1, 
                       max_length: int = 255) -> bool:
        """Valida longitud de string"""
        if value is None:
            return True
        
        value_str = str(value).strip()
        return min_length <= len(value_str) <= max_length
    
    @staticmethod
    def validate_numeric(value: Optional[str], min_val: float = None, 
                        max_val: float = None) -> bool:
        """Valida valores numéricos"""
        if value is None or value == "":
            return True
        
        try:
            num = float(value)
            
            if min_val is not None and num < min_val:
                return False
            
            if max_val is not None and num > max_val:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_string(value: Optional[str]) -> Optional[str]:
        """Limpia string removiendo espacios extras"""
        if value is None:
            return None
        
        return str(value).strip()
    
    @staticmethod
    def convert_to_float(value: Optional[str]) -> Optional[float]:
        """Convierte string a float"""
        if value is None or value == "":
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None