#!/usr/bin/env python3
"""
Debug script to troubleshoot Azure CLI installation and PATH issues.
"""

import subprocess
import os
import sys
import platform

def check_azure_cli_installation():
    """Check Azure CLI installation and provide detailed diagnostics."""
    
    print("Azure CLI Installation Diagnostics")
    print("=" * 50)
    
    # Check system information
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print()
    
    # Check PATH environment variable
    print("PATH Environment Variable:")
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    for i, path_dir in enumerate(path_dirs):
        print(f"  {i+1:2d}. {path_dir}")
    print()
    
    # Try different ways to find Azure CLI
    az_commands = ['az', 'az.cmd', 'azure-cli']
    az_found = False
    
    print("Checking for Azure CLI executable:")
    for cmd in az_commands:
        try:
            # Check if command exists in PATH
            result = subprocess.run(
                [cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ Found: {cmd}")
                print(f"   Version: {result.stdout.strip()}")
                az_found = True
                break
            else:
                print(f"❌ {cmd} returned error code: {result.returncode}")
                print(f"   Error: {result.stderr.strip()}")
                
        except FileNotFoundError:
            print(f"❌ {cmd} not found in PATH")
        except subprocess.TimeoutExpired:
            print(f"⏰ {cmd} command timed out")
        except Exception as e:
            print(f"❌ Error running {cmd}: {e}")
    
    print()
    
    # Check common installation locations
    print("Checking common Azure CLI installation locations:")
    common_paths = [
        # Windows
        r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin",
        r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin",
        r"C:\Users\{}\AppData\Local\Programs\Azure CLI\bin".format(os.getenv('USERNAME', '')),
        
        # macOS
        "/usr/local/bin",
        "/opt/homebrew/bin",
        "/usr/bin",
        
        # Linux
        "/usr/local/bin",
        "/usr/bin",
        "/opt/azure-cli/bin",
    ]
    
    for path in common_paths:
        az_path = os.path.join(path, 'az')
        az_cmd_path = os.path.join(path, 'az.cmd')
        
        if os.path.exists(az_path):
            print(f"✅ Found az at: {az_path}")
            az_found = True
        elif os.path.exists(az_cmd_path):
            print(f"✅ Found az.cmd at: {az_cmd_path}")
            az_found = True
        else:
            print(f"❌ Not found: {path}")
    
    print()
    
    # Provide installation instructions
    if not az_found:
        print("Azure CLI not found. Installation instructions:")
        print()
        
        system = platform.system().lower()
        if system == "windows":
            print("Windows Installation:")
            print("1. Download from: https://aka.ms/installazurecliwindows")
            print("2. Or use winget: winget install Microsoft.AzureCLI")
            print("3. Or use Chocolatey: choco install azure-cli")
            print("4. Restart your terminal after installation")
            
        elif system == "darwin":  # macOS
            print("macOS Installation:")
            print("1. Using Homebrew: brew install azure-cli")
            print("2. Or download from: https://aka.ms/installazureclimacos")
            print("3. Restart your terminal after installation")
            
        elif system == "linux":
            print("Linux Installation:")
            print("1. Ubuntu/Debian: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash")
            print("2. RHEL/CentOS: sudo yum install azure-cli")
            print("3. Or download from: https://aka.ms/InstallAzureCLILinux")
            print("4. Restart your terminal after installation")
    else:
        print("✅ Azure CLI is installed and accessible!")
        print()
        print("If you're still getting errors, try:")
        print("1. Restart your terminal/command prompt")
        print("2. Check if you need to log in: az login")
        print("3. Verify your account: az account show")

def test_azure_cli_commands():
    """Test various Azure CLI commands."""
    
    print("\n" + "=" * 50)
    print("Testing Azure CLI Commands")
    print("=" * 50)
    
    commands_to_test = [
        ['az', '--version'],
        ['az', 'account', 'show'],
        ['az', 'account', 'list', '--output', 'table']
    ]
    
    for cmd in commands_to_test:
        print(f"\nTesting: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Success!")
                if result.stdout.strip():
                    print(f"Output: {result.stdout.strip()[:200]}...")
            else:
                print(f"❌ Failed with code: {result.returncode}")
                if result.stderr.strip():
                    print(f"Error: {result.stderr.strip()}")
                    
        except FileNotFoundError:
            print("❌ Command not found")
        except subprocess.TimeoutExpired:
            print("⏰ Command timed out")
        except Exception as e:
            print(f"❌ Error: {e}")

def provide_solutions():
    """Provide common solutions for Azure CLI issues."""
    
    print("\n" + "=" * 50)
    print("Common Solutions")
    print("=" * 50)
    
    print("1. PATH Issues:")
    print("   - Restart your terminal/command prompt")
    print("   - Add Azure CLI to your PATH manually")
    print("   - Check if Azure CLI is in your PATH: echo $PATH (Linux/macOS) or echo %PATH% (Windows)")
    
    print("\n2. Installation Issues:")
    print("   - Uninstall and reinstall Azure CLI")
    print("   - Use the official installer from Microsoft")
    print("   - Check for conflicting installations")
    
    print("\n3. Permission Issues:")
    print("   - Run as administrator (Windows)")
    print("   - Use sudo (Linux/macOS)")
    print("   - Check file permissions")
    
    print("\n4. Authentication Issues:")
    print("   - Run: az login")
    print("   - Check if you're logged in: az account show")
    print("   - Clear cached credentials: az account clear")

if __name__ == "__main__":
    check_azure_cli_installation()
    test_azure_cli_commands()
    provide_solutions()

