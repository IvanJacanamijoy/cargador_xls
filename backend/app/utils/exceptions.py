from fastapi import HTTPException, status

class InvalidFileException(HTTPException):
    def __init__(self, detail: str = "Archivo inválido"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class FileTooLargeException(HTTPException):
    def __init__(self, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo permitido ({max_mb} MB)"
        )


class NoFileUploadedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se recibió ningún archivo"
        )


class BatchNotFoundException(HTTPException):
    def __init__(self, batch_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el batch con ID: {batch_id}"
        )
