"""
Módulo de Utilidad de Validadores de Datos
==========================================

Este módulo proporciona utilidades de validación para imágenes médicas y metadatos.

Clases:
    DataValidator: Clase principal para operaciones de validación de datos
"""

import numpy as np
from typing import Any, List, Dict, Optional
import logging

from ..models.medical_image import MedicalImage
from ..models.metadata import ImageMetadata


class DataValidator:
    """
    Clase de utilidad para validar datos de imágenes médicas y metadatos.
    
    Esta clase proporciona métodos de validación integrales para asegurar
    la integridad de datos y cumplimiento con estándares de imágenes médicas.
    
    Atributos:
        logger (logging.Logger): Instancia del logger
        validation_rules (Dict[str, Any]): Configuración para reglas de validación
    """
    
    def __init__(self):
        """Initialize the DataValidator."""
        self.logger = logging.getLogger(__name__)
        
        # Default validation rules
        self.validation_rules = {
            "max_file_size_mb": 1000,  # Maximum file size in MB
            "min_image_dimensions": (8, 8),  # Minimum image dimensions
            "max_image_dimensions": (4096, 4096, 4096),  # Maximum image dimensions
            "allowed_dtypes": [
                np.uint8, np.uint16, np.uint32,
                np.int8, np.int16, np.int32,
                np.float32, np.float64
            ],
            "required_metadata_fields": [],  # No required metadata fields by default
            "max_metadata_string_length": 1000
        }
    
    def validate_image(self, medical_image: MedicalImage) -> bool:
        """
        Validate a MedicalImage instance.
        
        Args:
            medical_image (MedicalImage): Image to validate
            
        Returns:
            bool: True if image is valid, False otherwise
        """
        try:
            errors = self.get_validation_errors(medical_image)
            if errors:
                for error in errors:
                    self.logger.warning(f"Validation error: {error}")
                return False
            return True
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return False
    
    def get_validation_errors(self, medical_image: MedicalImage) -> List[str]:
        """
        Get detailed validation errors for a medical image.
        
        Args:
            medical_image (MedicalImage): Image to validate
            
        Returns:
            List[str]: List of validation error messages
        """
        errors = []
        
        # Validate basic properties
        if not medical_image.filename:
            errors.append("Filename is required")
        
        if not medical_image.image_id:
            errors.append("Image ID is required")
        
        # Validate file size
        if medical_image.file_size:
            max_size_bytes = self.validation_rules["max_file_size_mb"] * 1024 * 1024
            if medical_image.file_size > max_size_bytes:
                errors.append(f"File size exceeds maximum ({medical_image.file_size} bytes)")
        
        # Validate pixel data if present
        if medical_image.pixel_data is not None:
            pixel_errors = self._validate_pixel_data(medical_image.pixel_data)
            errors.extend(pixel_errors)
        
        # Validate metadata
        metadata_errors = self._validate_metadata(medical_image.metadata)
        errors.extend(metadata_errors)
        
        return errors
    
    def validate_metadata(self, metadata: ImageMetadata) -> bool:
        """
        Validate ImageMetadata instance.
        
        Args:
            metadata (ImageMetadata): Metadata to validate
            
        Returns:
            bool: True if metadata is valid, False otherwise
        """
        try:
            errors = metadata.validate_metadata()
            if errors:
                for error in errors:
                    self.logger.warning(f"Metadata validation error: {error}")
                return False
            return True
            
        except Exception as e:
            self.logger.error(f"Metadata validation failed: {e}")
            return False
    
    def validate_pixel_data(self, pixel_data: np.ndarray) -> bool:
        """
        Validate pixel data array.
        
        Args:
            pixel_data (np.ndarray): Pixel data to validate
            
        Returns:
            bool: True if pixel data is valid, False otherwise
        """
        errors = self._validate_pixel_data(pixel_data)
        if errors:
            for error in errors:
                self.logger.warning(f"Pixel data validation error: {error}")
            return False
        return True
    
    def _validate_pixel_data(self, pixel_data: np.ndarray) -> List[str]:
        """
        Internal method to validate pixel data.
        
        Args:
            pixel_data (np.ndarray): Pixel data to validate
            
        Returns:
            List[str]: List of validation error messages
        """
        errors = []
        
        # Check if it's a numpy array
        if not isinstance(pixel_data, np.ndarray):
            errors.append("Pixel data must be a numpy array")
            return errors
        
        # Check array is not empty
        if pixel_data.size == 0:
            errors.append("Pixel data cannot be empty")
            return errors
        
        # Check dimensions
        min_dims = self.validation_rules["min_image_dimensions"]
        max_dims = self.validation_rules["max_image_dimensions"]
        
        if len(pixel_data.shape) < 2:
            errors.append("Image must have at least 2 dimensions")
        
        if len(pixel_data.shape) > len(max_dims):
            errors.append(f"Image has too many dimensions: {len(pixel_data.shape)}")
        
        # Check dimension sizes
        for i, dim_size in enumerate(pixel_data.shape):
            if i < len(min_dims) and dim_size < min_dims[i]:
                errors.append(f"Dimension {i} too small: {dim_size} < {min_dims[i]}")
            
            if i < len(max_dims) and dim_size > max_dims[i]:
                errors.append(f"Dimension {i} too large: {dim_size} > {max_dims[i]}")
        
        # Check data type
        allowed_dtypes = self.validation_rules["allowed_dtypes"]
        if pixel_data.dtype.type not in allowed_dtypes:
            errors.append(f"Unsupported data type: {pixel_data.dtype}")
        
        # Check for invalid values
        if np.any(np.isnan(pixel_data)):
            errors.append("Pixel data contains NaN values")
        
        if np.any(np.isinf(pixel_data)):
            errors.append("Pixel data contains infinite values")
        
        return errors
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Internal method to validate metadata dictionary.
        
        Args:
            metadata (Dict[str, Any]): Metadata to validate
            
        Returns:
            List[str]: List of validation error messages
        """
        errors = []
        
        # Check required fields
        required_fields = self.validation_rules["required_metadata_fields"]
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Required metadata field missing: {field}")
        
        # Check string length limits
        max_length = self.validation_rules["max_metadata_string_length"]
        for key, value in metadata.items():
            if isinstance(value, str) and len(value) > max_length:
                errors.append(f"Metadata field '{key}' exceeds maximum length: {len(value)}")
        
        return errors
    
    def validate_file_format(self, filename: str, expected_format: str) -> bool:
        """
        Validate file format matches expectation.
        
        Args:
            filename (str): Name of the file
            expected_format (str): Expected format (e.g., 'DICOM', 'NIfTI')
            
        Returns:
            bool: True if format matches, False otherwise
        """
        filename_lower = filename.lower()
        
        format_extensions = {
            'DICOM': ['.dcm', '.dicom'],
            'NIfTI': ['.nii', '.nii.gz'],
            'ANALYZE': ['.img', '.hdr'],
            'PNG': ['.png'],
            'JPEG': ['.jpg', '.jpeg'],
            'TIFF': ['.tiff', '.tif']
        }
        
        if expected_format not in format_extensions:
            self.logger.warning(f"Unknown format: {expected_format}")
            return False
        
        extensions = format_extensions[expected_format]
        for ext in extensions:
            if filename_lower.endswith(ext):
                return True
        
        return False
    
    def validate_dicom_compliance(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Validate DICOM compliance.
        
        Args:
            metadata (Dict[str, Any]): DICOM metadata
            
        Returns:
            List[str]: List of compliance issues
        """
        issues = []
        
        # Check for required DICOM tags
        required_tags = [
            'SOPInstanceUID',
            'StudyInstanceUID', 
            'SeriesInstanceUID',
            'Modality'
        ]
        
        for tag in required_tags:
            # Look for tag in various forms
            found = False
            for key in metadata.keys():
                if tag.lower() in key.lower():
                    found = True
                    break
            
            if not found:
                issues.append(f"Missing required DICOM tag: {tag}")
        
        # Check modality values
        modality_key = None
        for key in metadata.keys():
            if 'modality' in key.lower():
                modality_key = key
                break
        
        if modality_key:
            modality = metadata[modality_key]
            valid_modalities = [
                'CT', 'MR', 'PT', 'NM', 'US', 'XA', 'RF', 'DX', 'CR', 'MG'
            ]
            if modality not in valid_modalities:
                issues.append(f"Invalid DICOM modality: {modality}")
        
        return issues
    
    def validate_image_consistency(
        self,
        images: List[MedicalImage],
        check_dimensions: bool = True,
        check_modality: bool = True
    ) -> List[str]:
        """
        Validate consistency across multiple images.
        
        Args:
            images (List[MedicalImage]): List of images to check
            check_dimensions (bool): Whether to check dimension consistency
            check_modality (bool): Whether to check modality consistency
            
        Returns:
            List[str]: List of consistency issues
        """
        issues = []
        
        if len(images) < 2:
            return issues
        
        # Check dimensions consistency
        if check_dimensions:
            reference_shape = None
            for image in images:
                if image.pixel_data is not None:
                    if reference_shape is None:
                        reference_shape = image.pixel_data.shape
                    elif image.pixel_data.shape != reference_shape:
                        issues.append(
                            f"Inconsistent dimensions: {image.filename} "
                            f"has shape {image.pixel_data.shape}, "
                            f"expected {reference_shape}"
                        )
        
        # Check modality consistency
        if check_modality:
            modalities = set()
            for image in images:
                modality = None
                for key, value in image.metadata.items():
                    if 'modality' in key.lower():
                        modality = value
                        break
                
                if modality:
                    modalities.add(modality)
            
            if len(modalities) > 1:
                issues.append(f"Inconsistent modalities found: {modalities}")
        
        return issues
    
    def set_validation_rule(self, rule_name: str, value: Any) -> None:
        """
        Set a custom validation rule.
        
        Args:
            rule_name (str): Name of the rule
            value (Any): Rule value
        """
        self.validation_rules[rule_name] = value
        self.logger.info(f"Updated validation rule: {rule_name} = {value}")
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Get current validation rules.
        
        Returns:
            Dict[str, Any]: Current validation rules
        """
        return self.validation_rules.copy()