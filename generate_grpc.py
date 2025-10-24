#!/usr/bin/env python3
"""
Generate Python gRPC stubs from .proto files
Run this after copying .proto files from rip-workcell
"""
import subprocess
import sys
import re
from pathlib import Path

def generate_stubs():
    """Generate Python gRPC stubs"""
    proto_dir = Path("proto")
    output_dir = Path("generated")
    
    if not proto_dir.exists():
        print("✗ proto/ directory not found")
        print("  Copy .proto files from rip-workcell to proto/ directory")
        return 1
    
    output_dir.mkdir(exist_ok=True)
    
    proto_files = list(proto_dir.glob("*.proto"))
    
    if not proto_files:
        print("✗ No .proto files found in proto/")
        return 1
    
    print(f"Found {len(proto_files)} .proto files:")
    for proto_file in proto_files:
        print(f"  - {proto_file.name}")
    
    print("\nGenerating Python stubs...")
    
    for proto_file in proto_files:
        cmd = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            str(proto_file)
        ]
        
        print(f"  Generating {proto_file.name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ Failed to generate stubs for {proto_file.name}")
            print(result.stderr)
            return 1
    
    # Fix imports in generated files
    print("\nFixing imports in generated files...")
    fix_imports(output_dir)
    
    print("\n✓ Successfully generated gRPC stubs")
    print(f"  Output directory: {output_dir.absolute()}")
    
    # Create __init__.py
    init_file = output_dir / "__init__.py"
    init_file.write_text('"""Generated gRPC stubs"""\n')
    
    return 0

def fix_imports(output_dir):
    """
    Fix import statements in ALL generated files (_pb2.py and _pb2_grpc.py)
    Changes absolute imports to relative imports:
    - import xxx_pb2 -> from . import xxx_pb2
    - import xxx_pb2 as yyy -> from . import xxx_pb2 as yyy
    """
    for py_file in output_dir.glob("*_pb2*.py"):
        print(f"  Fixing imports in {py_file.name}...")
        
        content = py_file.read_text(encoding='utf-8')
        original_content = content
        
        # Pattern 1: import xxx_pb2 as yyy
        pattern1 = r'^import (\w+_pb2(?:_grpc)?) as (.+)$'
        replacement1 = r'from . import \1 as \2'
        content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)
        
        # Pattern 2: import xxx_pb2
        pattern2 = r'^import (\w+_pb2(?:_grpc)?)$'
        replacement2 = r'from . import \1'
        content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)
        
        # Check if any changes were made
        if content != original_content:
            py_file.write_text(content, encoding='utf-8')
            print(f"    ✓ Fixed imports in {py_file.name}")
        else:
            print(f"    - No imports to fix in {py_file.name}")

if __name__ == "__main__":
    sys.exit(generate_stubs())