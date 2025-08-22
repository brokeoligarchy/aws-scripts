# Azure VM Lister - Azure CLI Version

This PowerShell script uses Azure CLI 2.74 to list all Virtual Machines across Azure subscriptions.

## Prerequisites

- **Windows 11** with **PowerShell 5.1**
- **Azure CLI 2.74** or later installed
- Azure account with appropriate permissions
- Authenticated Azure CLI session

## Installation

### 1. Install Azure CLI

Download and install Azure CLI from the official Microsoft website:
https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows

### 2. Authenticate with Azure

```powershell
az login
```

This will open a browser window for authentication.

## Usage

### Basic Usage

List all VMs across all accessible subscriptions:

```powershell
.\List-AzureVMs-CLI.ps1
```

### Advanced Usage

#### List VMs in a specific subscription:

```powershell
.\List-AzureVMs-CLI.ps1 -SubscriptionId "12345678-1234-1234-1234-123456789012"
```

#### List VMs in a specific resource group:

```powershell
.\List-AzureVMs-CLI.ps1 -ResourceGroup "my-resource-group"
```

#### Get detailed VM information:

```powershell
.\List-AzureVMs-CLI.ps1 -Detailed
```

#### Include VM tags in output:

```powershell
.\List-AzureVMs-CLI.ps1 -ShowTags
```

#### Export to JSON format:

```powershell
.\List-AzureVMs-CLI.ps1 -OutputFormat JSON -OutputFile "my_vms.json"
```

#### Export to CSV format:

```powershell
.\List-AzureVMs-CLI.ps1 -OutputFormat CSV -OutputFile "my_vms.csv"
```

#### Combine multiple options:

```powershell
.\List-AzureVMs-CLI.ps1 -SubscriptionId "12345678-1234-1234-1234-123456789012" -Detailed -ShowTags -OutputFormat JSON
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `SubscriptionId` | String | No | Specific subscription ID to analyze |
| `ResourceGroup` | String | No | Specific resource group to analyze |
| `Detailed` | Switch | No | Get detailed VM information |
| `ShowTags` | Switch | No | Include VM tags in output |
| `OutputFormat` | String | No | Output format: Console, JSON, CSV, or Text |
| `OutputFile` | String | No | Output file path |
| `AllSubscriptions` | Switch | No | Process all accessible subscriptions |

## Output Information

The script provides the following information for each VM:

- **Name**: VM name
- **Resource Group**: Resource group containing the VM
- **Location**: Azure region
- **Subscription**: Subscription name and ID
- **VM Size**: Virtual machine size
- **Power State**: Current power state (Running, Stopped, etc.)
- **OS Type**: Operating system type (Windows, Linux)
- **OS Name**: Operating system name and version
- **OS Disk Size**: Size of the OS disk in GB
- **Network Interfaces**: Number of network interfaces
- **Tags**: VM tags (if enabled)

## Output Formats

### Console Output
- Colored, formatted table display
- Summary statistics
- Real-time progress information

### JSON Output
- Structured data format
- Includes metadata (generation timestamp, Azure CLI version)
- Suitable for programmatic processing

### CSV Output
- Comma-separated values
- Compatible with Excel and other spreadsheet applications
- All VM properties included

## Error Handling

The script includes comprehensive error handling:

- Azure CLI version compatibility check
- Authentication status verification
- Subscription access validation
- Graceful handling of permission errors
- Detailed error messages with troubleshooting suggestions

## Troubleshooting

### Common Issues

1. **Azure CLI not found**
   - Install Azure CLI from the official Microsoft website
   - Ensure it's added to your system PATH

2. **Not authenticated**
   - Run `az login` to authenticate
   - Check if your session has expired

3. **Insufficient permissions**
   - Ensure your account has Reader or higher permissions
   - Contact your Azure administrator

4. **Subscription not found**
   - Verify the subscription ID is correct
   - Ensure you have access to the subscription

### Version Compatibility

- **Azure CLI**: 2.74 or higher (recommended)
- **PowerShell**: 5.1 or higher
- **Windows**: 11 (tested)

## Examples

### Example 1: Basic VM listing
```powershell
.\List-AzureVMs-CLI.ps1
```

Output:
```
Azure VM Lister (Azure CLI 2.74)
============================================================
Compatible with: Windows 11, PowerShell 5.1
✓ Azure CLI found - Version: 2.74.0
✓ Azure CLI version is compatible (2.74+)
✓ Connected to Azure as: user@example.com
✓ Current subscription: My Subscription (12345678-1234-1234-1234-123456789012)
Getting subscriptions...
Found 3 subscription(s)

Processing subscription: My Subscription (12345678-1234-1234-1234-123456789012)
Found 5 VM(s) in subscription My Subscription

====================================================================================================
AZURE VMs SUMMARY (Azure CLI 2.74)
====================================================================================================
Total VMs found: 5

OS Type Distribution:
  Linux: 3
  Windows: 2

Power State Distribution:
  VM running: 4
  VM stopped: 1

Location Distribution:
  East US: 3
  West US 2: 2
```

### Example 2: Detailed output with tags
```powershell
.\List-AzureVMs-CLI.ps1 -Detailed -ShowTags -OutputFormat JSON
```

This will provide detailed information about each VM, include tags, and save the output to a JSON file.

## Security Notes

- The script only reads VM information (no modifications)
- No sensitive data is logged or stored
- Authentication tokens are managed by Azure CLI
- Output files contain only VM metadata (no credentials)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify Azure CLI version and authentication
3. Ensure proper permissions on Azure resources
4. Review the detailed error messages provided by the script
