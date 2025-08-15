# Azure VM Lister

A Python script to list all Azure VMs and their operating systems using Azure CLI.

## Features

- **List all VMs** across all subscriptions or specific subscriptions
- **OS Detection** - Automatically detects Windows/Linux and OS details
- **Comprehensive Information** - VM size, power state, location, resource group
- **Filtering Options** - By subscription, resource group
- **Detailed Mode** - Get additional OS information (slower but more detailed)
- **Multiple Export Formats** - Save results to JSON, CSV, or text files
- **Summary Statistics** - OS type distribution, power state distribution, location distribution
- **Tag Support** - Display VM tags for better organization

## Prerequisites

1. **Azure CLI Installation**: Install Azure CLI on your system
   ```bash
   # macOS (using Homebrew)
   brew install azure-cli
   
   # Windows (using winget)
   winget install Microsoft.AzureCLI
   
   # Linux (Ubuntu/Debian)
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

2. **Azure Login**: Log into your Azure account
   ```bash
   az login
   ```

3. **Python**: Python 3.6 or higher (uses only standard library modules)

## Installation

1. Clone or download the script
2. No additional Python packages required - uses only standard library

## Usage

### Basic Usage

```bash
# List all VMs across all subscriptions
python list_azure_vms.py

# List VMs in a specific subscription
python list_azure_vms.py --subscription "your-subscription-id"

# List VMs in a specific resource group
python list_azure_vms.py --resource-group "your-resource-group"
```

### Advanced Usage

```bash
# Get detailed OS information (slower but more accurate)
python list_azure_vms.py --detailed

# Show VM tags
python list_azure_vms.py --show-tags

# Save output to JSON file
python list_azure_vms.py --save-json "my_vms.json"

# Save output to CSV file
python list_azure_vms.py --save-csv "my_vms.csv"

# Save output to text file
python list_azure_vms.py --save-text "my_vms.txt"

# Show only summary statistics
python list_azure_vms.py --summary-only

# Combine options
python list_azure_vms.py --detailed --show-tags --save-csv "detailed_vms.csv"
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--subscription` | Specific subscription ID to analyze |
| `--resource-group` | Specific resource group to analyze |
| `--detailed` | Get detailed VM information (slower) |
| `--show-tags` | Show VM tags in output |
| `--save-json` | Save output to JSON file |
| `--save-csv` | Save output to CSV file |
| `--save-text` | Save output to text file |
| `--summary-only` | Show only summary, not detailed list |

## Output Examples

### Summary Output
```
====================================================================================================
AZURE VMs SUMMARY
====================================================================================================
Total VMs found: 15

OS Type Distribution:
  Linux: 8
  Windows: 7

Power State Distribution:
  VM running: 12
  VM deallocated: 3

Location Distribution:
  East US: 5
  West US 2: 4
  Central US: 3
  North Europe: 3
```

### Detailed Output
```
====================================================================================================
DETAILED VM INFORMATION
====================================================================================================
Name           Resource Group    Location    Subscription        VM Size    Power State    OS Type    OS Name              OS Disk (GB)
web-server-01  production-rg     East US     My Company          Standard_B2s VM running   Linux      Ubuntu 20.04 LTS     30
db-server-01   production-rg     East US     My Company          Standard_D4s VM running   Windows    Windows Server 2019  128
app-server-01  staging-rg        West US 2   My Company          Standard_B1s VM running   Linux      Ubuntu 18.04 LTS     20
```

## Information Retrieved

### Basic Information (Fast)
- VM Name
- Resource Group
- Location
- Subscription
- VM Size
- Power State
- Network Interface Count

### Detailed Information (Slower)
- OS Type (Windows/Linux)
- OS Name and Version
- OS Disk Size
- Image Reference Details

## OS Detection Methods

The script uses multiple methods to detect OS information:

1. **OS Profile Analysis** - Checks for `linuxConfiguration` or `windowsConfiguration`
2. **Image Reference** - Extracts OS details from the VM image
3. **Tags** - Looks for OS-related tags on the VM
4. **Fallback** - Uses "Unknown" if OS cannot be determined

## Export Formats

The script supports multiple export formats for different use cases:

### JSON Format
Best for programmatic processing and data analysis:

```json
{
  "generated_at": "2024-01-16T10:30:00",
  "total_vms": 15,
  "vms": [
    {
      "name": "web-server-01",
      "resource_group": "production-rg",
      "location": "East US",
      "subscription": "My Company",
      "subscription_id": "12345678-1234-1234-1234-123456789012",
      "vm_size": "Standard_B2s",
      "power_state": "VM running",
      "os_type": "Linux",
      "os_name": "Ubuntu 20.04 LTS",
      "os_version": "Unknown",
      "os_disk_size_gb": 30,
      "private_ip": "Unknown",
      "public_ip": "Unknown",
      "tags": {
        "Environment": "Production",
        "Project": "WebApp"
      }
    }
  ]
}
```

### CSV Format
Best for spreadsheet applications and data analysis:

```csv
Name,Resource Group,Location,Subscription,Subscription ID,VM Size,Power State,OS Type,OS Name,OS Version,OS Disk Size (GB),Network Interfaces,Tags
web-server-01,production-rg,East US,My Company,12345678-1234-1234-1234-123456789012,Standard_B2s,VM running,Linux,Ubuntu 20.04 LTS,Unknown,30,1,Environment=Production; Project=WebApp
db-server-01,production-rg,East US,My Company,12345678-1234-1234-1234-123456789012,Standard_D4s,VM running,Windows,Windows Server 2019,Unknown,128,1,Environment=Production; Project=Database
```

### Text Format
Best for human-readable reports and documentation:

```
Azure VM Information Report
==================================================
Generated: 2024-01-16 10:30:00
Total VMs: 15

SUMMARY
--------------------
OS Type Distribution:
  Linux: 8
  Windows: 7

Power State Distribution:
  VM running: 12
  VM deallocated: 3

Location Distribution:
  East US: 5
  West US 2: 4
  Central US: 3
  North Europe: 3

==================================================
DETAILED VM INFORMATION
==================================================

VM Name: web-server-01
Resource Group: production-rg
Location: East US
Subscription: My Company
Subscription ID: 12345678-1234-1234-1234-123456789012
VM Size: Standard_B2s
Power State: VM running
OS Type: Linux
OS Name: Ubuntu 20.04 LTS
OS Version: Unknown
OS Disk Size (GB): 30
Network Interfaces: 1
Tags: Environment=Production, Project=WebApp
----------------------------------------
```

## Performance Considerations

- **Basic Mode**: Fast, uses only `az vm list` command
- **Detailed Mode**: Slower, makes additional API calls for each VM
- **Large Subscriptions**: Consider using `--subscription` to limit scope
- **Resource Group Filtering**: Use `--resource-group` for faster results

## Troubleshooting

### Common Issues

1. **Azure CLI Not Found**
   ```
   Error: Azure CLI is not installed or not accessible.
   ```
   Solution: Install Azure CLI and ensure it's in your PATH

2. **Not Logged In**
   ```
   Error: Not logged into Azure CLI.
   ```
   Solution: Run `az login` to authenticate

3. **Permission Denied**
   ```
   Azure CLI command failed: Command 'az vm list' failed
   ```
   Solution: Ensure your account has Reader or higher permissions

4. **No VMs Found**
   ```
   No VMs found in subscription My Subscription
   ```
   Solution: Check if the subscription has VMs and you have access

5. **JSON Parsing Error**
   ```
   Failed to parse JSON output
   ```
   Solution: Check Azure CLI version and try updating it

### Debug Mode

To get more detailed error information, you can modify the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

- The script only reads VM information (no modifications)
- Uses Azure CLI authentication (supports MFA, service principals)
- No credentials are stored in the script
- Consider using service principals for automated runs

## Azure CLI Commands Used

The script uses these Azure CLI commands:

- `az account list` - Get subscriptions
- `az vm list` - List VMs in subscription
- `az vm show` - Get detailed VM information (detailed mode only)

## Contributing

Feel free to submit issues and enhancement requests!

## License

This script is provided as-is for educational and operational purposes.
