from openpyxl import load_workbook
import xlrd
from typing import List, Tuple
import logging
import os

logger = logging.getLogger(__name__)

class FileProcessor:
    """Procesa archivos XLS/XLSX y extrae datos"""

    OPTIONAL_COLUMNS = ["telefono", "valor", "descripcion"]

    @staticmethod
    def validate_file(file_path: str) -> bool:
        """Valida que el archivo sea XLS o XLSX válido"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".xlsx", ".xls"]:
            raise ValueError("El archivo debe ser .xlsx o .xls")

        try:
            if ext == ".xlsx":
                workbook = load_workbook(file_path, read_only=True, data_only=True)
                if not workbook.sheetnames:
                    raise ValueError("El archivo no contiene hojas")
            else:
                workbook = xlrd.open_workbook(file_path)
                if workbook.nsheets == 0:
                    raise ValueError("El archivo no contiene hojas")
            return True
        except Exception as e:
            logger.error(f"Error validando archivo: {e}")
            raise ValueError(f"Archivo inválido: {e}")

    @staticmethod
    def extract_data(file_path: str) -> Tuple[List[dict], List[dict]]:
        """Extrae datos del archivo XLS/XLSX"""
        valid_data = []
        errors = []
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == ".xlsx":
                workbook = load_workbook(file_path, data_only=True)
                worksheet = workbook.active
                headers = [str(cell.value).lower().strip() for cell in worksheet[1] if cell.value]
                rows = worksheet.iter_rows(min_row=2, values_only=True)
            else:
                workbook = xlrd.open_workbook(file_path)
                sheet = workbook.sheet_by_index(0)
                headers = [str(sheet.cell_value(0, col)).lower().strip() for col in range(sheet.ncols)]
                rows = (sheet.row_values(row_idx) for row_idx in range(1, sheet.nrows))

            if not headers:
                raise ValueError("El archivo no tiene encabezados")


            for row_idx, row in enumerate(rows, start=2):
                try:
                    row_data = {}
                    for col_idx, header in enumerate(headers):
                        value = row[col_idx] if col_idx < len(row) else None
                        if header in FileProcessor.REQUIRED_COLUMNS and (not value or str(value).strip() == ""):
                            raise ValueError(f"Campo obligatorio '{header}' vacío")
                        row_data[header] = value

                    email = str(row_data.get("email", "")).strip()
                    if "@" not in email or "." not in email:
                        raise ValueError(f"Email inválido: {email}")

                    valid_data.append(row_data)

                except ValueError as e:
                    errors.append({
                        "row_number": row_idx,
                        "error": str(e),
                        "data": dict(zip(headers, row)) if row else {}
                    })
                except Exception as e:
                    errors.append({
                        "row_number": row_idx,
                        "error": f"Error procesando fila: {str(e)}",
                        "data": dict(zip(headers, row)) if row else {}
                    })

            logger.info(f"Procesamiento completado: {len(valid_data)} válidos, {len(errors)} errores")
            return valid_data, errors

        except Exception as e:
            logger.error(f"Error extrayendo datos: {e}")
            raise

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Obtiene tamaño del archivo en bytes"""
        return os.path.getsize(file_path)
