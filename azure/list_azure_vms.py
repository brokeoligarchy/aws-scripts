#!/usr/bin/env python3
"""
Script to list all Azure VMs and their operating systems using Azure CLI.
"""

import subprocess
import json
import argparse
import sys
import csv
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_azure_cli_command(command):
    """
    Run an Azure CLI command and return the JSON output.
    
    Args:
        command (str): Azure CLI command to run
        
    Returns:
        dict: JSON response from Azure CLI
    """
    import platform
    
    # Detect if we're on Windows
    is_windows = platform.system().lower() == 'windows'
    
    # Try different approaches for Windows vs other platforms
    if is_windows:
        # On Windows, try different methods
        methods = [
            # Method 1: Use az.cmd with shell=True
            lambda cmd: subprocess.run(f"az.cmd {cmd.replace('az ', '')}", shell=True, capture_output=True, text=True, timeout=60),
            # Method 2: Use az with shell=True
            lambda cmd: subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60),
            # Method 3: Use az.cmd without shell
            lambda cmd: subprocess.run(f"az.cmd {cmd.replace('az ', '')}".split(), capture_output=True, text=True, timeout=60),
            # Method 4: Use az without shell
            lambda cmd: subprocess.run(cmd.split(), capture_output=True, text=True, timeout=60)
        ]
    else:
        # On non-Windows platforms
        methods = [
            lambda cmd: subprocess.run(cmd.split(), capture_output=True, text=True, timeout=60),
            lambda cmd: subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        ]
    
    for i, method in enumerate(methods, 1):
        try:
            logger.debug(f"Trying method {i} with command: {command}")
            
            result = method(command)
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON output: {e}")
                    logger.error(f"Raw output: {result.stdout}")
                    continue
            else:
                logger.debug(f"Method {i} failed - return code: {result.returncode}")
                if result.stderr.strip():
                    logger.debug(f"Error output: {result.stderr}")
                continue
                
        except subprocess.TimeoutExpired:
            logger.error(f"Azure CLI command timed out (method {i}): {command}")
            continue
        except FileNotFoundError:
            logger.debug(f"Azure CLI command not found (method {i}): {command}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error running Azure CLI command (method {i}): {e}")
            continue
    
    return None


def check_azure_cli_installed():
    """
    Check if Azure CLI is installed and accessible.
    
    Returns:
        bool: True if Azure CLI is available, False otherwise
    """
    import platform
    
    # Detect if we're on Windows
    is_windows = platform.system().lower() == 'windows'
    
    if is_windows:
        # On Windows, try different methods
        methods = [
            lambda: subprocess.run('az.cmd --version', shell=True, capture_output=True, text=True, timeout=10),
            lambda: subprocess.run('az --version', shell=True, capture_output=True, text=True, timeout=10),
            lambda: subprocess.run(['az.cmd', '--version'], capture_output=True, text=True, timeout=10),
            lambda: subprocess.run(['az', '--version'], capture_output=True, text=True, timeout=10)
        ]
    else:
        # On non-Windows platforms
        methods = [
            lambda: subprocess.run(['az', '--version'], capture_output=True, text=True, timeout=10),
            lambda: subprocess.run('az --version', shell=True, capture_output=True, text=True, timeout=10)
        ]
    
    for i, method in enumerate(methods, 1):
        try:
            result = method()
            if result.returncode == 0:
                logger.info(f"Found Azure CLI using method {i}")
                return True
        except FileNotFoundError:
            logger.debug(f"Method {i}: Azure CLI not found")
            continue
        except subprocess.TimeoutExpired:
            logger.warning(f"Method {i}: Azure CLI command timed out")
            continue
        except Exception as e:
            logger.debug(f"Method {i}: Error checking Azure CLI - {e}")
            continue
    
    return False


def check_azure_login():
    """
    Check if user is logged into Azure CLI.
    
    Returns:
        bool: True if logged in, False otherwise
    """
    import platform
    
    # Detect if we're on Windows
    is_windows = platform.system().lower() == 'windows'
    
    if is_windows:
        # On Windows, try different methods
        methods = [
            lambda: subprocess.run('az.cmd account show', shell=True, capture_output=True, text=True),
            lambda: subprocess.run('az account show', shell=True, capture_output=True, text=True),
            lambda: subprocess.run(['az.cmd', 'account', 'show'], capture_output=True, text=True),
            lambda: subprocess.run(['az', 'account', 'show'], capture_output=True, text=True)
        ]
    else:
        # On non-Windows platforms
        methods = [
            lambda: subprocess.run(['az', 'account', 'show'], capture_output=True, text=True),
            lambda: subprocess.run('az account show', shell=True, capture_output=True, text=True)
        ]
    
    for method in methods:
        try:
            result = method()
            if result.returncode == 0:
                return True
        except Exception:
            continue
    
    return False


def get_subscriptions():
    """
    Get list of all available subscriptions.
    
    Returns:
        list: List of subscription dictionaries
    """
    command = "az account list --output json"
    return run_azure_cli_command(command)


def get_vms_in_subscription(subscription_id):
    """
    Get all VMs in a specific subscription.
    
    Args:
        subscription_id (str): Azure subscription ID
        
    Returns:
        list: List of VM dictionaries
    """
    command = f"az vm list --subscription {subscription_id} --output json"
    return run_azure_cli_command(command)


def get_vm_details(subscription_id, resource_group, vm_name):
    """
    Get detailed information about a specific VM.
    
    Args:
        subscription_id (str): Azure subscription ID
        resource_group (str): Resource group name
        vm_name (str): VM name
        
    Returns:
        dict: VM details
    """
    command = f"az vm show --subscription {subscription_id} --resource-group {resource_group} --name {vm_name} --output json"
    return run_azure_cli_command(command)


def get_vm_os_info(vm_details):
    """
    Extract OS information from VM details.
    
    Args:
        vm_details (dict): VM details dictionary
        
    Returns:
        dict: OS information
    """
    os_info = {
        'os_type': 'Unknown',
        'os_name': 'Unknown',
        'os_version': 'Unknown',
        'os_disk_size_gb': 'Unknown'
    }
    
    try:
        # Get OS type (Windows/Linux)
        if 'osProfile' in vm_details and 'linuxConfiguration' in vm_details['osProfile']:
            os_info['os_type'] = 'Linux'
        elif 'osProfile' in vm_details and 'windowsConfiguration' in vm_details['osProfile']:
            os_info['os_type'] = 'Windows'
        
        # Get OS disk information
        if 'storageProfile' in vm_details and 'osDisk' in vm_details['storageProfile']:
            os_disk = vm_details['storageProfile']['osDisk']
            if 'diskSizeGB' in os_disk:
                os_info['os_disk_size_gb'] = os_disk['diskSizeGB']
            
            # Try to get OS name from image reference
            if 'imageReference' in os_disk:
                image_ref = os_disk['imageReference']
                if 'offer' in image_ref and 'sku' in image_ref:
                    os_info['os_name'] = f"{image_ref['offer']} {image_ref['sku']}"
                elif 'publisher' in image_ref and 'offer' in image_ref:
                    os_info['os_name'] = f"{image_ref['publisher']} {image_ref['offer']}"
        
        # Try to get OS name from VM name or tags
        if 'tags' in vm_details and vm_details['tags']:
            for tag_key, tag_value in vm_details['tags'].items():
                if 'os' in tag_key.lower() or 'system' in tag_key.lower():
                    os_info['os_name'] = tag_value
                    break
        
    except Exception as e:
        logger.debug(f"Error extracting OS info: {e}")
    
    return os_info


def format_vm_info(vm, subscription_name, vm_details=None):
    """
    Format VM information for display.
    
    Args:
        vm (dict): VM information
        subscription_name (str): Subscription name
        vm_details (dict): Detailed VM information
        
    Returns:
        dict: Formatted VM information
    """
    formatted_info = {
        'name': vm.get('name', 'Unknown'),
        'resource_group': vm.get('resourceGroup', 'Unknown'),
        'location': vm.get('location', 'Unknown'),
        'subscription': subscription_name,
        'subscription_id': vm.get('id', '').split('/')[2] if vm.get('id') else 'Unknown',
        'vm_size': vm.get('hardwareProfile', {}).get('vmSize', 'Unknown'),
        'power_state': 'Unknown',
        'os_type': 'Unknown',
        'os_name': 'Unknown',
        'os_version': 'Unknown',
        'os_disk_size_gb': 'Unknown',
        'private_ip': 'Unknown',
        'public_ip': 'Unknown',
        'tags': vm.get('tags', {})
    }
    
    # Get power state
    if vm.get('powerState'):
        formatted_info['power_state'] = vm['powerState']
    
    # Get OS information from detailed VM info
    if vm_details:
        os_info = get_vm_os_info(vm_details)
        formatted_info.update(os_info)
    
    # Get network information
    if 'networkProfile' in vm and vm['networkProfile'].get('networkInterfaces'):
        # Note: Getting IP addresses would require additional API calls
        # This is a simplified version
        formatted_info['network_interfaces'] = len(vm['networkProfile']['networkInterfaces'])
    
    return formatted_info


def print_vm_summary(vms_info):
    """
    Print a summary of all VMs.
    
    Args:
        vms_info (list): List of formatted VM information
    """
    if not vms_info:
        print("No VMs found.")
        return
    
    print(f"\n{'='*100}")
    print(f"AZURE VMs SUMMARY")
    print(f"{'='*100}")
    print(f"Total VMs found: {len(vms_info)}")
    
    # Count by OS type
    os_types = {}
    power_states = {}
    locations = {}
    
    for vm in vms_info:
        os_type = vm['os_type']
        power_state = vm['power_state']
        location = vm['location']
        
        os_types[os_type] = os_types.get(os_type, 0) + 1
        power_states[power_state] = power_states.get(power_state, 0) + 1
        locations[location] = locations.get(location, 0) + 1
    
    print(f"\nOS Type Distribution:")
    for os_type, count in sorted(os_types.items()):
        print(f"  {os_type}: {count}")
    
    print(f"\nPower State Distribution:")
    for state, count in sorted(power_states.items()):
        print(f"  {state}: {count}")
    
    print(f"\nLocation Distribution:")
    for location, count in sorted(locations.items()):
        print(f"  {location}: {count}")


def print_vm_details(vms_info, show_tags=False):
    """
    Print detailed VM information.
    
    Args:
        vms_info (list): List of formatted VM information
        show_tags (bool): Whether to show VM tags
    """
    if not vms_info:
        print("No VMs found.")
        return
    
    print(f"\n{'='*100}")
    print(f"DETAILED VM INFORMATION")
    print(f"{'='*100}")
    
    # Define column headers
    headers = [
        'Name', 'Resource Group', 'Location', 'Subscription', 
        'VM Size', 'Power State', 'OS Type', 'OS Name', 'OS Disk (GB)'
    ]
    
    # Calculate column widths
    col_widths = {header: len(header) for header in headers}
    
    # Update widths based on data
    for vm in vms_info:
        col_widths['Name'] = max(col_widths['Name'], len(vm['name']))
        col_widths['Resource Group'] = max(col_widths['Resource Group'], len(vm['resource_group']))
        col_widths['Location'] = max(col_widths['Location'], len(vm['location']))
        col_widths['Subscription'] = max(col_widths['Subscription'], len(vm['subscription']))
        col_widths['VM Size'] = max(col_widths['VM Size'], len(vm['vm_size']))
        col_widths['Power State'] = max(col_widths['Power State'], len(vm['power_state']))
        col_widths['OS Type'] = max(col_widths['OS Type'], len(vm['os_type']))
        col_widths['OS Name'] = max(col_widths['OS Name'], len(vm['os_name']))
        col_widths['OS Disk (GB)'] = max(col_widths['OS Disk (GB)'], len(str(vm['os_disk_size_gb'])))
    
    # Print header
    header_line = "  ".join(header.ljust(col_widths[header]) for header in headers)
    print(header_line)
    print("-" * len(header_line))
    
    # Print VM data
    for vm in sorted(vms_info, key=lambda x: (x['subscription'], x['resource_group'], x['name'])):
        row = [
            vm['name'].ljust(col_widths['Name']),
            vm['resource_group'].ljust(col_widths['Resource Group']),
            vm['location'].ljust(col_widths['Location']),
            vm['subscription'].ljust(col_widths['Subscription']),
            vm['vm_size'].ljust(col_widths['VM Size']),
            vm['power_state'].ljust(col_widths['Power State']),
            vm['os_type'].ljust(col_widths['OS Type']),
            vm['os_name'].ljust(col_widths['OS Name']),
            str(vm['os_disk_size_gb']).ljust(col_widths['OS Disk (GB)'])
        ]
        print("  ".join(row))
        
        # Show tags if requested
        if show_tags and vm['tags']:
            tag_line = "    Tags: " + ", ".join([f"{k}={v}" for k, v in vm['tags'].items()])
            print(tag_line)


def save_vms_to_json(vms_info, filename=None):
    """
    Save VM information to a JSON file.
    
    Args:
        vms_info (list): List of formatted VM information
        filename (str): Output filename (optional)
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"azure_vms_{timestamp}.json"
    
    try:
        output_data = {
            'generated_at': datetime.now().isoformat(),
            'total_vms': len(vms_info),
            'vms': vms_info
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"\nVM information saved to: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving to file: {e}")
        return None


def save_vms_to_csv(vms_info, filename=None):
    """
    Save VM information to a CSV file.
    
    Args:
        vms_info (list): List of formatted VM information
        filename (str): Output filename (optional)
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"azure_vms_{timestamp}.csv"
    
    try:
        # Define CSV headers
        headers = [
            'Name', 'Resource Group', 'Location', 'Subscription', 'Subscription ID',
            'VM Size', 'Power State', 'OS Type', 'OS Name', 'OS Version', 
            'OS Disk Size (GB)', 'Network Interfaces', 'Tags'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for vm in vms_info:
                # Prepare row data
                row = {
                    'Name': vm.get('name', ''),
                    'Resource Group': vm.get('resource_group', ''),
                    'Location': vm.get('location', ''),
                    'Subscription': vm.get('subscription', ''),
                    'Subscription ID': vm.get('subscription_id', ''),
                    'VM Size': vm.get('vm_size', ''),
                    'Power State': vm.get('power_state', ''),
                    'OS Type': vm.get('os_type', ''),
                    'OS Name': vm.get('os_name', ''),
                    'OS Version': vm.get('os_version', ''),
                    'OS Disk Size (GB)': vm.get('os_disk_size_gb', ''),
                    'Network Interfaces': vm.get('network_interfaces', ''),
                    'Tags': '; '.join([f"{k}={v}" for k, v in vm.get('tags', {}).items()])
                }
                writer.writerow(row)
        
        print(f"\nVM information saved to CSV: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving to CSV file: {e}")
        return None


def save_vms_to_text(vms_info, filename=None, show_tags=False):
    """
    Save VM information to a text file.
    
    Args:
        vms_info (list): List of formatted VM information
        filename (str): Output filename (optional)
        show_tags (bool): Whether to include tags in the output
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"azure_vms_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # Write header
            f.write("Azure VM Information Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total VMs: {len(vms_info)}\n\n")
            
            # Write summary
            f.write("SUMMARY\n")
            f.write("-" * 20 + "\n")
            
            # Count by OS type
            os_types = {}
            power_states = {}
            locations = {}
            
            for vm in vms_info:
                os_type = vm.get('os_type', 'Unknown')
                power_state = vm.get('power_state', 'Unknown')
                location = vm.get('location', 'Unknown')
                
                os_types[os_type] = os_types.get(os_type, 0) + 1
                power_states[power_state] = power_states.get(power_state, 0) + 1
                locations[location] = locations.get(location, 0) + 1
            
            f.write(f"OS Type Distribution:\n")
            for os_type, count in sorted(os_types.items()):
                f.write(f"  {os_type}: {count}\n")
            
            f.write(f"\nPower State Distribution:\n")
            for state, count in sorted(power_states.items()):
                f.write(f"  {state}: {count}\n")
            
            f.write(f"\nLocation Distribution:\n")
            for location, count in sorted(locations.items()):
                f.write(f"  {location}: {count}\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("DETAILED VM INFORMATION\n")
            f.write("=" * 50 + "\n\n")
            
            # Write detailed information
            for vm in sorted(vms_info, key=lambda x: (x.get('subscription', ''), x.get('resource_group', ''), x.get('name', ''))):
                f.write(f"VM Name: {vm.get('name', 'Unknown')}\n")
                f.write(f"Resource Group: {vm.get('resource_group', 'Unknown')}\n")
                f.write(f"Location: {vm.get('location', 'Unknown')}\n")
                f.write(f"Subscription: {vm.get('subscription', 'Unknown')}\n")
                f.write(f"Subscription ID: {vm.get('subscription_id', 'Unknown')}\n")
                f.write(f"VM Size: {vm.get('vm_size', 'Unknown')}\n")
                f.write(f"Power State: {vm.get('power_state', 'Unknown')}\n")
                f.write(f"OS Type: {vm.get('os_type', 'Unknown')}\n")
                f.write(f"OS Name: {vm.get('os_name', 'Unknown')}\n")
                f.write(f"OS Version: {vm.get('os_version', 'Unknown')}\n")
                f.write(f"OS Disk Size (GB): {vm.get('os_disk_size_gb', 'Unknown')}\n")
                f.write(f"Network Interfaces: {vm.get('network_interfaces', 'Unknown')}\n")
                
                if show_tags and vm.get('tags'):
                    f.write(f"Tags: {', '.join([f'{k}={v}' for k, v in vm['tags'].items()])}\n")
                
                f.write("-" * 40 + "\n\n")
        
        print(f"\nVM information saved to text file: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving to text file: {e}")
        return None


def main():
    """
    Main function to list Azure VMs.
    """
    parser = argparse.ArgumentParser(description='List Azure VMs and their operating systems')
    parser.add_argument('--subscription', help='Specific subscription ID to analyze')
    parser.add_argument('--resource-group', help='Specific resource group to analyze')
    parser.add_argument('--detailed', action='store_true', help='Get detailed VM information (slower)')
    parser.add_argument('--show-tags', action='store_true', help='Show VM tags')
    parser.add_argument('--save-json', help='Save output to JSON file')
    parser.add_argument('--save-csv', help='Save output to CSV file')
    parser.add_argument('--save-text', help='Save output to text file')
    parser.add_argument('--summary-only', action='store_true', help='Show only summary, not detailed list')
    
    args = parser.parse_args()
    
    print("Azure VM Lister")
    print("=" * 60)
    
    # Check if Azure CLI is installed
    if not check_azure_cli_installed():
        print("Error: Azure CLI is not installed or not accessible.")
        print("\nTroubleshooting steps:")
        print("1. Run the debug script: python debug_azure_cli.py")
        print("2. Make sure Azure CLI is installed and in your PATH")
        print("3. Try restarting your terminal/command prompt")
        print("4. Check installation at: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        print("\nCommon solutions:")
        print("- Windows: Restart terminal after installation")
        print("- macOS: Check if Homebrew path is in your shell profile")
        print("- Linux: Make sure /usr/local/bin is in your PATH")
        sys.exit(1)
    
    # Check if user is logged in
    if not check_azure_login():
        print("Error: Not logged into Azure CLI.")
        print("Please run: az login")
        sys.exit(1)
    
    try:
        # Get subscriptions
        print("Getting subscriptions...")
        subscriptions = get_subscriptions()
        
        if not subscriptions:
            print("No subscriptions found or accessible.")
            return
        
        print(f"Found {len(subscriptions)} subscription(s)")
        
        # Filter subscriptions if specified
        if args.subscription:
            subscriptions = [sub for sub in subscriptions if sub.get('id') == args.subscription]
            if not subscriptions:
                print(f"Subscription {args.subscription} not found or not accessible.")
                return
        
        all_vms_info = []
        
        # Process each subscription
        for subscription in subscriptions:
            subscription_id = subscription.get('id')
            subscription_name = subscription.get('name', 'Unknown')
            
            print(f"\nProcessing subscription: {subscription_name} ({subscription_id})")
            
            # Get VMs in this subscription
            vms = get_vms_in_subscription(subscription_id)
            
            if not vms:
                print(f"No VMs found in subscription {subscription_name}")
                continue
            
            print(f"Found {len(vms)} VM(s) in subscription {subscription_name}")
            
            # Process each VM
            for vm in vms:
                vm_name = vm.get('name')
                resource_group = vm.get('resourceGroup')
                
                # Skip if resource group filter is specified
                if args.resource_group and resource_group != args.resource_group:
                    continue
                
                vm_details = None
                if args.detailed:
                    print(f"  Getting details for VM: {vm_name}")
                    vm_details = get_vm_details(subscription_id, resource_group, vm_name)
                
                # Format VM information
                vm_info = format_vm_info(vm, subscription_name, vm_details)
                all_vms_info.append(vm_info)
        
        if not all_vms_info:
            print("No VMs found matching the criteria.")
            return
        
        # Print summary
        print_vm_summary(all_vms_info)
        
        # Print detailed information if not summary-only
        if not args.summary_only:
            print_vm_details(all_vms_info, show_tags=args.show_tags)
        
        # Save to files if requested
        if args.save_json:
            save_vms_to_json(all_vms_info, args.save_json)
        elif args.save_csv:
            save_vms_to_csv(all_vms_info, args.save_csv)
        elif args.save_text:
            save_vms_to_text(all_vms_info, args.save_text, show_tags=args.show_tags)
        elif args.detailed:
            # Auto-save detailed information to JSON
            save_vms_to_json(all_vms_info)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    main()
