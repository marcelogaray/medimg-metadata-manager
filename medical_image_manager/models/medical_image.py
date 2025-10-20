"""
Módulo de Modelo de Imagen Médica
=================================

Este módulo define la clase MedicalImage para representar imágenes médicas
y sus metadatos asociados.

Clases:
    MedicalImage: Clase principal para representación de imágenes médicas
"""

from typing import Optional, Dict, Any, Union
import numpy as np
from datetime import datetime
import uuid


class MedicalImage:
    """
    Representa una imagen médica con sus metadatos y datos de píxeles.
    
    Esta clase encapsula toda la información relacionada con una imagen médica,
    incluyendo datos de píxeles, metadatos e información de archivo.
    
    Atributos:
        image_id (str): Identificador único para la imagen
        filename (str): Nombre de archivo original de la imagen
        pixel_data (Optional[np.ndarray]): Array de datos de píxeles de la imagen
        metadata (Dict[str, Any]): Diccionario que contiene metadatos de la imagen
        format_type (str): Formato de imagen (ej., 'DICOM', 'NIfTI')
        creation_date (datetime): Cuándo se creó el objeto imagen
        last_modified (datetime): Cuándo se modificó la imagen por última vez
        file_size (Optional[int]): Tamaño del archivo de imagen en bytes
    """
    
    def __init__(
        self,
        filename: str,
        pixel_data: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None,
        format_type: str = "Desconocido",
        file_size: Optional[int] = None
    ):
        """
        Inicializar una nueva instancia de MedicalImage.
        
        Args:
            filename (str): Nombre de archivo original de la imagen
            pixel_data (Optional[np.ndarray]): Datos de píxeles de la imagen
            metadata (Optional[Dict[str, Any]]): Diccionario de metadatos de la imagen
            format_type (str): Formato del archivo de imagen
            file_size (Optional[int]): Tamaño del archivo en bytes
        """
        self.image_id: str = str(uuid.uuid4())
        self.filename: str = filename
        self.pixel_data: Optional[np.ndarray] = pixel_data
        self.metadata: Dict[str, Any] = metadata or {}
        self.format_type: str = format_type
        self.creation_date: datetime = datetime.now()
        self.last_modified: datetime = datetime.now()
        self.file_size: Optional[int] = file_size
    
    def update_metadata(self, key: str, value: Any) -> None:
        """
        Actualizar un campo de metadatos.
        
        Args:
            key (str): Nombre del campo de metadatos
            value (Any): Nuevo valor para el campo
        """
        self.metadata[key] = value
        self.last_modified = datetime.now()
    
    def get_metadata(self, key: str) -> Optional[Any]:
        """
        Obtener un valor de metadatos por clave.
        
        Args:
            key (str): Nombre del campo de metadatos
            
        Returns:
            Optional[Any]: Valor de metadatos o None si la clave no existe
        """
        return self.metadata.get(key)
    
    def remove_metadata(self, key: str) -> bool:
        """
        Eliminar un campo de metadatos.
        
        Args:
            key (str): Nombre del campo de metadatos a eliminar
            
        Returns:
            bool: True si la clave fue eliminada, False si la clave no existía
        """
        if key in self.metadata:
            del self.metadata[key]
            self.last_modified = datetime.now()
            return True
        return False
    
    def get_image_info(self) -> Dict[str, Any]:
        """
        Obtener información completa sobre la imagen.
        
        Returns:
            Dict[str, Any]: Diccionario que contiene información de la imagen
        """
        info = {
            "image_id": self.image_id,
            "filename": self.filename,
            "format_type": self.format_type,
            "creation_date": self.creation_date.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "file_size": self.file_size,
            "has_pixel_data": self.pixel_data is not None,
            "metadata_fields": list(self.metadata.keys())
        }
        
        if self.pixel_data is not None:
            info.update({
                "image_shape": self.pixel_data.shape,
                "image_dtype": str(self.pixel_data.dtype),
                "pixel_data_size": self.pixel_data.nbytes
            })
        
        return info
    
    def validate_data(self) -> bool:
        """
        Validar la integridad de los datos de la imagen.
        
        Returns:
            bool: True si los datos de la imagen son válidos, False en caso contrario
        """
        if not self.filename:
            return False
        
        if self.pixel_data is not None:
            if not isinstance(self.pixel_data, np.ndarray):
                return False
            if self.pixel_data.size == 0:
                return False
        
        return True
    
    def __str__(self) -> str:
        """Representación en cadena de la MedicalImage."""
        return f"MedicalImage(id={self.image_id[:8]}, filename={self.filename})"
    
    def __repr__(self) -> str:
        """Representación detallada en cadena de la MedicalImage."""
        return (f"MedicalImage(image_id='{self.image_id}', "
                f"filename='{self.filename}', "
                f"format_type='{self.format_type}', "
                f"has_pixel_data={self.pixel_data is not None})")