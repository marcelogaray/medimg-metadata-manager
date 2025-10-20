"""
Módulo de Servicio Gestor de Imágenes
=====================================

Este módulo proporciona la clase de servicio principal para gestionar imágenes médicas
y sus metadatos, incluyendo operaciones de registro, modificación y eliminación.

Clases:
    ImageManager: Clase de servicio principal para operaciones de gestión de imágenes
"""

from typing import Dict, List, Optional, Any, Union
import os
import json
import pickle
from datetime import datetime
import logging

from ..models.medical_image import MedicalImage
from ..models.metadata import ImageMetadata
from ..utils.file_handler import FileHandler
from ..utils.validators import DataValidator


class ImageManager:
    """
    Clase de servicio principal para gestionar imágenes médicas y metadatos.
    
    Esta clase proporciona funcionalidad integral para la gestión de imágenes médicas
    incluyendo operaciones de registro, modificación, eliminación y persistencia.
    
    Atributos:
        images (Dict[str, MedicalImage]): Registro de imágenes gestionadas
        storage_path (str): Ruta para almacenamiento persistente
        file_handler (FileHandler): Manejador para operaciones de archivo
        validator (DataValidator): Utilidades de validación de datos
        logger (logging.Logger): Instancia del logger
    """
    
    def __init__(self, storage_path: str = "data/images"):
        """
        Inicializa el ImageManager.
        
        Args:
            storage_path (str): Ruta para almacenar datos de imagen y metadatos
        """
        self.images: Dict[str, MedicalImage] = {}
        self.storage_path: str = storage_path
        self.file_handler = FileHandler()
        self.validator = DataValidator()
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Asegurar que el directorio de almacenamiento existe
        os.makedirs(storage_path, exist_ok=True)
        
        # Cargar imágenes existentes desde el almacenamiento
        self._load_existing_images()
    
    def register_image(
        self,
        file_path: str,
        metadata: Optional[ImageMetadata] = None,
        load_pixel_data: bool = True
    ) -> str:
        """
        Registra una nueva imagen médica en el sistema.
        
        Args:
            file_path (str): Ruta al archivo de imagen
            metadata (Optional[ImageMetadata]): Metadatos de la imagen
            load_pixel_data (bool): Si cargar datos de píxeles en memoria
            
        Returns:
            str: ID único de imagen para la imagen registrada
            
        Raises:
            FileNotFoundError: Si el archivo de imagen no existe
            ValueError: Si el formato de imagen no es soportado
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        # Cargar datos de imagen
        pixel_data, file_metadata, format_type = self.file_handler.load_image(
            file_path, load_pixel_data
        )
        
        # Crear objeto de imagen médica
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        medical_image = MedicalImage(
            filename=filename,
            pixel_data=pixel_data if load_pixel_data else None,
            metadata=file_metadata,
            format_type=format_type,
            file_size=file_size
        )
        
        # Añadir metadatos estructurados si se proporcionan
        if metadata:
            medical_image.metadata['structured_metadata'] = metadata.get_all_metadata()
        
        # Validar datos de imagen
        if not self.validator.validate_image(medical_image):
            raise ValueError("Datos de imagen inválidos")
        
        # Almacenar imagen en registro
        self.images[medical_image.image_id] = medical_image
        
        # Persistir al almacenamiento
        self._save_image_metadata(medical_image)
        
        self.logger.info(f"Registered image: {medical_image.image_id} ({filename})")
        return medical_image.image_id
    
    def get_image(self, image_id: str) -> Optional[MedicalImage]:
        """
        Recupera una imagen médica por ID.
        
        Args:
            image_id (str): Identificador único de imagen
            
        Returns:
            Optional[MedicalImage]: La imagen médica o None si no se encuentra
        """
        return self.images.get(image_id)
    
    def update_image_metadata(
        self,
        image_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Actualiza metadatos para una imagen específica.
        
        Args:
            image_id (str): Identificador único de imagen
            metadata_updates (Dict[str, Any]): Campos de metadatos a actualizar
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        image = self.images.get(image_id)
        if not image:
            self.logger.warning(f"Image not found for update: {image_id}")
            return False
        
        # Actualizar metadatos
        for key, value in metadata_updates.items():
            image.update_metadata(key, value)
        
        # Persistir cambios
        self._save_image_metadata(image)
        
        self.logger.info(f"Updated metadata for image: {image_id}")
        return True
    
    def delete_image(self, image_id: str, delete_files: bool = False) -> bool:
        """
        Elimina una imagen del sistema.
        
        Args:
            image_id (str): Identificador único de imagen
            delete_files (bool): Si eliminar archivos asociados
            
        Returns:
            bool: True si la eliminación fue exitosa, False en caso contrario
        """
        image = self.images.get(image_id)
        if not image:
            self.logger.warning(f"Image not found for deletion: {image_id}")
            return False
        
        # Remover del registro
        del self.images[image_id]
        
        # Eliminar almacenamiento persistente
        metadata_file = os.path.join(self.storage_path, f"{image_id}_metadata.json")
        if os.path.exists(metadata_file):
            os.remove(metadata_file)
        
        if delete_files:
            # Eliminar archivos de imagen asociados si se solicita
            # Nota: Esto requeriría rastrear rutas de archivos originales
            pass
        
        self.logger.info(f"Deleted image: {image_id}")
        return True
    
    def search_images(
        self,
        query: str,
        search_fields: Optional[List[str]] = None
    ) -> List[MedicalImage]:
        """
        Busca imágenes basándose en el contenido de metadatos.
        
        Args:
            query (str): Cadena de consulta de búsqueda
            search_fields (Optional[List[str]]): Campos específicos para buscar
            
        Returns:
            List[MedicalImage]: Lista de imágenes que coinciden
        """
        matching_images = []
        query_lower = query.lower()
        
        for image in self.images.values():
            # Buscar en nombre de archivo
            if query_lower in image.filename.lower():
                matching_images.append(image)
                continue
            
            # Buscar en metadatos
            if search_fields:
                for field in search_fields:
                    value = image.get_metadata(field)
                    if value and query_lower in str(value).lower():
                        matching_images.append(image)
                        break
            else:
                # Search all metadata
                for value in image.metadata.values():
                    if query_lower in str(value).lower():
                        matching_images.append(image)
                        break
        
        return matching_images
    
    def list_images(
        self,
        format_filter: Optional[str] = None,
        sort_by: str = "creation_date"
    ) -> List[MedicalImage]:
        """
        List all registered images with optional filtering and sorting.
        
        Args:
            format_filter (Optional[str]): Filter by image format
            sort_by (str): Field to sort by
            
        Returns:
            List[MedicalImage]: List of images
        """
        images = list(self.images.values())
        
        # Apply format filter
        if format_filter:
            images = [img for img in images if img.format_type == format_filter]
        
        # Sort images
        if sort_by == "creation_date":
            images.sort(key=lambda x: x.creation_date)
        elif sort_by == "filename":
            images.sort(key=lambda x: x.filename)
        elif sort_by == "last_modified":
            images.sort(key=lambda x: x.last_modified)
        elif sort_by == "file_size":
            images.sort(key=lambda x: x.file_size or 0)
        
        return images
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about managed images.
        
        Returns:
            Dict[str, Any]: Dictionary containing various statistics
        """
        if not self.images:
            return {"total_images": 0}
        
        formats = {}
        total_size = 0
        with_pixel_data = 0
        
        for image in self.images.values():
            # Count formats
            formats[image.format_type] = formats.get(image.format_type, 0) + 1
            
            # Total file size
            if image.file_size:
                total_size += image.file_size
            
            # Images with pixel data
            if image.pixel_data is not None:
                with_pixel_data += 1
        
        return {
            "total_images": len(self.images),
            "formats": formats,
            "total_file_size_bytes": total_size,
            "images_with_pixel_data": with_pixel_data,
            "images_metadata_only": len(self.images) - with_pixel_data
        }
    
    def export_metadata(self, output_file: str, format_type: str = "json") -> bool:
        """
        Exporta todos los metadatos a un archivo.
        
        Args:
            output_file (str): Ruta del archivo de salida
            format_type (str): Formato de exportación ('json' o 'csv')
            
        Returns:
            bool: True si la exportación fue exitosa, False en caso contrario
        """
        try:
            if format_type.lower() == "json":
                metadata_list = []
                for image in self.images.values():
                    metadata_list.append({
                        "image_id": image.image_id,
                        "filename": image.filename,
                        "format_type": image.format_type,
                        "creation_date": image.creation_date.isoformat(),
                        "metadata": image.metadata
                    })
                
                with open(output_file, 'w') as f:
                    json.dump(metadata_list, f, indent=2, default=str)
            
            elif format_type.lower() == "csv":
                import csv
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Escribir encabezado
                    writer.writerow([
                        'image_id', 'filename', 'format_type', 
                        'creation_date', 'file_size', 'metadata_json'
                    ])
                    
                    # Escribir datos
                    for image in self.images.values():
                        writer.writerow([
                            image.image_id,
                            image.filename,
                            image.format_type,
                            image.creation_date.isoformat(),
                            image.file_size,
                            json.dumps(image.metadata)
                        ])
            
            self.logger.info(f"Exported metadata to: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export metadata: {e}")
            return False
    
    def _load_existing_images(self) -> None:
        """Carga imágenes existentes desde el almacenamiento persistente."""
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith('_metadata.json'):
                try:
                    metadata_file = os.path.join(self.storage_path, filename)
                    with open(metadata_file, 'r') as f:
                        data = json.load(f)
                    
                    # Reconstruir objeto de imagen médica
                    image = MedicalImage(
                        filename=data['filename'],
                        pixel_data=None,  # Datos de píxeles no almacenados en metadatos
                        metadata=data['metadata'],
                        format_type=data['format_type'],
                        file_size=data.get('file_size')
                    )
                    image.image_id = data['image_id']
                    image.creation_date = datetime.fromisoformat(data['creation_date'])
                    image.last_modified = datetime.fromisoformat(data['last_modified'])
                    
                    self.images[image.image_id] = image
                    
                except Exception as e:
                    self.logger.warning(f"Failed to load image metadata from {filename}: {e}")
    
    def _save_image_metadata(self, image: MedicalImage) -> None:
        """Guarda metadatos de imagen en almacenamiento persistente."""
        metadata_file = os.path.join(self.storage_path, f"{image.image_id}_metadata.json")
        
        data = {
            "image_id": image.image_id,
            "filename": image.filename,
            "format_type": image.format_type,
            "creation_date": image.creation_date.isoformat(),
            "last_modified": image.last_modified.isoformat(),
            "file_size": image.file_size,
            "metadata": image.metadata
        }
        
        try:
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save metadata for {image.image_id}: {e}")
    
    def __len__(self) -> int:
        """Return the number of managed images."""
        return len(self.images)
    
    def __contains__(self, image_id: str) -> bool:
        """Check if an image ID is managed by this instance."""
        return image_id in self.images