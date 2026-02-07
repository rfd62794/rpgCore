import yaml
from pathlib import Path

# Fix key assets with proper classifications
harvested_dir = Path('assets/harvested')

# Manual corrections for key assets
corrections = {
    'chest_0_0.yaml': {
        'object_type': 'entity',
        'collision': True,
        'tags': ['interactive', 'container', 'lootable', 'static', 'edge_cleaned', 'auto_detected']
    },
    'voyager_0_0.yaml': {
        'object_type': 'entity',
        'tags': ['interactive', 'player', 'character', 'edge_cleaned', 'auto_detected']
    },
    'tree_0_2.yaml': {
        'object_type': 'decoration',
        'tags': ['visual', 'ambient', 'organic', 'natural', 'tree', 'edge_cleaned', 'auto_detected']
    }
}

print('🔧 Applying manual corrections to key assets...')

for yaml_file, corrections_data in corrections.items():
    yaml_path = harvested_dir / yaml_file
    
    if yaml_path.exists():
        try:
            with open(yaml_path, 'r') as f:
                metadata = yaml.safe_load(f)
            
            # Apply corrections
            for key, value in corrections_data.items():
                metadata[key] = value
            
            # Update detection info
            metadata['detection_info']['detected_type'] = metadata['object_type']
            if metadata['object_type'] == 'entity' and 'chest' in yaml_file:
                metadata['detection_info']['is_chest'] = True
            
            # Save corrected metadata
            with open(yaml_path, 'w') as f:
                yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
            
            print(f'✅ Fixed {yaml_file}: {metadata["object_type"]}')
            
        except Exception as e:
            print(f'⚠️ Error fixing {yaml_file}: {e}')
    else:
        print(f'❌ File not found: {yaml_file}')

print('🎯 Manual corrections complete!')
