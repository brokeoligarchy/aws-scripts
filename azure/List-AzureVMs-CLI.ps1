#!/usr/bin/env pwsh
<#
.SYNOPSIS
    List all Azure VMs using Azure CLI 2.74

.DESCRIPTION
    This script uses Azure CLI 2.74 to connect to Azure and list all VMs
    across all accessible subscriptions with detailed information including
    operating system details, power state, and other relevant information.
    Optimized for Windows 11 and PowerShell 5.1.

.PARAMETER SubscriptionId
    Optional. Specific subscription ID to analyze.

.PARAMETER ResourceGroup
    Optional. Specific resource group to analyze.

.PARAMETER Detailed
    Optional. Get detailed VM information including network interfaces and disks.

.PARAMETER ShowTags
    Optional. Include VM tags in the output.

.PARAMETER OutputFormat
    Optional. Output format: Console, JSON, CSV, or Text. Default is Console.

.PARAMETER OutputFile
    Optional. Output file path.

.PARAMETER AllSubscriptions
    Optional. Process all accessible subscriptions (default behavior).

.EXAMPLE
    .\List-AzureVMs-CLI.ps1

.EXAMPLE
    .\List-AzureVMs-CLI.ps1 -SubscriptionId "12345678-1234-1234-1234-123456789012" -Detailed

.EXAMPLE
    .\List-AzureVMs-CLI.ps1 -OutputFormat JSON -OutputFile "my_vms.json"

.EXAMPLE
    .\List-AzureVMs-CLI.ps1 -ResourceGroup "my-rg" -ShowTags

.NOTES
    Requires Azure CLI 2.74 or later to be installed and user to be authenticated.
    Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows
    Authenticate with: az login
    Version: 1.0
    Author: Azure Scripts
    Compatible with: Windows 11, PowerShell 5.1, Azure CLI 2.74+
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory = $false)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory = $false)]
    [switch]$Detailed,
    
    [Parameter(Mandatory = $false)]
    [switch]$ShowTags,
    
    [Parameter(Mandatory = $false)]
    [ValidateSet("Console", "JSON", "CSV", "Text")]
    [string]$OutputFormat = "Console",
    
    [Parameter(Mandatory = $false)]
    [string]$OutputFile,
    
    [Parameter(Mandatory = $false)]
    [switch]$AllSubscriptions
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if Azure CLI is installed
function Test-AzureCLI {
    try {
        $azVersion = az version --output json 2>$null | ConvertFrom-Json
        if ($azVersion) {
            $cliVersion = $azVersion.'azure-cli'
            Write-ColorOutput "✓ Azure CLI found - Version: $cliVersion" "Green"
            
            # Check if version is 2.74 or higher
            $versionParts = $cliVersion.Split('.')
            if ($versionParts.Count -ge 2) {
                $major = [int]$versionParts[0]
                $minor = [int]$versionParts[1]
                if ($major -gt 2 -or ($major -eq 2 -and $minor -ge 74)) {
                    Write-ColorOutput "✓ Azure CLI version is compatible (2.74+)" "Green"
                    return $true
                } else {
                    Write-ColorOutput "⚠ Azure CLI version $cliVersion detected. Recommended: 2.74 or higher" "Yellow"
                    return $true
                }
            }
            return $true
        } else {
            Write-ColorOutput "✗ Azure CLI not found" "Red"
            Write-ColorOutput "Please install Azure CLI from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows" "Yellow"
            return $false
        }
    }
    catch {
        Write-ColorOutput "✗ Error checking Azure CLI: $($_.Exception.Message)" "Red"
        Write-ColorOutput "Please install Azure CLI from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows" "Yellow"
        return $false
    }
}

# Function to check Azure authentication
function Test-AzureConnection {
    try {
        $account = az account show --output json 2>$null | ConvertFrom-Json
        if ($account) {
            Write-ColorOutput "✓ Connected to Azure as: $($account.user.name)" "Green"
            Write-ColorOutput "✓ Current subscription: $($account.name) ($($account.id))" "Green"
            return $true
        } else {
            Write-ColorOutput "✗ Not connected to Azure" "Red"
            Write-ColorOutput "Please run: az login" "Yellow"
            return $false
        }
    }
    catch {
        Write-ColorOutput "✗ Error checking Azure connection: $($_.Exception.Message)" "Red"
        Write-ColorOutput "Please run: az login" "Yellow"
        return $false
    }
}

# Function to get all accessible subscriptions
function Get-AzureSubscriptions {
    param([string]$SpecificSubscriptionId)
    
    try {
        if ($SpecificSubscriptionId) {
            $subscriptions = az account subscription show --subscription $SpecificSubscriptionId --output json 2>$null | ConvertFrom-Json
            if ($subscriptions) {
                return @($subscriptions)
            } else {
                Write-ColorOutput "Subscription $SpecificSubscriptionId not found or not accessible." "Red"
                return @()
            }
        } else {
            $subscriptions = az account subscription list --output json 2>$null | ConvertFrom-Json
            return $subscriptions
        }
    }
    catch {
        Write-ColorOutput "Error getting subscriptions: $($_.Exception.Message)" "Red"
        return @()
    }
}

# Function to get VMs for a subscription
function Get-AzureVMs {
    param(
        [string]$SubscriptionId,
        [string]$ResourceGroup,
        [switch]$Detailed
    )
    
    try {
        # Set subscription context
        az account set --subscription $SubscriptionId 2>$null | Out-Null
        
        $vmParams = @("vm", "list")
        
        if ($ResourceGroup) {
            $vmParams += "--resource-group", $ResourceGroup
        }
        
        if ($Detailed) {
            $vmParams += "--show-details"
        }
        
        $vmParams += "--output", "json"
        
        $vms = az $vmParams 2>$null | ConvertFrom-Json
        return $vms
    }
    catch {
        Write-ColorOutput "Error getting VMs for subscription $SubscriptionId`: $($_.Exception.Message)" "Red"
        return @()
    }
}

# Function to get VM power state
function Get-VMPowerState {
    param([string]$ResourceGroup, [string]$VMName)
    
    try {
        $powerState = az vm get-instance-view --resource-group $ResourceGroup --name $VMName --output json 2>$null | ConvertFrom-Json
        if ($powerState.statuses) {
            $powerStatus = $powerState.statuses | Where-Object { $_.code -like "PowerState/*" }
            if ($powerStatus) {
                return $powerStatus.displayStatus
            }
        }
        return "Unknown"
    }
    catch {
        return "Unknown"
    }
}

# Function to get OS information from VM
function Get-VMOSInfo {
    param([object]$VM)
    
    $osInfo = @{
        OSType = "Unknown"
        OSName = "Unknown"
        OSVersion = "Unknown"
        OSDiskSizeGB = "Unknown"
    }
    
    try {
        # Get OS type
        if ($VM.storageProfile.osDisk.osType) {
            $osInfo.OSType = $VM.storageProfile.osDisk.osType
        }
        
        # Get OS disk information
        if ($VM.storageProfile.osDisk.diskSizeGB) {
            $osInfo.OSDiskSizeGB = $VM.storageProfile.osDisk.diskSizeGB
        }
        
        # Try to get OS name from image reference
        if ($VM.storageProfile.imageReference) {
            $imageRef = $VM.storageProfile.imageReference
            if ($imageRef.offer -and $imageRef.sku) {
                $osInfo.OSName = "$($imageRef.offer) $($imageRef.sku)"
            } elseif ($imageRef.publisher -and $imageRef.offer) {
                $osInfo.OSName = "$($imageRef.publisher) $($imageRef.offer)"
            }
        }
        
        # Try to get OS name from VM tags
        if ($VM.tags) {
            foreach ($tag in $VM.tags.PSObject.Properties) {
                if ($tag.Name -like "*os*" -or $tag.Name -like "*system*") {
                    $osInfo.OSName = $tag.Value
                    break
                }
            }
        }
    }
    catch {
        Write-Warning "Error extracting OS info for VM $($VM.name): $($_.Exception.Message)"
    }
    
    return $osInfo
}

# Function to format VM information
function Format-VMInfo {
    param(
        [object]$VM,
        [string]$SubscriptionName,
        [hashtable]$OSInfo
    )
    
    $vmInfo = @{
        Name = $VM.name
        ResourceGroup = $VM.resourceGroup
        Location = $VM.location
        Subscription = $SubscriptionName
        SubscriptionId = $VM.id.Split('/')[2]
        VMSize = $VM.hardwareProfile.vmSize
        PowerState = "Unknown"
        OSType = "Unknown"
        OSName = "Unknown"
        OSVersion = "Unknown"
        OSDiskSizeGB = "Unknown"
        NetworkInterfaces = 0
        Tags = @{}
    }
    
    # Get power state
    $vmInfo.PowerState = Get-VMPowerState -ResourceGroup $VM.resourceGroup -VMName $VM.name
    
    # Get OS information
    if ($OSInfo) {
        $vmInfo.OSType = $OSInfo.OSType
        $vmInfo.OSName = $OSInfo.OSName
        $vmInfo.OSVersion = $OSInfo.OSVersion
        $vmInfo.OSDiskSizeGB = $OSInfo.OSDiskSizeGB
    }
    
    # Get network interface count
    if ($VM.networkProfile.networkInterfaces) {
        $vmInfo.NetworkInterfaces = $VM.networkProfile.networkInterfaces.Count
    }
    
    # Get tags
    if ($VM.tags) {
        foreach ($tag in $VM.tags.PSObject.Properties) {
            $vmInfo.Tags[$tag.Name] = $tag.Value
        }
    }
    
    return $vmInfo
}

# Function to print VM summary
function Show-VMSummary {
    param([array]$VMsInfo)
    
    if (-not $VMsInfo -or $VMsInfo.Count -eq 0) {
        Write-ColorOutput "No VMs found." "Yellow"
        return
    }
    
    Write-ColorOutput "`n" + "=" * 100 "Cyan"
    Write-ColorOutput "AZURE VMs SUMMARY (Azure CLI 2.74)" "Cyan"
    Write-ColorOutput "=" * 100 "Cyan"
    Write-ColorOutput "Total VMs found: $($VMsInfo.Count)" "White"
    
    # Count by OS type
    $osTypes = @{}
    $powerStates = @{}
    $locations = @{}
    
    foreach ($vm in $VMsInfo) {
        $osType = $vm.OSType
        $powerState = $vm.PowerState
        $location = $vm.Location
        
        if ($osTypes.ContainsKey($osType)) {
            $osTypes[$osType]++
        } else {
            $osTypes[$osType] = 1
        }
        
        if ($powerStates.ContainsKey($powerState)) {
            $powerStates[$powerState]++
        } else {
            $powerStates[$powerState] = 1
        }
        
        if ($locations.ContainsKey($location)) {
            $locations[$location]++
        } else {
            $locations[$location] = 1
        }
    }
    
    Write-ColorOutput "`nOS Type Distribution:" "Yellow"
    foreach ($osType in $osTypes.Keys | Sort-Object) {
        Write-ColorOutput "  $osType`: $($osTypes[$osType])" "White"
    }
    
    Write-ColorOutput "`nPower State Distribution:" "Yellow"
    foreach ($state in $powerStates.Keys | Sort-Object) {
        Write-ColorOutput "  $state`: $($powerStates[$state])" "White"
    }
    
    Write-ColorOutput "`nLocation Distribution:" "Yellow"
    foreach ($location in $locations.Keys | Sort-Object) {
        Write-ColorOutput "  $location`: $($locations[$location])" "White"
    }
}

# Function to print detailed VM information
function Show-VMDetails {
    param([array]$VMsInfo, [switch]$ShowTags)
    
    if (-not $VMsInfo -or $VMsInfo.Count -eq 0) {
        Write-ColorOutput "No VMs found." "Yellow"
        return
    }
    
    Write-ColorOutput "`n" + "=" * 100 "Cyan"
    Write-ColorOutput "DETAILED VM INFORMATION" "Cyan"
    Write-ColorOutput "=" * 100 "Cyan"
    
    # Define column headers
    $headers = @('Name', 'Resource Group', 'Location', 'Subscription', 'VM Size', 'Power State', 'OS Type', 'OS Name', 'OS Disk (GB)')
    
    # Calculate column widths
    $colWidths = @{}
    foreach ($header in $headers) {
        $colWidths[$header] = $header.Length
    }
    
    # Update widths based on data
    foreach ($vm in $VMsInfo) {
        $colWidths['Name'] = [Math]::Max($colWidths['Name'], $vm.Name.Length)
        $colWidths['Resource Group'] = [Math]::Max($colWidths['Resource Group'], $vm.ResourceGroup.Length)
        $colWidths['Location'] = [Math]::Max($colWidths['Location'], $vm.Location.Length)
        $colWidths['Subscription'] = [Math]::Max($colWidths['Subscription'], $vm.Subscription.Length)
        $colWidths['VM Size'] = [Math]::Max($colWidths['VM Size'], $vm.VMSize.Length)
        $colWidths['Power State'] = [Math]::Max($colWidths['Power State'], $vm.PowerState.Length)
        $colWidths['OS Type'] = [Math]::Max($colWidths['OS Type'], $vm.OSType.Length)
        $colWidths['OS Name'] = [Math]::Max($colWidths['OS Name'], $vm.OSName.Length)
        $colWidths['OS Disk (GB)'] = [Math]::Max($colWidths['OS Disk (GB)'], $vm.OSDiskSizeGB.ToString().Length)
    }
    
    # Print header
    $headerLine = ""
    foreach ($header in $headers) {
        $headerLine += $header.PadRight($colWidths[$header]) + "  "
    }
    Write-ColorOutput $headerLine "Yellow"
    Write-ColorOutput ("-" * $headerLine.Length) "Yellow"
    
    # Print VM data
    foreach ($vm in $VMsInfo | Sort-Object Subscription, ResourceGroup, Name) {
        $row = @(
            $vm.Name.PadRight($colWidths['Name']),
            $vm.ResourceGroup.PadRight($colWidths['Resource Group']),
            $vm.Location.PadRight($colWidths['Location']),
            $vm.Subscription.PadRight($colWidths['Subscription']),
            $vm.VMSize.PadRight($colWidths['VM Size']),
            $vm.PowerState.PadRight($colWidths['Power State']),
            $vm.OSType.PadRight($colWidths['OS Type']),
            $vm.OSName.PadRight($colWidths['OS Name']),
            $vm.OSDiskSizeGB.ToString().PadRight($colWidths['OS Disk (GB)'])
        )
        Write-ColorOutput ($row -join "  ") "White"
        
        # Show tags if requested
        if ($ShowTags -and $vm.Tags.Count -gt 0) {
            $tagLine = "    Tags: " + ($vm.Tags.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ", "
            Write-ColorOutput $tagLine "Gray"
        }
    }
}

# Function to save output to JSON
function Save-VMsToJSON {
    param([array]$VMsInfo, [string]$OutputFile)
    
    if (-not $OutputFile) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $OutputFile = "azure_vms_cli_$timestamp.json"
    }
    
    try {
        $outputData = @{
            GeneratedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
            AzureCLIVersion = (az version --output json 2>$null | ConvertFrom-Json).'azure-cli'
            TotalVMs = $VMsInfo.Count
            VMs = $VMsInfo
        }
        
        $outputData | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputFile -Encoding UTF8
        Write-ColorOutput "`nVM information saved to: $OutputFile" "Green"
        return $OutputFile
    }
    catch {
        Write-ColorOutput "Error saving to JSON file: $($_.Exception.Message)" "Red"
        return $null
    }
}

# Function to save output to CSV
function Save-VMsToCSV {
    param([array]$VMsInfo, [string]$OutputFile)
    
    if (-not $OutputFile) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $OutputFile = "azure_vms_cli_$timestamp.csv"
    }
    
    try {
        $csvData = @()
        foreach ($vm in $VMsInfo) {
            $csvData += [PSCustomObject]@{
                Name = $vm.Name
                ResourceGroup = $vm.ResourceGroup
                Location = $vm.Location
                Subscription = $vm.Subscription
                SubscriptionId = $vm.SubscriptionId
                VMSize = $vm.VMSize
                PowerState = $vm.PowerState
                OSType = $vm.OSType
                OSName = $vm.OSName
                OSVersion = $vm.OSVersion
                OSDiskSizeGB = $vm.OSDiskSizeGB
                NetworkInterfaces = $vm.NetworkInterfaces
                Tags = ($vm.Tags.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "; "
            }
        }
        
        $csvData | Export-Csv -Path $OutputFile -NoTypeInformation -Encoding UTF8
        Write-ColorOutput "`nVM information saved to CSV: $OutputFile" "Green"
        return $OutputFile
    }
    catch {
        Write-ColorOutput "Error saving to CSV file: $($_.Exception.Message)" "Red"
        return $null
    }
}

# Main script execution
try {
    Write-ColorOutput "Azure VM Lister (Azure CLI 2.74)" "Cyan"
    Write-ColorOutput "=" * 60 "Cyan"
    Write-ColorOutput "Compatible with: Windows 11, PowerShell 5.1" "Gray"
    
    # Check Azure CLI
    if (-not (Test-AzureCLI)) {
        exit 1
    }
    
    # Check Azure connection
    if (-not (Test-AzureConnection)) {
        exit 1
    }
    
    # Get subscriptions
    Write-ColorOutput "Getting subscriptions..." "White"
    $subscriptions = Get-AzureSubscriptions -SpecificSubscriptionId $SubscriptionId
    
    if (-not $subscriptions -or $subscriptions.Count -eq 0) {
        Write-ColorOutput "No subscriptions found or accessible." "Red"
        exit 1
    }
    
    Write-ColorOutput "Found $($subscriptions.Count) subscription(s)" "Green"
    
    $allVMsInfo = @()
    
    # Process each subscription
    foreach ($subscription in $subscriptions) {
        $subscriptionId = $subscription.subscriptionId
        $subscriptionName = $subscription.displayName
        
        Write-ColorOutput "`nProcessing subscription: $subscriptionName ($subscriptionId)" "Yellow"
        
        # Get VMs in this subscription
        $vms = Get-AzureVMs -SubscriptionId $subscriptionId -ResourceGroup $ResourceGroup -Detailed:$Detailed
        
        if (-not $vms -or $vms.Count -eq 0) {
            Write-ColorOutput "No VMs found in subscription $subscriptionName" "Yellow"
            continue
        }
        
        Write-ColorOutput "Found $($vms.Count) VM(s) in subscription $subscriptionName" "Green"
        
        # Process each VM
        foreach ($vm in $vms) {
            $vmName = $vm.name
            $resourceGroup = $vm.resourceGroup
            
            # Skip if resource group filter is specified
            if ($ResourceGroup -and $resourceGroup -ne $ResourceGroup) {
                continue
            }
            
            $osInfo = $null
            if ($Detailed) {
                Write-ColorOutput "  Getting details for VM: $vmName" "Gray"
                $osInfo = Get-VMOSInfo -VM $vm
            }
            
            # Format VM information
            $vmInfo = Format-VMInfo -VM $vm -SubscriptionName $subscriptionName -OSInfo $osInfo
            $allVMsInfo += $vmInfo
        }
    }
    
    if (-not $allVMsInfo -or $allVMsInfo.Count -eq 0) {
        Write-ColorOutput "No VMs found matching the criteria." "Yellow"
        exit 0
    }
    
    # Print summary
    Show-VMSummary -VMsInfo $allVMsInfo
    
    # Print detailed information
    Show-VMDetails -VMsInfo $allVMsInfo -ShowTags:$ShowTags
    
    # Save to files if requested
    switch ($OutputFormat) {
        "JSON" {
            Save-VMsToJSON -VMsInfo $allVMsInfo -OutputFile $OutputFile
        }
        "CSV" {
            Save-VMsToCSV -VMsInfo $allVMsInfo -OutputFile $OutputFile
        }
        default {
            # Auto-save detailed information to JSON if detailed mode
            if ($Detailed) {
                Save-VMsToJSON -VMsInfo $allVMsInfo
            }
        }
    }
    
    Write-ColorOutput "`nScript completed successfully!" "Green"
    Write-ColorOutput "Generated using Azure CLI 2.74" "Gray"
}
catch {
    Write-ColorOutput "`nUnexpected error: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Full error details: $($_.Exception)" "Red"
    exit 1
}
