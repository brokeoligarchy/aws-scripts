#!/usr/bin/env pwsh
<#
.SYNOPSIS
    List all Azure VMs from all subscriptions with their operating system information.

.DESCRIPTION
    This script connects to Azure, retrieves all subscriptions, and lists all VMs
    with detailed information including operating system details, power state,
    and other relevant information.

.PARAMETER SubscriptionId
    Optional. Specific subscription ID to analyze.

.PARAMETER ResourceGroup
    Optional. Specific resource group to analyze.

.PARAMETER Detailed
    Optional. Get detailed VM information.

.PARAMETER ShowTags
    Optional. Include VM tags in the output.

.PARAMETER OutputFormat
    Optional. Output format: Console, JSON, CSV, or Text. Default is Console.

.PARAMETER OutputFile
    Optional. Output file path.

.EXAMPLE
    .\List-AzureVMs.ps1

.EXAMPLE
    .\List-AzureVMs.ps1 -SubscriptionId "12345678-1234-1234-1234-123456789012" -Detailed

.EXAMPLE
    .\List-AzureVMs.ps1 -OutputFormat JSON -OutputFile "my_vms.json"

.NOTES
    Requires Azure PowerShell module to be installed and user to be authenticated.
    Install with: Install-Module -Name Az -AllowClobber -Force
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
    [string]$OutputFile
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# Function to check Azure PowerShell module
function Test-AzureModule {
    try {
        $azModule = Get-Module -Name Az -ListAvailable
        if ($azModule) {
            Write-ColorOutput "✓ Azure PowerShell module found" "Green"
            return $true
        } else {
            Write-ColorOutput "✗ Azure PowerShell module not found" "Red"
            Write-ColorOutput "Please install with: Install-Module -Name Az -AllowClobber -Force" "Yellow"
            return $false
        }
    }
    catch {
        Write-ColorOutput "✗ Error checking Azure PowerShell module: $($_.Exception.Message)" "Red"
        return $false
    }
}

# Function to check Azure authentication
function Test-AzureConnection {
    try {
        $context = Get-AzContext
        if ($context) {
            Write-ColorOutput "✓ Connected to Azure as: $($context.Account.Id)" "Green"
            return $true
        } else {
            Write-ColorOutput "✗ Not connected to Azure" "Red"
            Write-ColorOutput "Please run: Connect-AzAccount" "Yellow"
            return $false
        }
    }
    catch {
        Write-ColorOutput "✗ Error checking Azure connection: $($_.Exception.Message)" "Red"
        return $false
    }
}

# Function to get OS information from VM
function Get-VMOSInfo {
    param([Microsoft.Azure.Commands.Compute.Models.PSVirtualMachine]$VM)
    
    $osInfo = @{
        OSType = "Unknown"
        OSName = "Unknown"
        OSVersion = "Unknown"
        OSDiskSizeGB = "Unknown"
    }
    
    try {
        # Get OS type
        if ($VM.OSProfile.LinuxConfiguration) {
            $osInfo.OSType = "Linux"
        } elseif ($VM.OSProfile.WindowsConfiguration) {
            $osInfo.OSType = "Windows"
        }
        
        # Get OS disk information
        if ($VM.StorageProfile.OSDisk) {
            $osDisk = $VM.StorageProfile.OSDisk
            if ($osDisk.DiskSizeGB) {
                $osInfo.OSDiskSizeGB = $osDisk.DiskSizeGB
            }
            
            # Try to get OS name from image reference
            if ($osDisk.ImageReference) {
                $imageRef = $osDisk.ImageReference
                if ($imageRef.Offer -and $imageRef.Sku) {
                    $osInfo.OSName = "$($imageRef.Offer) $($imageRef.Sku)"
                } elseif ($imageRef.Publisher -and $imageRef.Offer) {
                    $osInfo.OSName = "$($imageRef.Publisher) $($imageRef.Offer)"
                }
            }
        }
        
        # Try to get OS name from VM tags
        if ($VM.Tags) {
            foreach ($tag in $VM.Tags.GetEnumerator()) {
                if ($tag.Key -like "*os*" -or $tag.Key -like "*system*") {
                    $osInfo.OSName = $tag.Value
                    break
                }
            }
        }
    }
    catch {
        Write-Warning "Error extracting OS info for VM $($VM.Name): $($_.Exception.Message)"
    }
    
    return $osInfo
}

# Function to format VM information
function Format-VMInfo {
    param(
        [Microsoft.Azure.Commands.Compute.Models.PSVirtualMachine]$VM,
        [string]$SubscriptionName,
        [hashtable]$OSInfo
    )
    
    $vmInfo = @{
        Name = $VM.Name
        ResourceGroup = $VM.ResourceGroupName
        Location = $VM.Location
        Subscription = $SubscriptionName
        SubscriptionId = $VM.Id.Split('/')[2]
        VMSize = $VM.HardwareProfile.VMSize
        PowerState = "Unknown"
        OSType = "Unknown"
        OSName = "Unknown"
        OSVersion = "Unknown"
        OSDiskSizeGB = "Unknown"
        NetworkInterfaces = 0
        Tags = @{}
    }
    
    # Get power state
    try {
        $powerState = Get-AzVM -ResourceGroupName $VM.ResourceGroupName -Name $VM.Name -Status
        if ($powerState.Statuses) {
            $vmInfo.PowerState = ($powerState.Statuses | Where-Object { $_.Code -like "PowerState/*" }).DisplayStatus
        }
    }
    catch {
        Write-Warning "Could not get power state for VM $($VM.Name)"
    }
    
    # Get OS information
    if ($OSInfo) {
        $vmInfo.OSType = $OSInfo.OSType
        $vmInfo.OSName = $OSInfo.OSName
        $vmInfo.OSVersion = $OSInfo.OSVersion
        $vmInfo.OSDiskSizeGB = $OSInfo.OSDiskSizeGB
    }
    
    # Get network interface count
    if ($VM.NetworkProfile.NetworkInterfaces) {
        $vmInfo.NetworkInterfaces = $VM.NetworkProfile.NetworkInterfaces.Count
    }
    
    # Get tags
    if ($VM.Tags) {
        foreach ($tag in $VM.Tags.GetEnumerator()) {
            $vmInfo.Tags[$tag.Key] = $tag.Value
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
    Write-ColorOutput "AZURE VMs SUMMARY" "Cyan"
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
        $OutputFile = "azure_vms_$timestamp.json"
    }
    
    try {
        $outputData = @{
            GeneratedAt = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
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
        $OutputFile = "azure_vms_$timestamp.csv"
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
    Write-ColorOutput "Azure VM Lister (PowerShell)" "Cyan"
    Write-ColorOutput "=" * 60 "Cyan"
    
    # Check Azure PowerShell module
    if (-not (Test-AzureModule)) {
        exit 1
    }
    
    # Check Azure connection
    if (-not (Test-AzureConnection)) {
        exit 1
    }
    
    # Get subscriptions
    Write-ColorOutput "Getting subscriptions..." "White"
    if ($SubscriptionId) {
        $subscriptions = Get-AzSubscription -SubscriptionId $SubscriptionId -ErrorAction SilentlyContinue
        if (-not $subscriptions) {
            Write-ColorOutput "Subscription $SubscriptionId not found or not accessible." "Red"
            exit 1
        }
    } else {
        $subscriptions = Get-AzSubscription -ErrorAction SilentlyContinue
    }
    
    if (-not $subscriptions) {
        Write-ColorOutput "No subscriptions found or accessible." "Red"
        exit 1
    }
    
    Write-ColorOutput "Found $($subscriptions.Count) subscription(s)" "Green"
    
    $allVMsInfo = @()
    
    # Process each subscription
    foreach ($subscription in $subscriptions) {
        $subscriptionId = $subscription.Id
        $subscriptionName = $subscription.Name
        
        Write-ColorOutput "`nProcessing subscription: $subscriptionName ($subscriptionId)" "Yellow"
        
        # Set context to current subscription
        Set-AzContext -SubscriptionId $subscriptionId -ErrorAction SilentlyContinue | Out-Null
        
        # Get VMs in this subscription
        $vmParams = @{}
        if ($ResourceGroup) {
            $vmParams.ResourceGroupName = $ResourceGroup
        }
        
        $vms = Get-AzVM @vmParams -ErrorAction SilentlyContinue
        
        if (-not $vms) {
            Write-ColorOutput "No VMs found in subscription $subscriptionName" "Yellow"
            continue
        }
        
        Write-ColorOutput "Found $($vms.Count) VM(s) in subscription $subscriptionName" "Green"
        
        # Process each VM
        foreach ($vm in $vms) {
            $vmName = $vm.Name
            $resourceGroup = $vm.ResourceGroupName
            
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
}
catch {
    Write-ColorOutput "`nUnexpected error: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Full error details: $($_.Exception)" "Red"
    exit 1
}
