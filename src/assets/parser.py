"""
Asset Parser Component
ADR 086: The Fault-Tolerant Asset Pipeline

Text-to-Data component - Reads YAML files into dictionaries.
If one file fails, the parser just skips it and moves to the next.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

class AssetParser:
    """Isolated YAML loader with fault tolerance"""
    
    def __init__(self, assets_path: Path):
        self.assets_path = assets_path
        self.parsed_data: Dict[str, Dict] = {}
        self.failed_files: List[str] = []
    
    def load_all_assets(self) -> Dict[str, Dict]:
        """Load all YAML files in the assets directory"""
        logger.info(f"📄 AssetParser: Loading from {self.assets_path}")
        
        # Get all YAML files
        yaml_files = list(self.assets_path.glob("*.yaml"))
        logger.info(f"📁 Found {len(yaml_files)} YAML files: {[f.name for f in yaml_files]}")
        
        # Load each file separately with fault tolerance
        for yaml_file in yaml_files:
            try:
                data = self._load_single_file(yaml_file)
                if data:
                    file_type = yaml_file.stem
                    self.parsed_data[file_type] = data
                    logger.info(f"✅ Loaded {file_type} from {yaml_file.name}")
                else:
                    logger.warning(f"⚠️ Empty file: {yaml_file.name}")
                    
            except Exception as e:
                self.failed_files.append(yaml_file.name)
                logger.error(f"💥 Failed to load {yaml_file.name}: {e}")
                # Continue loading other files (fault tolerance)
        
        # Report results
        loaded_count = len(self.parsed_data)
        total_count = len(yaml_files)
        
        logger.info(f"📄 AssetParser Results: {loaded_count}/{total_count} files loaded")
        
        if self.failed_files:
            logger.warning(f"⚠️ Failed files: {self.failed_files}")
        
        return self.parsed_data
    
    def _load_single_file(self, yaml_file: Path) -> Optional[Dict]:
        """Load a single YAML file with error handling"""
        if not yaml_file.exists():
            raise FileNotFoundError(f"Asset file not found: {yaml_file}")
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                return {}
            
            if not isinstance(data, dict):
                logger.warning(f"⚠️ {yaml_file.name} does not contain a dictionary")
                return {}
            
            return data
            
        except yaml.YAMLError as e:
            logger.error(f"💥 YAML syntax error in {yaml_file.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"💥 Unexpected error loading {yaml_file.name}: {e}")
            raise
    
    def get_data(self, file_type: str) -> Dict:
        """Get parsed data for a specific file type"""
        return self.parsed_data.get(file_type, {})
    
    def has_file(self, file_type: str) -> bool:
        """Check if a file type was successfully loaded"""
        return file_type in self.parsed_data
    
    def get_loaded_files(self) -> List[str]:
        """Get list of successfully loaded file types"""
        return list(self.parsed_data.keys())
    
    def get_failed_files(self) -> List[str]:
        """Get list of files that failed to load"""
        return self.failed_files.copy()
    
    def validate_required_files(self, required_files: List[str]) -> bool:
        """Validate that required files were loaded"""
        missing_files = [f for f in required_files if not self.has_file(f)]
        
        if missing_files:
            logger.warning(f"⚠️ Missing required files: {missing_files}")
            return False
        
        logger.info("✅ All required files loaded")
        return True
