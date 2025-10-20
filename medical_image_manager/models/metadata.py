"""
Módulo de Modelo de Metadatos
============================

Este módulo define clases para el manejo de metadatos de imágenes médicas.

Clases:
    ImageMetadata: Clase para gestión estructurada de metadatos
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import json


@dataclass
class PatientInfo:
    """Estructura de información del paciente para imágenes médicas."""
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_sex: Optional[str] = None
    patient_birth_date: Optional[str] = None


@dataclass
class StudyInfo:
    """Estructura de información del estudio para imágenes médicas."""
    study_id: Optional[str] = None
    study_date: Optional[str] = None
    study_time: Optional[str] = None
    study_description: Optional[str] = None
    modality: Optional[str] = None
    institution_name: Optional[str] = None


@dataclass
class ImageMetadata:
    """
    Metadatos estructurados para imágenes médicas.
    
    Esta clase proporciona una manera estandarizada de manejar metadatos de imágenes médicas
    con capacidades de validación y serialización.
    
    Atributos:
        patient_info (PatientInfo): Información relacionada con el paciente
        study_info (StudyInfo): Información relacionada con el estudio
        image_info (Dict[str, Any]): Metadatos específicos de la imagen
        custom_fields (Dict[str, Any]): Campos de metadatos definidos por el usuario
        created_at (datetime): Cuándo se crearon los metadatos
        updated_at (datetime): Cuándo se actualizaron por última vez los metadatos
    """
    
    patient_info: PatientInfo = field(default_factory=PatientInfo)
    study_info: StudyInfo = field(default_factory=StudyInfo)
    image_info: Dict[str, Any] = field(default_factory=dict)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_patient_info(self, **kwargs) -> None:
        """
        Actualiza la información del paciente.
        
        Args:
            **kwargs: Campos de información del paciente a actualizar
        """
        for key, value in kwargs.items():
            if hasattr(self.patient_info, key):
                setattr(self.patient_info, key, value)
        self.updated_at = datetime.now()
    
    def update_study_info(self, **kwargs) -> None:
        """
        Actualiza la información del estudio.
        
        Args:
            **kwargs: Campos de información del estudio a actualizar
        """
        for key, value in kwargs.items():
            if hasattr(self.study_info, key):
                setattr(self.study_info, key, value)
        self.updated_at = datetime.now()
    
    def update_image_info(self, key: str, value: Any) -> None:
        """
        Actualiza información específica de la imagen.
        
        Args:
            key (str): Nombre del campo
            value (Any): Valor del campo
        """
        self.image_info[key] = value
        self.updated_at = datetime.now()
    
    def add_custom_field(self, key: str, value: Any) -> None:
        """
        Añade un campo de metadatos personalizado.
        
        Args:
            key (str): Nombre del campo
            value (Any): Valor del campo
        """
        self.custom_fields[key] = value
        self.updated_at = datetime.now()
    
    def remove_custom_field(self, key: str) -> bool:
        """
        Elimina un campo de metadatos personalizado.
        
        Args:
            key (str): Nombre del campo a eliminar
            
        Returns:
            bool: True si el campo fue eliminado, False si no existía
        """
        if key in self.custom_fields:
            del self.custom_fields[key]
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_all_metadata(self) -> Dict[str, Any]:
        """
        Obtiene todos los metadatos como un diccionario.
        
        Returns:
            Dict[str, Any]: Diccionario completo de metadatos
        """
        return {
            "patient_info": self.patient_info.__dict__,
            "study_info": self.study_info.__dict__,
            "image_info": self.image_info,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def search_metadata(self, query: str) -> List[tuple]:
        """
        Busca campos de metadatos que contengan una cadena de consulta.
        
        Args:
            query (str): Consulta de búsqueda
            
        Returns:
            List[tuple]: Lista de tuplas (ruta_campo, valor) que coinciden con la consulta
        """
        results = []
        all_metadata = self.get_all_metadata()
        
        def search_recursive(data: Any, path: str = "") -> None:
            if isinstance(data, dict):
                for key, value in data.items():
                    new_path = f"{path}.{key}" if path else key
                    if query.lower() in str(value).lower():
                        results.append((new_path, value))
                    search_recursive(value, new_path)
            elif isinstance(data, (list, tuple)):
                for i, item in enumerate(data):
                    new_path = f"{path}[{i}]"
                    search_recursive(item, new_path)
            elif query.lower() in str(data).lower():
                results.append((path, data))
        
        search_recursive(all_metadata)
        return results
    
    def validate_metadata(self) -> List[str]:
        """
        Valida la integridad y completitud de los metadatos.
        
        Returns:
            List[str]: Lista de mensajes de error de validación
        """
        errors = []
        
        # Verificar información requerida del paciente
        if not self.patient_info.patient_id:
            errors.append("El ID del paciente es requerido")
        
        # Verificar modalidad válida
        valid_modalities = ['CT', 'MRI', 'PET', 'SPECT', 'US', 'XR', 'MG', 'DX']
        if (self.study_info.modality and 
            self.study_info.modality not in valid_modalities):
            errors.append(f"Modalidad inválida: {self.study_info.modality}")
        
        # Verificar formatos de fecha
        if self.patient_info.patient_birth_date:
            try:
                datetime.strptime(self.patient_info.patient_birth_date, '%Y-%m-%d')
            except ValueError:
                errors.append("La fecha de nacimiento del paciente debe estar en formato YYYY-MM-DD")
        
        return errors
    
    def to_json(self) -> str:
        """
        Serializa los metadatos a cadena JSON.
        
        Returns:
            str: Representación JSON de los metadatos
        """
        return json.dumps(self.get_all_metadata(), indent=2, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ImageMetadata':
        """
        Crea una instancia de ImageMetadata desde una cadena JSON.
        
        Args:
            json_str (str): Cadena JSON que contiene metadatos
            
        Returns:
            ImageMetadata: Nueva instancia con metadatos cargados
        """
        data = json.loads(json_str)
        
        metadata = cls()
        
        # Cargar información del paciente
        if 'patient_info' in data:
            for key, value in data['patient_info'].items():
                if hasattr(metadata.patient_info, key):
                    setattr(metadata.patient_info, key, value)
        
        # Cargar información del estudio
        if 'study_info' in data:
            for key, value in data['study_info'].items():
                if hasattr(metadata.study_info, key):
                    setattr(metadata.study_info, key, value)
        
        # Cargar información de imagen y campos personalizados
        metadata.image_info = data.get('image_info', {})
        metadata.custom_fields = data.get('custom_fields', {})
        
        # Cargar marcas de tiempo
        if 'created_at' in data:
            metadata.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            metadata.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return metadata
    
    def __str__(self) -> str:
        """Representación en cadena de ImageMetadata."""
        patient_id = self.patient_info.patient_id or "Unknown"
        modality = self.study_info.modality or "Unknown"
        return f"ImageMetadata(Patient: {patient_id}, Modality: {modality})"