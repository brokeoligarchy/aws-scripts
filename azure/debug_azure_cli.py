#!/usr/bin/env python3
"""
Debug script to diagnose Azure CLI installation issues on Windows.
"""

import subprocess
import os
import sys
import platform

def check_system_info():
    """Print system information."""
    print("=== SYSTEM INFORMATION ===")
    print(f"Platform: {platform.platform()}")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print()

def check_path():
    """Check PATH environment variable."""
    print("=== PATH ENVIRONMENT VARIABLE ===")
    path = os.environ.get('PATH', '')
    path_dirs = path.split(os.pathsep)
    
    print(f"PATH contains {len(path_dirs)} directories:")
    for i, directory in enumerate(path_dirs, 1):
        print(f"  {i:2d}. {directory}")
    print()

def check_azure_cli_commands():
    """Check different ways to find Azure CLI."""
    print("=== AZURE CLI COMMAND CHECK ===")
    
    # Common Azure CLI command variations
    az_commands = [
        'az',
        'az.cmd', 
        'az.exe',
        r'C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd',
        r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd',
        r'C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft Azure CLI\az.cmd'
    ]
    
    for cmd in az_commands:
        print(f"Testing command: {cmd}")
        
        # Method 1: Direct subprocess call
        try:
            result = subprocess.run(
                [cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"  ✓ SUCCESS: {cmd} works with subprocess.run([cmd, '--version'])")
                print(f"    Output: {result.stdout.strip()}")
            else:
                print(f"  ✗ FAILED: {cmd} returned code {result.returncode}")
                print(f"    Error: {result.stderr.strip()}")
        except FileNotFoundError:
            print(f"  ✗ NOT FOUND: {cmd}")
        except subprocess.TimeoutExpired:
            print(f"  ✗ TIMEOUT: {cmd}")
        except Exception as e:
            print(f"  ✗ ERROR: {cmd} - {e}")
        
        # Method 2: Shell=True approach
        try:
            result = subprocess.run(
                f'{cmd} --version',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"  ✓ SUCCESS: {cmd} works with shell=True")
                print(f"    Output: {result.stdout.strip()}")
            else:
                print(f"  ✗ FAILED: {cmd} with shell=True returned code {result.returncode}")
                print(f"    Error: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"  ✗ TIMEOUT: {cmd} with shell=True")
        except Exception as e:
            print(f"  ✗ ERROR: {cmd} with shell=True - {e}")
        
        print()

def check_where_az():
    """Use 'where' command to find az."""
    print("=== USING 'WHERE' COMMAND ===")
    
    try:
        # On Windows, use 'where' to find az
        result = subprocess.run(
            'where az',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("Found az using 'where az':")
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"  {line.strip()}")
        else:
            print("'where az' command failed")
            print(f"Error: {result.stderr.strip()}")
    except Exception as e:
        print(f"Error running 'where az': {e}")
    
    print()

def check_azure_login():
    """Check if Azure login works."""
    print("=== AZURE LOGIN CHECK ===")
    
    # Try different methods
    methods = [
        ("subprocess.run(['az', 'account', 'show'])", lambda: subprocess.run(['az', 'account', 'show'], capture_output=True, text=True)),
        ("subprocess.run('az account show', shell=True)", lambda: subprocess.run('az account show', shell=True, capture_output=True, text=True)),
        ("subprocess.run(['az.cmd', 'account', 'show'])", lambda: subprocess.run(['az.cmd', 'account', 'show'], capture_output=True, text=True)),
        ("subprocess.run('az.cmd account show', shell=True)", lambda: subprocess.run('az.cmd account show', shell=True, capture_output=True, text=True))
    ]
    
    for method_name, method_func in methods:
        print(f"Testing: {method_name}")
        try:
            result = method_func()
            if result.returncode == 0:
                print(f"  ✓ SUCCESS: {method_name}")
                # Don't print the full output as it might contain sensitive info
                print(f"    Return code: {result.returncode}")
            else:
                print(f"  ✗ FAILED: {method_name}")
                print(f"    Return code: {result.returncode}")
                print(f"    Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"  ✗ ERROR: {method_name} - {e}")
        print()

def main():
    """Main debug function."""
    print("Azure CLI Debug Script for Windows")
    print("=" * 50)
    print()
    
    check_system_info()
    check_path()
    check_where_az()
    check_azure_cli_commands()
    check_azure_login()
    
    print("=== RECOMMENDATIONS ===")
    print("1. If 'where az' found az.cmd, the script should use 'az.cmd' instead of 'az'")
    print("2. If shell=True works but direct subprocess doesn't, use shell=True approach")
    print("3. Make sure Azure CLI is properly installed and in PATH")
    print("4. Try restarting PowerShell after Azure CLI installation")
    print("5. Check if running as administrator helps")

if __name__ == "__main__":
    main()

