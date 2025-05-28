#!/usr/bin/env python3
"""
Output Directory Manager for Environmental Screening

This module provides utilities for managing custom output directories
for environmental screening projects. It ensures all files for the same
screening subject are organized into a dedicated directory structure.

Features:
- Creates custom directories based on location name and timestamp
- Sanitizes directory names for filesystem compatibility
- Provides consistent directory structure for all screening outputs
- Handles both coordinate-based and cadastral-based screenings
- Manages subdirectories for different file types (reports, maps, logs)
"""

import os
import re
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

class OutputDirectoryManager:
    """Manages custom output directories for environmental screening projects"""
    
    def __init__(self, base_output_dir: str = "output"):
        """
        Initialize the directory manager
        
        Args:
            base_output_dir: Base directory for all outputs (default: "output")
        """
        self.base_output_dir = base_output_dir
        self.current_project_dir = None
        self.current_project_name = None
        
    def create_project_directory(
        self, 
        location_name: Optional[str] = None,
        coordinates: Optional[Tuple[float, float]] = None,
        cadastral_number: Optional[str] = None,
        custom_name: Optional[str] = None
    ) -> str:
        """
        Create a custom project directory for environmental screening
        
        Args:
            location_name: Descriptive location name (e.g., "Cataño, Puerto Rico")
            coordinates: Tuple of (longitude, latitude)
            cadastral_number: Cadastral number if applicable
            custom_name: Custom project name override (used exactly as provided)
            
        Returns:
            Path to the created project directory
        """
        
        # Generate project name
        if custom_name:
            # Use custom name exactly as provided - no sanitization or timestamp
            project_name = custom_name
            full_project_name = custom_name
        elif location_name:
            project_name = location_name
            # Sanitize project name for filesystem
            sanitized_name = self._sanitize_directory_name(project_name)
            # Add visually appealing timestamp to ensure uniqueness
            timestamp = datetime.now().strftime("%Y-%m-%d_at_%H.%M.%S")
            full_project_name = f"{sanitized_name}_{timestamp}"
        elif cadastral_number:
            project_name = f"Cadastral_{cadastral_number}"
            # Sanitize project name for filesystem
            sanitized_name = self._sanitize_directory_name(project_name)
            # Add visually appealing timestamp to ensure uniqueness
            timestamp = datetime.now().strftime("%Y-%m-%d_at_%H.%M.%S")
            full_project_name = f"{sanitized_name}_{timestamp}"
        elif coordinates:
            lon, lat = coordinates
            project_name = f"Coordinates_{lon:.6f}_{lat:.6f}"
            # Sanitize project name for filesystem
            sanitized_name = self._sanitize_directory_name(project_name)
            # Add visually appealing timestamp to ensure uniqueness
            timestamp = datetime.now().strftime("%Y-%m-%d_at_%H.%M.%S")
            full_project_name = f"{sanitized_name}_{timestamp}"
        else:
            project_name = "Environmental_Screening"
            # Sanitize project name for filesystem
            sanitized_name = self._sanitize_directory_name(project_name)
            # Add visually appealing timestamp to ensure uniqueness
            timestamp = datetime.now().strftime("%Y-%m-%d_at_%H.%M.%S")
            full_project_name = f"{sanitized_name}_{timestamp}"
        
        # Create full project directory path
        project_dir = os.path.join(self.base_output_dir, full_project_name)
        
        # Store current project info before creating directory structure
        self.current_project_dir = project_dir
        self.current_project_name = full_project_name
        
        # Create directory structure
        self._create_directory_structure(project_dir)
        
        print(f"📁 Created project directory: {project_dir}")
        return project_dir
    
    def get_subdirectory(self, subdir_type: str) -> str:
        """
        Get path to a specific subdirectory within the current project
        
        Args:
            subdir_type: Type of subdirectory ('reports', 'maps', 'logs', 'data')
            
        Returns:
            Path to the subdirectory
        """
        if not self.current_project_dir:
            raise ValueError("No project directory has been created. Call create_project_directory() first.")
        
        subdir_path = os.path.join(self.current_project_dir, subdir_type)
        os.makedirs(subdir_path, exist_ok=True)
        return subdir_path
    
    def get_file_path(self, filename: str, subdir_type: str = "reports") -> str:
        """
        Get full path for a file within the project directory structure
        
        Args:
            filename: Name of the file
            subdir_type: Subdirectory type ('reports', 'maps', 'logs', 'data')
            
        Returns:
            Full path to the file
        """
        subdir = self.get_subdirectory(subdir_type)
        return os.path.join(subdir, filename)
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Get information about the current project directory
        
        Returns:
            Dictionary with project information
        """
        if not self.current_project_dir:
            return {"error": "No project directory created"}
        
        return {
            "project_directory": self.current_project_dir,
            "project_name": self.current_project_name,
            "base_directory": self.base_output_dir,
            "subdirectories": {
                "reports": os.path.join(self.current_project_dir, "reports"),
                "maps": os.path.join(self.current_project_dir, "maps"),
                "logs": os.path.join(self.current_project_dir, "logs"),
                "data": os.path.join(self.current_project_dir, "data")
            },
            "created_time": datetime.now().isoformat()
        }
    
    def _sanitize_directory_name(self, name: str) -> str:
        """
        Sanitize a name for use as a directory name
        
        Args:
            name: Original name
            
        Returns:
            Sanitized name safe for filesystem use
        """
        # Remove or replace problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)  # Windows problematic chars
        sanitized = re.sub(r'[^\w\s\-_.]', '_', sanitized)  # Keep only alphanumeric, spaces, hyphens, underscores, dots
        sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscores
        sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple underscores with single
        sanitized = sanitized.strip('_.')  # Remove leading/trailing underscores and dots
        
        # Limit length
        if len(sanitized) > 50:
            sanitized = sanitized[:50].rstrip('_')
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "screening_project"
        
        return sanitized
    
    def _create_directory_structure(self, project_dir: str):
        """
        Create the standard directory structure for a screening project
        
        Args:
            project_dir: Path to the project directory
        """
        # Create main project directory
        os.makedirs(project_dir, exist_ok=True)
        
        # Create subdirectories
        subdirs = ["reports", "maps", "logs", "data"]
        for subdir in subdirs:
            subdir_path = os.path.join(project_dir, subdir)
            os.makedirs(subdir_path, exist_ok=True)
        
        # Create a project info file
        info_file = os.path.join(project_dir, "project_info.txt")
        with open(info_file, 'w') as f:
            f.write(f"Environmental Screening Project\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}\n")
            f.write(f"Project Directory: {project_dir}\n")
            f.write(f"Project Name: {self.current_project_name}\n\n")
            f.write(f"Directory Structure:\n")
            f.write(f"├── reports/     (PDF reports, comprehensive documents)\n")
            f.write(f"├── maps/        (Generated maps and visualizations)\n")
            f.write(f"├── logs/        (Analysis logs and raw data)\n")
            f.write(f"└── data/        (Structured data exports)\n")

# Global instance for easy access
_global_manager = None

def get_output_manager() -> OutputDirectoryManager:
    """Get the global output directory manager instance"""
    global _global_manager
    if _global_manager is None:
        _global_manager = OutputDirectoryManager()
    return _global_manager

def create_screening_directory(
    location_name: Optional[str] = None,
    coordinates: Optional[Tuple[float, float]] = None,
    cadastral_number: Optional[str] = None,
    custom_name: Optional[str] = None
) -> str:
    """
    Convenience function to create a screening project directory
    
    Args:
        location_name: Descriptive location name
        coordinates: Tuple of (longitude, latitude)
        cadastral_number: Cadastral number if applicable
        custom_name: Custom project name override (used exactly as provided)
        
    Returns:
        Path to the created project directory
    """
    manager = get_output_manager()
    return manager.create_project_directory(
        location_name=location_name,
        coordinates=coordinates,
        cadastral_number=cadastral_number,
        custom_name=custom_name
    )

def get_screening_file_path(filename: str, file_type: str = "reports") -> str:
    """
    Convenience function to get a file path within the current screening project
    
    Args:
        filename: Name of the file
        file_type: Type of file ('reports', 'maps', 'logs', 'data')
        
    Returns:
        Full path to the file
    """
    manager = get_output_manager()
    return manager.get_file_path(filename, file_type)

def get_current_project_info() -> Dict[str, Any]:
    """
    Convenience function to get current project information
    
    Returns:
        Dictionary with project information
    """
    manager = get_output_manager()
    return manager.get_project_info()

if __name__ == "__main__":
    print("📁 Output Directory Manager for Environmental Screening")
    print("=" * 60)
    
    # Example usage
    manager = OutputDirectoryManager()
    
    # Test with different scenarios
    print("\n🧪 Testing directory creation scenarios:")
    
    # Scenario 1: Location name
    print("\n1. Creating directory for location name...")
    dir1 = manager.create_project_directory(location_name="Cataño, Puerto Rico")
    print(f"   Created: {dir1}")
    
    # Scenario 2: Coordinates
    print("\n2. Creating directory for coordinates...")
    manager2 = OutputDirectoryManager()
    dir2 = manager2.create_project_directory(coordinates=(-66.150906, 18.434059))
    print(f"   Created: {dir2}")
    
    # Scenario 3: Cadastral number
    print("\n3. Creating directory for cadastral number...")
    manager3 = OutputDirectoryManager()
    dir3 = manager3.create_project_directory(cadastral_number="227-052-007-20")
    print(f"   Created: {dir3}")
    
    # Scenario 4: Custom name
    print("\n4. Creating directory with custom name...")
    manager4 = OutputDirectoryManager()
    dir4 = manager4.create_project_directory(custom_name="Miami Beach Environmental Assessment")
    print(f"   Created: {dir4}")
    
    # Test file path generation
    print("\n📄 Testing file path generation...")
    file_paths = {
        "flood_report": manager.get_file_path("comprehensive_flood_report.pdf", "reports"),
        "wetland_map": manager.get_file_path("wetland_analysis_map.pdf", "maps"),
        "analysis_log": manager.get_file_path("analysis_results.json", "logs"),
        "cadastral_data": manager.get_file_path("cadastral_info.json", "data")
    }
    
    for file_type, path in file_paths.items():
        print(f"   {file_type}: {path}")
    
    # Show project info
    print("\n📋 Project Information:")
    info = manager.get_project_info()
    for key, value in info.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for subkey, subvalue in value.items():
                print(f"     {subkey}: {subvalue}")
        else:
            print(f"   {key}: {value}")
    
    print("\n✅ Output Directory Manager testing completed!")
    print("📁 Check the 'output/' directory to see the created project structures.") 