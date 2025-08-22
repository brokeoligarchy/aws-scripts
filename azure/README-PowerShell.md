# Azure VM Lister - PowerShell Script

This PowerShell script lists all Azure VMs from all accessible subscriptions with their operating system information.

## Features

- Lists all VMs across all accessible Azure subscriptions
- Shows detailed operating system information
- Displays power state, VM size, location, and other details
- Supports filtering by subscription and resource group
- Outputs to console, JSON, or CSV formats
- Includes VM tags (optional)
- Colored console output for better readability

## Prerequisites

1. **Azure PowerShell Module**: Install the Azure PowerShell module
   ```powershell
   Install-Module -Name Az -AllowClobber -Force
   ```

2. **Azure CLI**: Azure CLI 2.74 or later (you have 2.74 ✓)
   ```bash
   az --version
   ```

3. **Azure Authentication**: Connect to Azure
   ```powershell
   Connect-AzAccount
   ```
   
   Or using Azure CLI:
   ```bash
   az login
   ```

4. **PowerShell Version**: Requires PowerShell 5.1 or later (PowerShell Core 6.0+ recommended)

## Usage

### Basic Usage

List all VMs from all subscriptions:
```powershell
.\List-AzureVMs.ps1
```

### Advanced Usage

List VMs from a specific subscription:
```powershell
.\List-AzureVMs.ps1 -SubscriptionId "12345678-1234-1234-1234-123456789012"
```

List VMs from a specific resource group:
```powershell
.\List-AzureVMs.ps1 -ResourceGroup "my-resource-group"
```

Get detailed VM information (includes OS disk details):
```powershell
.\List-AzureVMs.ps1 -Detailed
```

Include VM tags in the output:
```powershell
.\List-AzureVMs.ps1 -ShowTags
```

Save output to JSON file:
```powershell
.\List-AzureVMs.ps1 -OutputFormat JSON -OutputFile "my_vms.json"
```

Save output to CSV file:
```powershell
.\List-AzureVMs.ps1 -OutputFormat CSV -OutputFile "my_vms.csv"
```

Combine multiple options:
```powershell
.\List-AzureVMs.ps1 -Detailed -ShowTags -OutputFormat JSON -OutputFile "detailed_vms.json"
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `SubscriptionId` | String | No | Specific subscription ID to analyze |
| `ResourceGroup` | String | No | Specific resource group to analyze |
| `Detailed` | Switch | No | Get detailed VM information including OS disk details |
| `ShowTags` | Switch | No | Include VM tags in the output |
| `OutputFormat` | String | No | Output format: Console, JSON, or CSV (default: Console) |
| `OutputFile` | String | No | Output file path (auto-generated if not specified) |

## Output Information

The script provides the following information for each VM:

- **Name**: VM name
- **Resource Group**: Resource group containing the VM
- **Location**: Azure region
- **Subscription**: Subscription name
- **Subscription ID**: Subscription identifier
- **VM Size**: Virtual machine size (e.g., Standard_D2s_v3)
- **Power State**: Current power state (Running, Stopped, etc.)
- **OS Type**: Operating system type (Windows, Linux, Unknown)
- **OS Name**: Operating system name (e.g., "Ubuntu Server 18.04 LTS")
- **OS Version**: Operating system version
- **OS Disk Size (GB)**: Size of the OS disk in gigabytes
- **Network Interfaces**: Number of network interfaces attached
- **Tags**: VM tags (if ShowTags parameter is used)

## Output Formats

### Console Output
- Colored output for better readability
- Summary statistics (OS type distribution, power states, locations)
- Detailed table format for VM information

### JSON Output
- Structured data format
- Includes metadata (generation timestamp, total VM count)
- Suitable for further processing or integration

### CSV Output
- Comma-separated values format
- Suitable for import into Excel or other spreadsheet applications
- Includes all VM properties

## Examples

### Example 1: Basic List
```powershell
.\List-AzureVMs.ps1
```
Output:
```
Azure VM Lister (PowerShell)
============================================================
✓ Azure PowerShell module found
✓ Connected to Azure as: user@example.com
Getting subscriptions...
Found 3 subscription(s)

Processing subscription: Production (12345678-1234-1234-1234-123456789012)
Found 5 VM(s) in subscription Production

====================================================================================================
AZURE VMs SUMMARY
====================================================================================================
Total VMs found: 5

OS Type Distribution:
  Linux: 3
  Windows: 2

Power State Distribution:
  Running: 4
  Stopped: 1

Location Distribution:
  East US: 3
  West US 2: 2
```

### Example 2: Detailed Output with Tags
```powershell
.\List-AzureVMs.ps1 -Detailed -ShowTags -OutputFormat JSON
```

### Example 3: Filter by Resource Group
```powershell
.\List-AzureVMs.ps1 -ResourceGroup "web-servers" -Detailed
```

## Troubleshooting

### Common Issues

1. **Azure PowerShell Module Not Found**
   ```
   ✗ Azure PowerShell module not found
   Please install with: Install-Module -Name Az -AllowClobber -Force
   ```
   Solution: Install the Azure PowerShell module as shown above.

2. **Not Connected to Azure**
   ```
   ✗ Not connected to Azure
   Please run: Connect-AzAccount
   ```
   Solution: Run `Connect-AzAccount` to authenticate with Azure.

3. **No Subscriptions Found**
   ```
   No subscriptions found or accessible.
   ```
   Solution: Check your Azure account permissions and ensure you have access to subscriptions.

4. **Execution Policy Error**
   ```
   File cannot be loaded because running scripts is disabled on this system.
   ```
   Solution: Set execution policy to allow script execution:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

### Performance Tips

- Use the `-Detailed` parameter only when needed, as it requires additional API calls
- For large environments, consider filtering by subscription or resource group
- JSON output is faster than CSV for large datasets

## Security Considerations

- The script requires Azure authentication with appropriate permissions
- VM information may contain sensitive data (names, resource groups, etc.)
- Output files should be stored securely
- Consider using Azure Key Vault for storing sensitive configuration

## Dependencies

- Azure PowerShell Module (Az)
- Azure CLI 2.74+ (you have 2.74 ✓)
- PowerShell 5.1+ or PowerShell Core 6.0+
- Internet connection for Azure API calls

## Compatibility Notes

- **Azure CLI 2.74**: Fully compatible with all script features
- **Azure PowerShell Module**: Works with Az module versions 5.0+
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Authentication**: Supports both interactive and service principal authentication

## License

This script is provided as-is for educational and operational purposes.
