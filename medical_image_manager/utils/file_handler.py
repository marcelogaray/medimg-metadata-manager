"""
Módulo de Utilidad Manejador de Archivos
========================================

Este módulo proporciona utilidades para manejar varios formatos de archivos de imágenes médicas.

Clases:
    FileHandler: Clase principal para operaciones de archivos y manejo de formatos
"""

import os
import numpy as np
from typing import Tuple, Optional, Dict, Any, Union
import logging


class FileHandler:
    """
    Clase de utilidad para manejar archivos de imágenes médicas.
    
    Esta clase proporciona métodos para cargar y guardar imágenes médicas
    en varios formatos incluyendo DICOM, NIfTI, y otros.
    
    Atributos:
        logger (logging.Logger): Instancia del logger
        supported_formats (Dict[str, str]): Mapeo de extensiones de archivo a formatos
    """
    
    def __init__(self):
        """Inicializa el FileHandler."""
        self.logger = logging.getLogger(__name__)
        
        # Supported file formats
        self.supported_formats = {
            '.dcm': 'DICOM',
            '.dicom': 'DICOM',
            '.nii': 'NIfTI',
            '.nii.gz': 'NIfTI',
            '.img': 'ANALYZE',
            '.hdr': 'ANALYZE',
            '.png': 'PNG',
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.tiff': 'TIFF',
            '.tif': 'TIFF'
        }
    
    def load_image(
        self,
        file_path: str,
        load_pixel_data: bool = True
    ) -> Tuple[Optional[np.ndarray], Dict[str, Any], str]:
        """
        Load a medical image file.
        
        Args:
            file_path (str): Path to the image file
            load_pixel_data (bool): Whether to load pixel data
            
        Returns:
            Tuple[Optional[np.ndarray], Dict[str, Any], str]: 
                (pixel_data, metadata, format_type)
                
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If format is not supported
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file format
        format_type = self._detect_format(file_path)
        
        if format_type == 'DICOM':
            return self._load_dicom(file_path, load_pixel_data)
        elif format_type == 'NIfTI':
            return self._load_nifti(file_path, load_pixel_data)
        elif format_type == 'ANALYZE':
            return self._load_analyze(file_path, load_pixel_data)
        elif format_type in ['PNG', 'JPEG', 'TIFF']:
            return self._load_standard_image(file_path, load_pixel_data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def save_image(
        self,
        pixel_data: np.ndarray,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        format_type: Optional[str] = None
    ) -> bool:
        """
        Save image data to file.
        
        Args:
            pixel_data (np.ndarray): Image pixel data
            file_path (str): Output file path
            metadata (Optional[Dict[str, Any]]): Image metadata
            format_type (Optional[str]): Target format (auto-detected if None)
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            if format_type is None:
                format_type = self._detect_format(file_path)
            
            if format_type == 'NIfTI':
                return self._save_nifti(pixel_data, file_path, metadata)
            elif format_type in ['PNG', 'JPEG', 'TIFF']:
                return self._save_standard_image(pixel_data, file_path)
            else:
                self.logger.error(f"Saving not supported for format: {format_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to save image: {e}")
            return False
    
    def _detect_format(self, file_path: str) -> str:
        """
        Detect image format from file path.
        
        Args:
            file_path (str): Path to image file
            
        Returns:
            str: Detected format type
        """
        file_path_lower = file_path.lower()
        
        # Check for compound extensions first
        if file_path_lower.endswith('.nii.gz'):
            return 'NIfTI'
        
        # Check single extensions
        for ext, format_type in self.supported_formats.items():
            if file_path_lower.endswith(ext):
                return format_type
        
        # Try to detect DICOM files without extension
        try:
            import pydicom
            pydicom.dcmread(file_path, stop_before_pixels=True)
            return 'DICOM'
        except:
            pass
        
        return 'Unknown'
    
    def _load_dicom(
        self,
        file_path: str,
        load_pixel_data: bool
    ) -> Tuple[Optional[np.ndarray], Dict[str, Any], str]:
        """Load DICOM image file."""
        try:
            import pydicom
            
            # Read DICOM file
            if load_pixel_data:
                ds = pydicom.dcmread(file_path)
                pixel_data = ds.pixel_array if hasattr(ds, 'pixel_array') else None
            else:
                ds = pydicom.dcmread(file_path, stop_before_pixels=True)
                pixel_data = None
            
            # Extract metadata
            metadata = {}
            for elem in ds:
                if elem.VR != 'SQ':  # Skip sequence elements for simplicity
                    try:
                        key = f"{elem.tag}_{elem.keyword}" if elem.keyword else str(elem.tag)
                        metadata[key] = str(elem.value)
                    except:
                        continue
            
            return pixel_data, metadata, 'DICOM'
            
        except ImportError:
            self.logger.error("pydicom library not available")
            raise ValueError("DICOM support requires pydicom library")
        except Exception as e:
            self.logger.error(f"Failed to load DICOM file: {e}")
            raise
    
    def _load_nifti(
        self,
        file_path: str,
        load_pixel_data: bool
    ) -> Tuple[Optional[np.ndarray], Dict[str, Any], str]:
        """Load NIfTI image file."""
        try:
            import nibabel as nib
            
            # Load NIfTI image
            img = nib.load(file_path)
            
            # Get pixel data if requested
            pixel_data = img.get_fdata() if load_pixel_data else None
            
            # Extract header information as metadata
            header = img.header
            metadata = {}
            
            # Convert header fields to metadata
            for key in header.keys():
                try:
                    value = header[key]
                    if hasattr(value, 'tolist'):
                        value = value.tolist()
                    metadata[f"nifti_{key}"] = value
                except:
                    continue
            
            # Add affine matrix
            metadata['nifti_affine'] = img.affine.tolist()
            
            # Add basic image information
            metadata['nifti_shape'] = img.shape
            metadata['nifti_datatype'] = str(img.get_data_dtype())
            
            return pixel_data, metadata, 'NIfTI'
            
        except ImportError:
            self.logger.error("nibabel library not available")
            raise ValueError("NIfTI support requires nibabel library")
        except Exception as e:
            self.logger.error(f"Failed to load NIfTI file: {e}")
            raise
    
    def _load_analyze(
        self,
        file_path: str,
        load_pixel_data: bool
    ) -> Tuple[Optional[np.ndarray], Dict[str, Any], str]:
        """Load ANALYZE format image file."""
        try:
            import nibabel as nib
            
            # Load ANALYZE image
            img = nib.load(file_path)
            
            # Get pixel data if requested
            pixel_data = img.get_fdata() if load_pixel_data else None
            
            # Extract metadata
            metadata = {
                'analyze_shape': img.shape,
                'analyze_datatype': str(img.get_data_dtype()),
                'analyze_affine': img.affine.tolist()
            }
            
            return pixel_data, metadata, 'ANALYZE'
            
        except ImportError:
            self.logger.error("nibabel library not available")
            raise ValueError("ANALYZE support requires nibabel library")
        except Exception as e:
            self.logger.error(f"Failed to load ANALYZE file: {e}")
            raise
    
    def _load_standard_image(
        self,
        file_path: str,
        load_pixel_data: bool
    ) -> Tuple[Optional[np.ndarray], Dict[str, Any], str]:
        """Load standard image formats (PNG, JPEG, TIFF)."""
        try:
            import cv2
            
            if load_pixel_data:
                # Load image with OpenCV
                pixel_data = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
                if pixel_data is None:
                    raise ValueError("Failed to load image with OpenCV")
            else:
                pixel_data = None
            
            # Get basic file information
            metadata = {
                'file_size': os.path.getsize(file_path),
                'file_extension': os.path.splitext(file_path)[1]
            }
            
            if pixel_data is not None:
                metadata.update({
                    'image_shape': pixel_data.shape,
                    'image_dtype': str(pixel_data.dtype)
                })
            
            format_type = self._detect_format(file_path)
            return pixel_data, metadata, format_type
            
        except ImportError:
            self.logger.error("opencv-python library not available")
            raise ValueError("Standard image support requires opencv-python library")
        except Exception as e:
            self.logger.error(f"Failed to load image file: {e}")
            raise
    
    def _save_nifti(
        self,
        pixel_data: np.ndarray,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save image data as NIfTI format."""
        try:
            import nibabel as nib
            
            # Create affine matrix (identity if not provided)
            affine = np.eye(4)
            if metadata and 'nifti_affine' in metadata:
                affine = np.array(metadata['nifti_affine'])
            
            # Create NIfTI image
            nii_img = nib.Nifti1Image(pixel_data, affine)
            
            # Save to file
            nib.save(nii_img, file_path)
            
            self.logger.info(f"Saved NIfTI image: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save NIfTI image: {e}")
            return False
    
    def _save_standard_image(
        self,
        pixel_data: np.ndarray,
        file_path: str
    ) -> bool:
        """Save image data as standard format."""
        try:
            import cv2
            
            # Save image with OpenCV
            success = cv2.imwrite(file_path, pixel_data)
            
            if success:
                self.logger.info(f"Saved image: {file_path}")
                return True
            else:
                self.logger.error(f"Failed to save image: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to save image: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic file information.
        
        Args:
            file_path (str): Path to file
            
        Returns:
            Dict[str, Any]: File information
        """
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        stat = os.stat(file_path)
        
        return {
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "file_size": stat.st_size,
            "format_type": self._detect_format(file_path),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "extension": os.path.splitext(file_path)[1]
        }
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate if file can be loaded.
        
        Args:
            file_path (str): Path to file
            
        Returns:
            bool: True if file is valid, False otherwise
        """
        try:
            _, _, format_type = self.load_image(file_path, load_pixel_data=False)
            return format_type != 'Unknown'
        except:
            return False