"""
Suite de Pruebas para Trabajo Final Grup4
===============================================

Este módulo contiene pruebas unitarias 

Cobertura de Pruebas:
- Funcionalidad de la clase MedicalImage
- Manejo de ImageMetadata
- Operaciones de ImageManager
- Funcionalidad de DataLoader
- Utilidades de manejo de archivos
- Validación de datos
"""

import unittest
import tempfile
import os
import numpy as np
from datetime import datetime

# Importar módulos a probar
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from medical_image_manager.models.medical_image import MedicalImage
from medical_image_manager.models.metadata import ImageMetadata
from medical_image_manager.services.image_manager import ImageManager
from medical_image_manager.services.data_loader import DataLoader
from medical_image_manager.utils.file_handler import FileHandler
from medical_image_manager.utils.validators import DataValidator


class TestMedicalImage(unittest.TestCase):
    """Casos de prueba para la clase MedicalImage."""
    
    def setUp(self):
        """Configurar elementos de prueba."""
        self.test_image = MedicalImage(
            filename="test_image.nii",
            pixel_data=np.random.rand(64, 64, 32),
            metadata={"modality": "MRI", "patient_id": "12345"},
            format_type="NIfTI"
        )
    
    def test_image_creation(self):
        """Test basic image creation."""
        self.assertIsNotNone(self.test_image.image_id)
        self.assertEqual(self.test_image.filename, "test_image.nii")
        self.assertEqual(self.test_image.format_type, "NIfTI")
        self.assertIsInstance(self.test_image.creation_date, datetime)
    
    def test_metadata_operations(self):
        """Test metadata manipulation."""
        # Test getting metadata
        self.assertEqual(self.test_image.get_metadata("modality"), "MRI")
        
        # Test updating metadata
        self.test_image.update_metadata("slice_thickness", 1.5)
        self.assertEqual(self.test_image.get_metadata("slice_thickness"), 1.5)
        
        # Test removing metadata
        success = self.test_image.remove_metadata("patient_id")
        self.assertTrue(success)
        self.assertIsNone(self.test_image.get_metadata("patient_id"))
    
    def test_image_info(self):
        """Test image information retrieval."""
        info = self.test_image.get_image_info()
        
        self.assertIn("image_id", info)
        self.assertIn("filename", info)
        self.assertIn("format_type", info)
        self.assertIn("has_pixel_data", info)
        self.assertTrue(info["has_pixel_data"])
    
    def test_validation(self):
        """Test image validation."""
        self.assertTrue(self.test_image.validate_data())
        
        # Test with invalid data
        invalid_image = MedicalImage(filename="")
        self.assertFalse(invalid_image.validate_data())


class TestImageMetadata(unittest.TestCase):
    """Test cases for ImageMetadata class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.metadata = ImageMetadata()
    
    def test_patient_info_update(self):
        """Test patient information updates."""
        self.metadata.update_patient_info(
            patient_id="12345",
            patient_name="John Doe",
            patient_age=45
        )
        
        self.assertEqual(self.metadata.patient_info.patient_id, "12345")
        self.assertEqual(self.metadata.patient_info.patient_name, "John Doe")
        self.assertEqual(self.metadata.patient_info.patient_age, 45)
    
    def test_study_info_update(self):
        """Test study information updates."""
        self.metadata.update_study_info(
            modality="CT",
            study_description="Chest CT"
        )
        
        self.assertEqual(self.metadata.study_info.modality, "CT")
        self.assertEqual(self.metadata.study_info.study_description, "Chest CT")
    
    def test_custom_fields(self):
        """Test custom field operations."""
        self.metadata.add_custom_field("custom_field", "custom_value")
        self.assertEqual(self.metadata.custom_fields["custom_field"], "custom_value")
        
        success = self.metadata.remove_custom_field("custom_field")
        self.assertTrue(success)
        self.assertNotIn("custom_field", self.metadata.custom_fields)
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        self.metadata.update_patient_info(patient_id="12345")
        self.metadata.add_custom_field("test", "value")
        
        json_str = self.metadata.to_json()
        self.assertIsInstance(json_str, str)
        
        loaded_metadata = ImageMetadata.from_json(json_str)
        self.assertEqual(loaded_metadata.patient_info.patient_id, "12345")
        self.assertEqual(loaded_metadata.custom_fields["test"], "value")


class TestImageManager(unittest.TestCase):
    """Test cases for ImageManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.image_manager = ImageManager(storage_path=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_manager_initialization(self):
        """Test image manager initialization."""
        self.assertIsInstance(self.image_manager.images, dict)
        self.assertEqual(len(self.image_manager.images), 0)
    
    def test_statistics(self):
        """Test statistics generation."""
        stats = self.image_manager.get_statistics()
        self.assertEqual(stats["total_images"], 0)
        
        # Add a mock image for testing
        test_image = MedicalImage(
            filename="test.nii",
            format_type="NIfTI"
        )
        self.image_manager.images[test_image.image_id] = test_image
        
        stats = self.image_manager.get_statistics()
        self.assertEqual(stats["total_images"], 1)
        self.assertIn("NIfTI", stats["formats"])


class TestDataValidator(unittest.TestCase):
    """Test cases for DataValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
    
    def test_pixel_data_validation(self):
        """Test pixel data validation."""
        # Valid data
        valid_data = np.random.rand(64, 64, 32).astype(np.float32)
        self.assertTrue(self.validator.validate_pixel_data(valid_data))
        
        # Invalid data
        empty_data = np.array([])
        self.assertFalse(self.validator.validate_pixel_data(empty_data))
        
        # Data with NaN values
        nan_data = np.full((10, 10), np.nan)
        self.assertFalse(self.validator.validate_pixel_data(nan_data))
    
    def test_image_validation(self):
        """Test medical image validation."""
        # Valid image
        valid_image = MedicalImage(
            filename="test.nii",
            pixel_data=np.random.rand(64, 64, 32),
            format_type="NIfTI"
        )
        self.assertTrue(self.validator.validate_image(valid_image))
        
        # Invalid image (no filename)
        invalid_image = MedicalImage(filename="")
        self.assertFalse(self.validator.validate_image(invalid_image))
    
    def test_validation_rules(self):
        """Test validation rule management."""
        original_max_size = self.validator.validation_rules["max_file_size_mb"]
        
        # Update rule
        self.validator.set_validation_rule("max_file_size_mb", 500)
        self.assertEqual(self.validator.validation_rules["max_file_size_mb"], 500)
        
        # Get rules
        rules = self.validator.get_validation_rules()
        self.assertIsInstance(rules, dict)
        self.assertEqual(rules["max_file_size_mb"], 500)


class TestDataLoader(unittest.TestCase):
    """Test cases for DataLoader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_loader = DataLoader(download_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test data loader initialization."""
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertIsInstance(self.data_loader.file_handler, FileHandler)
    
    def test_sample_dataset_creation(self):
        """Test sample dataset creation."""
        try:
            import nibabel as nib
            
            sample_dir = os.path.join(self.temp_dir, "samples")
            sample_files = self.data_loader.create_sample_dataset(sample_dir, 3)
            
            self.assertEqual(len(sample_files), 3)
            for file_path in sample_files:
                self.assertTrue(os.path.exists(file_path))
                self.assertTrue(file_path.endswith('.nii.gz'))
                
        except ImportError:
            self.skipTest("nibabel not available for sample dataset creation")
    
    def test_directory_loading(self):
        """Test loading from directory."""
        # Create some test files
        test_files = ["test1.nii", "test2.dcm", "test3.txt"]
        for filename in test_files:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write("test content")
        
        # Load from directory
        image_files = self.data_loader.load_from_directory(self.temp_dir)
        
        # Should find .nii and .dcm files, but not .txt
        expected_files = 2
        self.assertEqual(len(image_files), expected_files)


class TestFileHandler(unittest.TestCase):
    """Test cases for FileHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.file_handler = FileHandler()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_format_detection(self):
        """Test file format detection."""
        test_cases = [
            ("test.nii", "NIfTI"),
            ("test.nii.gz", "NIfTI"),
            ("test.dcm", "DICOM"),
            ("test.png", "PNG"),
            ("unknown.xyz", "Unknown")
        ]
        
        for filename, expected_format in test_cases:
            detected_format = self.file_handler._detect_format(filename)
            self.assertEqual(detected_format, expected_format)
    
    def test_file_info(self):
        """Test file information retrieval."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.nii")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        file_info = self.file_handler.get_file_info(test_file)
        
        self.assertEqual(file_info["filename"], "test.nii")
        self.assertEqual(file_info["format_type"], "NIfTI")
        self.assertGreater(file_info["file_size"], 0)
    
    def test_file_validation(self):
        """Test file validation."""
        # Non-existent file
        self.assertFalse(self.file_handler.validate_file("nonexistent.nii"))
        
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("not an image")
        
        # This should return False for unsupported format
        self.assertFalse(self.file_handler.validate_file(test_file))


if __name__ == "__main__":
    # Configure test runner
    unittest.main(verbosity=2)