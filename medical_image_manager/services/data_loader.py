"""
Módulo de Servicio Cargador de Datos
====================================

Este módulo proporciona funcionalidad para cargar datos de imágenes médicas
desde varias fuentes, incluyendo el dataset de Zenodo.

Clases:
    DataLoader: Clase de servicio para cargar datos de imágenes médicas
"""

import os
import requests
import zipfile
import tempfile
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path

from ..models.medical_image import MedicalImage
from ..utils.file_handler import FileHandler


class DataLoader:
    """
    Clase de servicio para cargar datos de imágenes médicas desde varias fuentes.
    
    Esta clase maneja la descarga y carga de imágenes médicas desde fuentes remotas
    como Zenodo, así como la carga desde directorios locales.
    
    Atributos:
        file_handler (FileHandler): Manejador para operaciones de archivo
        logger (logging.Logger): Instancia del logger
        download_dir (str): Directorio para archivos descargados
    """
    
    def __init__(self, download_dir: str = "data/downloads"):
        """
        Inicializa el DataLoader.
        
        Args:
            download_dir (str): Directorio para almacenar archivos descargados
        """
        self.file_handler = FileHandler()
        self.logger = logging.getLogger(__name__)
        self.download_dir = download_dir
        
        # Asegurar que el directorio de descarga existe
        os.makedirs(download_dir, exist_ok=True)
    
    def download_zenodo_dataset(
        self,
        record_id: str = "7105232",
        extract: bool = True
    ) -> str:
        """
        Download dataset from Zenodo.
        
        Args:
            record_id (str): Zenodo record ID
            extract (bool): Whether to extract downloaded archives
            
        Returns:
            str: Path to downloaded/extracted data
            
        Raises:
            requests.RequestException: If download fails
        """
        zenodo_url = f"https://zenodo.org/api/records/{record_id}"
        
        try:
            # Get record information
            self.logger.info(f"Fetching Zenodo record information: {record_id}")
            response = requests.get(zenodo_url)
            response.raise_for_status()
            
            record_data = response.json()
            files = record_data.get('files', [])
            
            if not files:
                raise ValueError("No files found in Zenodo record")
            
            # Download files
            download_path = os.path.join(self.download_dir, f"zenodo_{record_id}")
            os.makedirs(download_path, exist_ok=True)
            
            downloaded_files = []
            for file_info in files:
                file_url = file_info['links']['self']
                filename = file_info['key']
                file_path = os.path.join(download_path, filename)
                
                self.logger.info(f"Downloading: {filename}")
                self._download_file(file_url, file_path)
                downloaded_files.append(file_path)
                
                # Extract if it's an archive
                if extract and filename.endswith(('.zip', '.tar.gz', '.tar')):
                    self._extract_archive(file_path, download_path)
            
            self.logger.info(f"Dataset downloaded to: {download_path}")
            return download_path
            
        except Exception as e:
            self.logger.error(f"Failed to download Zenodo dataset: {e}")
            raise
    
    def load_from_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        supported_formats: Optional[List[str]] = None
    ) -> List[str]:
        """
        Load image files from a directory.
        
        Args:
            directory_path (str): Path to directory containing images
            recursive (bool): Whether to search subdirectories
            supported_formats (Optional[List[str]]): List of supported file extensions
            
        Returns:
            List[str]: List of image file paths
        """
        if supported_formats is None:
            supported_formats = ['.dcm', '.nii', '.nii.gz', '.img', '.hdr']
        
        image_files = []
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            self.logger.warning(f"Directory does not exist: {directory_path}")
            return image_files
        
        # Search for image files
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for file_path in directory_path.glob(pattern):
            if file_path.is_file():
                # Check if file extension is supported
                for ext in supported_formats:
                    if file_path.name.lower().endswith(ext.lower()):
                        image_files.append(str(file_path))
                        break
        
        self.logger.info(f"Found {len(image_files)} image files in {directory_path}")
        return image_files
    
    def load_dicom_series(
        self,
        series_directory: str
    ) -> List[str]:
        """
        Load DICOM series from a directory.
        
        Args:
            series_directory (str): Directory containing DICOM series
            
        Returns:
            List[str]: List of DICOM file paths in series order
        """
        dicom_files = []
        
        try:
            import pydicom
            
            # Find all DICOM files
            for root, dirs, files in os.walk(series_directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # Try to read as DICOM
                        pydicom.dcmread(file_path, stop_before_pixels=True)
                        dicom_files.append(file_path)
                    except:
                        # Not a DICOM file, skip
                        continue
            
            # Sort DICOM files by instance number if available
            def get_instance_number(file_path):
                try:
                    ds = pydicom.dcmread(file_path, stop_before_pixels=True)
                    return getattr(ds, 'InstanceNumber', 0)
                except:
                    return 0
            
            dicom_files.sort(key=get_instance_number)
            
        except ImportError:
            self.logger.warning("pydicom not available, using file-based discovery")
            # Fallback to file extension search
            dicom_files = self.load_from_directory(
                series_directory, 
                recursive=True, 
                supported_formats=['.dcm', '.dicom']
            )
        
        return dicom_files
    
    def validate_dataset(
        self,
        file_paths: List[str]
    ) -> Dict[str, Any]:
        """
        Validate a dataset of medical images.
        
        Args:
            file_paths (List[str]): List of image file paths
            
        Returns:
            Dict[str, Any]: Validation results
        """
        results = {
            "total_files": len(file_paths),
            "valid_files": 0,
            "invalid_files": 0,
            "formats": {},
            "errors": []
        }
        
        for file_path in file_paths:
            try:
                # Try to load image metadata
                _, metadata, format_type = self.file_handler.load_image(
                    file_path, load_pixel_data=False
                )
                
                results["valid_files"] += 1
                results["formats"][format_type] = results["formats"].get(format_type, 0) + 1
                
            except Exception as e:
                results["invalid_files"] += 1
                results["errors"].append(f"{file_path}: {str(e)}")
        
        return results
    
    def create_sample_dataset(
        self,
        output_dir: str,
        num_samples: int = 10
    ) -> List[str]:
        """
        Create a sample dataset for testing purposes.
        
        Args:
            output_dir (str): Output directory for sample files
            num_samples (int): Number of sample files to create
            
        Returns:
            List[str]: List of created sample file paths
        """
        import numpy as np
        
        os.makedirs(output_dir, exist_ok=True)
        sample_files = []
        
        for i in range(num_samples):
            # Create synthetic 3D image data
            image_data = np.random.randint(0, 4096, size=(64, 64, 32), dtype=np.uint16)
            
            # Save as NIfTI format (requires nibabel)
            try:
                import nibabel as nib
                
                # Create NIfTI image
                nii_img = nib.Nifti1Image(image_data, affine=np.eye(4))
                
                # Save to file
                filename = f"sample_{i:03d}.nii.gz"
                file_path = os.path.join(output_dir, filename)
                nib.save(nii_img, file_path)
                
                sample_files.append(file_path)
                
            except ImportError:
                self.logger.warning("nibabel not available, skipping NIfTI sample creation")
                break
        
        self.logger.info(f"Created {len(sample_files)} sample files in {output_dir}")
        return sample_files
    
    def _download_file(self, url: str, file_path: str) -> None:
        """
        Download a file from URL to local path.
        
        Args:
            url (str): URL to download from
            file_path (str): Local path to save file
        """
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # Simple progress indication
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        if downloaded_size % (1024 * 1024) == 0:  # Every MB
                            self.logger.info(f"Download progress: {progress:.1f}%")
    
    def _extract_archive(self, archive_path: str, extract_dir: str) -> None:
        """
        Extract an archive file.
        
        Args:
            archive_path (str): Path to archive file
            extract_dir (str): Directory to extract to
        """
        try:
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif archive_path.endswith(('.tar.gz', '.tar')):
                import tarfile
                with tarfile.open(archive_path, 'r') as tar_ref:
                    tar_ref.extractall(extract_dir)
            
            self.logger.info(f"Extracted: {archive_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to extract {archive_path}: {e}")
    
    def get_download_info(self, record_id: str = "7105232") -> Dict[str, Any]:
        """
        Get information about a Zenodo dataset without downloading.
        
        Args:
            record_id (str): Zenodo record ID
            
        Returns:
            Dict[str, Any]: Dataset information
        """
        zenodo_url = f"https://zenodo.org/api/records/{record_id}"
        
        try:
            response = requests.get(zenodo_url)
            response.raise_for_status()
            
            record_data = response.json()
            
            info = {
                "record_id": record_id,
                "title": record_data.get('metadata', {}).get('title', 'Unknown'),
                "description": record_data.get('metadata', {}).get('description', ''),
                "publication_date": record_data.get('metadata', {}).get('publication_date', ''),
                "files": []
            }
            
            for file_info in record_data.get('files', []):
                info["files"].append({
                    "filename": file_info['key'],
                    "size": file_info['size'],
                    "checksum": file_info.get('checksum', '')
                })
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get dataset info: {e}")
            return {"error": str(e)}