"""
Trabajo Final Grupo 4 - Aplicación Principal
============================================

Esta aplicación trabaja con https://zenodo.org/records/7105232
Dataset OLIVES: Etiquetas Oftálmicas para Investigar Semántica Visual Ocular

Equipo 4
1 Eynar Pari
2
3
4
5
"""

import os
import sys
from typing import Optional, List
import logging

# Agregar el paquete al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medical_image_manager import ImageManager, DataLoader, MedicalImage, ImageMetadata
from medical_image_manager.utils.validators import DataValidator


class MedicalImageApp:
    """
    Aplicación de Gestión de Imágenes Médicas - Trabajo Final Grupo4
    
    Esta clase proporciona una interfaz basada en terminal para que los usuarios
    interactúen con la funcionalidad de gestión de imágenes médicas.
    """
    
    def __init__(self):
        """Inicializar la aplicación"""
        self.image_manager = ImageManager()
        self.data_loader = DataLoader()
        self.validator = DataValidator()
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        print("=" * 60)
        print("     Trabajo Final Grupo4")
        print("=" * 60)
    
    def run(self) -> None:
        """Ejecutar el bucle principal de la aplicación."""
        try:
            while True:
                self.display_main_menu()
                choice = input("\nSeleccione una opción (1-7): ").strip()
                
                if choice == '1':
                    self.register_image_menu()
                elif choice == '2':
                    self.view_images_menu()
                elif choice == '3':
                    self.modify_metadata_menu()
                elif choice == '4':
                    self.delete_image_menu()
                elif choice == '5':
                    self.search_images_menu()
                elif choice == '6':
                    self.load_dataset_menu()
                elif choice == '7':
                    print("\n¡ Gracias Magister !")
                    break
                else:
                    print("\nOpción inválida. Por favor intente de nuevo.")
                
                input("\nPresione Enter para continuar...")
                
        except KeyboardInterrupt:
            print("\n\nAplicación interrumpida por el usuario. ¡Hasta luego!")
        except Exception as e:
            self.logger.error(f"Error de aplicación: {e}")
            print(f"\nOcurrió un error: {e}")
    
    def display_main_menu(self) -> None:
        """Mostrar las opciones del menu principal."""
        print("\n" + "=" * 50)
        print("            MENÚ PRINCIPAL")
        print("=" * 50)
        print("1. Registrar Nueva Imagen")
        print("2. Ver Imágenes Registradas")
        print("3. Modificar Metadatos de Imagen")
        print("4. Eliminar Imagen")
        print(" extras ------")
        print("5. Buscar Imágenes")
        print("6. Cargar Dataset de Zenodo (descargar) ")
        print("7. Salir")
        print("=" * 50)
    
    def register_image_menu(self) -> None:
        """Manejar el registro de imágenes."""
        print("\n--- Registrar Nueva Imagen ---")
        
        file_path = input("Ingrese la ruta del archivo de imagen: ").strip()
        
        if not file_path:
            print("La ruta del archivo no puede estar vacía.")
            return
        
        if not os.path.exists(file_path):
            print(f"Archivo no encontrado: {file_path}")
            return
        
        try:
            # Preguntar si el usuario quiere agregar metadatos
            add_metadata = input("¿Agregar metadatos personalizados? (s/n): ").strip().lower() == 's'
            
            metadata = None
            if add_metadata:
                metadata = self.create_metadata_interactive()
            
            # Registrar la imagen
            load_pixels = input("¿Cargar datos de píxeles en memoria? (s/n): ").strip().lower() == 's'
            image_id = self.image_manager.register_image(
                file_path=file_path,
                metadata=metadata,
                load_pixel_data=load_pixels
            )
            
            print(f"\n¡Imagen registrada exitosamente!")
            print(f"ID de Imagen: {image_id}")
            
        except Exception as e:
            print(f"Error al registrar imagen: {e}")
    
    def view_images_menu(self) -> None:
        """Handle viewing registered images."""
        print("\n--- View Registered Images ---")
        
        images = self.image_manager.list_images()
        
        if not images:
            print("No images registered.")
            return
        
        print(f"\nFound {len(images)} registered images:\n")
        
        for i, image in enumerate(images, 1):
            print(f"{i}. {image.filename}")
            print(f"   ID: {image.image_id}")
            print(f"   Format: {image.format_type}")
            print(f"   Size: {image.file_size or 'Unknown'} bytes")
            print(f"   Created: {image.creation_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Has pixel data: {'Yes' if image.pixel_data is not None else 'No'}")
            print()
        
        # Ask if user wants to view details of a specific image
        view_details = input("View details of a specific image? (y/n): ").strip().lower() == 'y'
        
        if view_details:
            try:
                choice = int(input(f"Enter image number (1-{len(images)}): ")) - 1
                if 0 <= choice < len(images):
                    self.display_image_details(images[choice])
                else:
                    print("Invalid image number.")
            except ValueError:
                print("Please enter a valid number.")
    
    def display_image_details(self, image: MedicalImage) -> None:
        """Display detailed information about an image."""
        print(f"\n--- Image Details: {image.filename} ---")
        
        info = image.get_image_info()
        
        for key, value in info.items():
            if key != 'metadata_fields':
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Display metadata
        if image.metadata:
            print("\nMetadata:")
            for key, value in image.metadata.items():
                # Truncate long values
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:97] + "..."
                print(f"  {key}: {str_value}")
        
        # Validation status
        is_valid = self.validator.validate_image(image)
        print(f"\nValidation Status: {'✓ Valid' if is_valid else '✗ Invalid'}")
        
        if not is_valid:
            errors = self.validator.get_validation_errors(image)
            print("Validation Errors:")
            for error in errors:
                print(f"  - {error}")
    
    def modify_metadata_menu(self) -> None:
        """Handle metadata modification."""
        print("\n--- Modify Image Metadata ---")
        
        images = self.image_manager.list_images()
        if not images:
            print("No images registered.")
            return
        
        # Select image
        print("Select an image to modify:")
        for i, image in enumerate(images, 1):
            print(f"{i}. {image.filename} (ID: {image.image_id[:8]}...)")
        
        try:
            choice = int(input(f"Enter image number (1-{len(images)}): ")) - 1
            if not (0 <= choice < len(images)):
                print("Invalid image number.")
                return
            
            selected_image = images[choice]
            
            # Modification options
            print("\nModification options:")
            print("1. Add/Update metadata field")
            print("2. Remove metadata field")
            print("3. Bulk update from JSON")
            
            mod_choice = input("Select option (1-3): ").strip()
            
            if mod_choice == '1':
                key = input("Enter metadata key: ").strip()
                value = input("Enter metadata value: ").strip()
                
                # Try to convert to appropriate type
                try:
                    # Try int first
                    if value.isdigit():
                        value = int(value)
                    # Try float
                    elif '.' in value and value.replace('.', '').isdigit():
                        value = float(value)
                    # Keep as string otherwise
                except:
                    pass
                
                success = self.image_manager.update_image_metadata(
                    selected_image.image_id, {key: value}
                )
                
                if success:
                    print(f"Metadata updated: {key} = {value}")
                else:
                    print("Failed to update metadata.")
            
            elif mod_choice == '2':
                # Show existing metadata keys
                if selected_image.metadata:
                    print("\nExisting metadata keys:")
                    keys = list(selected_image.metadata.keys())
                    for i, key in enumerate(keys, 1):
                        print(f"{i}. {key}")
                    
                    try:
                        key_choice = int(input(f"Select key to remove (1-{len(keys)}): ")) - 1
                        if 0 <= key_choice < len(keys):
                            key_to_remove = keys[key_choice]
                            selected_image.remove_metadata(key_to_remove)
                            print(f"Removed metadata key: {key_to_remove}")
                        else:
                            print("Invalid key number.")
                    except ValueError:
                        print("Please enter a valid number.")
                else:
                    print("No metadata to remove.")
            
            elif mod_choice == '3':
                json_str = input("Enter JSON metadata (or file path): ").strip()
                
                if os.path.exists(json_str):
                    # Read from file
                    with open(json_str, 'r') as f:
                        json_str = f.read()
                
                try:
                    import json
                    metadata_dict = json.loads(json_str)
                    
                    success = self.image_manager.update_image_metadata(
                        selected_image.image_id, metadata_dict
                    )
                    
                    if success:
                        print("Metadata updated from JSON.")
                    else:
                        print("Failed to update metadata.")
                        
                except json.JSONDecodeError:
                    print("Invalid JSON format.")
            
        except ValueError:
            print("Please enter a valid number.")
        except Exception as e:
            print(f"Error modifying metadata: {e}")
    
    def delete_image_menu(self) -> None:
        """Handle image deletion."""
        print("\n--- Delete Image ---")
        
        images = self.image_manager.list_images()
        if not images:
            print("No images registered.")
            return
        
        # Select image to delete
        print("Select an image to delete:")
        for i, image in enumerate(images, 1):
            print(f"{i}. {image.filename} (ID: {image.image_id[:8]}...)")
        
        try:
            choice = int(input(f"Enter image number (1-{len(images)}): ")) - 1
            if not (0 <= choice < len(images)):
                print("Invalid image number.")
                return
            
            selected_image = images[choice]
            
            # Confirmation
            confirm = input(f"Delete '{selected_image.filename}'? (y/N): ").strip().lower()
            
            if confirm == 'y':
                success = self.image_manager.delete_image(selected_image.image_id)
                
                if success:
                    print("Image deleted successfully.")
                else:
                    print("Failed to delete image.")
            else:
                print("Deletion cancelled.")
                
        except ValueError:
            print("Please enter a valid number.")
        except Exception as e:
            print(f"Error deleting image: {e}")
    
    def search_images_menu(self) -> None:
        """Handle image searching."""
        print("\n--- Search Images ---")
        
        query = input("Enter search query: ").strip()
        
        if not query:
            print("Search query cannot be empty.")
            return
        
        # Search options
        print("\nSearch in:")
        print("1. All fields")
        print("2. Filename only")
        print("3. Specific metadata fields")
        
        search_choice = input("Select option (1-3): ").strip()
        
        search_fields = None
        if search_choice == '3':
            fields_input = input("Enter metadata field names (comma-separated): ").strip()
            search_fields = [field.strip() for field in fields_input.split(',')]
        elif search_choice == '2':
            search_fields = ['filename']
        
        try:
            results = self.image_manager.search_images(query, search_fields)
            
            if not results:
                print("No images found matching the query.")
                return
            
            print(f"\nFound {len(results)} matching images:")
            for i, image in enumerate(results, 1):
                print(f"{i}. {image.filename}")
                print(f"   ID: {image.image_id}")
                print(f"   Format: {image.format_type}")
                print()
            
        except Exception as e:
            print(f"Search error: {e}")
    
    def load_dataset_menu(self) -> None:
        """Handle dataset loading."""
        print("\n--- Load Dataset ---")
        print("1. Download Zenodo dataset")
        print("2. Load from local directory")
        print("3. Create sample dataset")
        
        choice = input("Select option (1-3): ").strip()
        
        try:
            if choice == '1':
                record_id = input("Enter Zenodo record ID (default: 7105232): ").strip()
                if not record_id:
                    record_id = "7105232"
                
                print("Downloading dataset... This may take a while.")
                dataset_path = self.data_loader.download_zenodo_dataset(record_id)
                
                # Ask if user wants to register images
                register = input("Register downloaded images? (y/n): ").strip().lower() == 'y'
                
                if register:
                    self.bulk_register_images(dataset_path)
                
            elif choice == '2':
                directory = input("Enter directory path: ").strip()
                
                if not os.path.exists(directory):
                    print(f"Directory not found: {directory}")
                    return
                
                image_files = self.data_loader.load_from_directory(directory)
                
                if not image_files:
                    print("No supported image files found.")
                    return
                
                print(f"Found {len(image_files)} image files.")
                register = input("Register all images? (y/n): ").strip().lower() == 'y'
                
                if register:
                    self.bulk_register_images(directory, image_files)
            
            elif choice == '3':
                output_dir = input("Enter output directory (default: data/samples): ").strip()
                if not output_dir:
                    output_dir = "data/samples"
                
                num_samples = input("Number of samples (default: 10): ").strip()
                try:
                    num_samples = int(num_samples) if num_samples else 10
                except ValueError:
                    num_samples = 10
                
                sample_files = self.data_loader.create_sample_dataset(output_dir, num_samples)
                
                if sample_files:
                    print(f"Created {len(sample_files)} sample files.")
                    register = input("Register sample images? (y/n): ").strip().lower() == 'y'
                    
                    if register:
                        self.bulk_register_images(output_dir, sample_files)
                
        except Exception as e:
            print(f"Dataset loading error: {e}")
    
    def bulk_register_images(
        self, 
        directory: str, 
        file_list: Optional[List[str]] = None
    ) -> None:
        """Register multiple images at once."""
        if file_list is None:
            file_list = self.data_loader.load_from_directory(directory)
        
        if not file_list:
            print("No files to register.")
            return
        
        print(f"\nRegistering {len(file_list)} images...")
        
        success_count = 0
        error_count = 0
        
        for i, file_path in enumerate(file_list, 1):
            try:
                print(f"Processing {i}/{len(file_list)}: {os.path.basename(file_path)}")
                
                image_id = self.image_manager.register_image(
                    file_path=file_path,
                    load_pixel_data=False  # Don't load pixel data for bulk operations
                )
                
                success_count += 1
                
            except Exception as e:
                print(f"  Error: {e}")
                error_count += 1
        
        print(f"\nBulk registration complete:")
        print(f"  Successfully registered: {success_count}")
        print(f"  Errors: {error_count}")
    
    def create_metadata_interactive(self) -> ImageMetadata:
        """Create metadata interactively."""
        metadata = ImageMetadata()
        
        print("\n--- Create Metadata ---")
        
        # Patient information
        patient_id = input("Patient ID: ").strip()
        if patient_id:
            metadata.update_patient_info(patient_id=patient_id)
        
        patient_name = input("Patient Name: ").strip()
        if patient_name:
            metadata.update_patient_info(patient_name=patient_name)
        
        # Study information
        modality = input("Modality (CT, MRI, PET, etc.): ").strip()
        if modality:
            metadata.update_study_info(modality=modality)
        
        study_desc = input("Study Description: ").strip()
        if study_desc:
            metadata.update_study_info(study_description=study_desc)
        
        # Custom fields
        while True:
            add_custom = input("Add custom field? (y/n): ").strip().lower()
            if add_custom != 'y':
                break
            
            key = input("Field name: ").strip()
            value = input("Field value: ").strip()
            
            if key and value:
                metadata.add_custom_field(key, value)
        
        return metadata


def main():
    """Punto de entrada principal."""
    app = MedicalImageApp()
    app.run()


if __name__ == "__main__":
    main()