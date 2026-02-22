import os
import shutil
import glob
from pathlib import Path

def main():
    root_dir = Path(".")
    archive_dir = Path("archive/legacy_root_2026")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Exact files or wildcards to move
    patterns_to_move = [
        # Markdown docs at root
        "BUILD_PIPELINE.md", "CONSTITUTION.md", "DELIVERABLES.md", 
        "PHASE_*_SUMMARY.md", "PLAN.md", "QUICK_START.md", 
        "SESSION_*_DIRECTIVE.md", "SESSION_*_SUMMARY.md", "SESSION_SUMMARY.md", 
        "SPEC.md", "py_inventory.md",
        
        # Batch and Powershell
        "*.bat", "*.ps1",
        
        # Logs and Outputs
        "*.txt", "*.log",
        
        # Old Python Scripts
        "run_auto_battle.py", "run_demo.py", "run_overworld.py", 
        "run_territorial_grid.py", "start_visual_demo.py", 
        "cleanup_tests.py", "archive_docs.py", "run_last_appointment.py",
        
        # Other stragglers
        "THREE_TIER_PRODUCTION_VALIDATION_REPORT.json"
    ]
    
    # Files to explicitly KEEP
    keep_files = {
        "README.md", "CONTRIBUTING.md", "LICENSE", "game.py", 
        "pyproject.toml", "requirements.txt", "uv.lock", 
        "demos.json", "MANIFEST.json"
    }

    files_moved = 0
    for pattern in patterns_to_move:
        # Avoid directories, only files
        for match in glob.glob(pattern):
            path = Path(match)
            if path.is_file() and path.name not in keep_files:
                dest = archive_dir / path.name
                shutil.move(str(path), str(dest))
                print(f"Archived: {path.name}")
                files_moved += 1
                
    print(f"Total files archived to {archive_dir}: {files_moved}")

if __name__ == "__main__":
    main()
