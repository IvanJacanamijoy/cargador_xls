from fastapi import HTTPException, status


class InvalidFileException(HTTPException):
    def __init__(self, detail: str = "Archivo inválido"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class FileTooLargeException(HTTPException):
    def __init__(self, max_size_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo demasiado grande. Máximo: {max_size_mb}MB"
        )


class NoFileUploadedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se subió ningún archivo"
        )


class ProcessingException(Exception):
    """Excepción para errores durante el procesamiento"""
    pass


class DatabaseException(HTTPException):
    def __init__(self, detail: str = "Error en la base de datos"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )