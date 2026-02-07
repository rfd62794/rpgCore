#!/usr/bin/env python3
"""
Rust Build Script for DGT Harvest Core
Python 3.12 compatible build system for high-performance image processing
"""

import subprocess
import sys
import os
from pathlib import Path
import shutil
from loguru import logger


def check_rust_toolchain():
    """Check if Rust toolchain is available"""
    try:
        result = subprocess.run(['rustc', '--version'], 
                              capture_output=True, text=True, check=True)
        logger.success(f"✅ Rust toolchain found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("❌ Rust toolchain not found")
        logger.error("Please install Rust from https://rustup.rs/")
        return False


def check_maturin():
    """Check if maturin is available"""
    try:
        result = subprocess.run(['maturin', '--version'], 
                              capture_output=True, text=True, check=True)
        logger.success(f"✅ Maturin found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("❌ Maturin not found")
        logger.error("Installing Maturin...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'maturin'], check=True)
            logger.success("✅ Maturin installed successfully")
            return True
        except subprocess.CalledProcessError:
            logger.error("❌ Failed to install Maturin")
            return False


def build_rust_module():
    """Build the Rust module using maturin"""
    rust_dir = Path('dgt_harvest_rust')
    
    if not rust_dir.exists():
        logger.error(f"❌ Rust directory not found: {rust_dir}")
        return False
    
    # Change to Rust directory
    original_cwd = Path.cwd()
    
    try:
        # Build with maturin
        logger.info("🔨 Building Rust harvest core...")
        
        # Use development mode for faster iteration
        result = subprocess.run([
            'maturin', 'build', '--release', '--target-dir', '..'
        ], cwd=rust_dir, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode == 0:
            logger.success("✅ Rust module built successfully")
            
            # Copy the built module to the parent directory
            target_dir = Path('..')
            wheel_files = list(target_dir.glob('dgt_harvest_rust*.whl'))
            
            if wheel_files:
                for wheel_file in wheel_files:
                    logger.info(f"📦 Found wheel: {wheel_file.name}")
            
            return True
        else:
            logger.error(f"❌ Build failed: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Build error: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir(original_cwd)


def install_rust_module():
    """Install the built Rust module"""
    target_dir = Path('..')
    wheel_files = list(target_dir.glob('dgt_harvest_rust*.whl'))
    
    if not wheel_files:
        logger.error("❌ No built wheel files found")
        return False
    
    try:
        # Install the wheel
        for wheel_file in wheel_files:
            logger.info(f"📦 Installing: {wheel_file.name}")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', str(wheel_file), '--force-reinstall'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.success(f"✅ Installed: {wheel_file.name}")
            else:
                logger.error(f"❌ Failed to install: {wheel_file.name}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Installation error: {e}")
        return False


def main():
    """Main build function"""
    logger.info("🦀 DGT Rust Build System")
    logger.info("=" * 50)
    
    # Check prerequisites
    if not check_rust_toolchain():
        logger.error("Please install Rust from https://rustup.rs/")
        return 1
    
    if not check_maturin():
        return 1
    
    # Build the module
    if not build_rust_module():
        return 1
    
    # Install the module
    if not install_rust_module():
        return 1
    
    logger.success("🚀 Rust module ready for use!")
    logger.info("🎯 The DGT Sheet-Cutter now has instant sub-millisecond sprite analysis!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
