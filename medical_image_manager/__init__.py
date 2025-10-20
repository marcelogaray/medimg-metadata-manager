"""
Paquete Gestor de Imágenes Médicas
==================================

Un paquete integral para gestionar imágenes médicas y sus metadatos
con fines de investigación.

Este paquete proporciona funcionalidad para:
- Registro, modificación y eliminación de imágenes médicas
- Gestión y persistencia de metadatos
- Soporte para múltiples formatos de imagen médica (DICOM, NIfTI)
- Diseño orientado a objetos siguiendo mejores prácticas

Autor: Equipo de Investigación Médica
Versión: 1.0.0
Licencia: MIT
"""

__version__ = "1.0.0"
__author__ = "Equipo de Investigación Médica"
__email__ = "research@medical.edu"

from .models.medical_image import MedicalImage
from .models.metadata import ImageMetadata
from .services.image_manager import ImageManager
from .services.data_loader import DataLoader

__all__ = [
    "MedicalImage",
    "ImageMetadata", 
    "ImageManager",
    "DataLoader"
]