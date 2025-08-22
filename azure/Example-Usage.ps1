#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Example usage of the List-AzureVMs.ps1 script.

.DESCRIPTION
    This script demonstrates various ways to use the List-AzureVMs.ps1 script
    with different parameters and scenarios.

.EXAMPLE
    .\Example-Usage.ps1
#>

Write-Host "Azure VM Lister - Example Usage" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check if the main script exists
if (-not (Test-Path ".\List-AzureVMs.ps1")) {
    Write-Host "Error: List-AzureVMs.ps1 not found in current directory." -ForegroundColor Red
    Write-Host "Please ensure you're running this from the same directory as List-AzureVMs.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Available examples:" -ForegroundColor Yellow
Write-Host "1. Basic VM listing (all subscriptions)" -ForegroundColor White
Write-Host "2. Detailed VM listing with OS information" -ForegroundColor White
Write-Host "3. List VMs with tags" -ForegroundColor White
Write-Host "4. Export to JSON format" -ForegroundColor White
Write-Host "5. Export to CSV format" -ForegroundColor White
Write-Host "6. Filter by specific subscription" -ForegroundColor White
Write-Host "7. Filter by resource group" -ForegroundColor White
Write-Host "8. Run all examples" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-8) or press Enter to exit"

switch ($choice) {
    "1" {
        Write-Host "`nRunning: Basic VM listing..." -ForegroundColor Green
        .\List-AzureVMs.ps1
    }
    "2" {
        Write-Host "`nRunning: Detailed VM listing with OS information..." -ForegroundColor Green
        .\List-AzureVMs.ps1 -Detailed
    }
    "3" {
        Write-Host "`nRunning: List VMs with tags..." -ForegroundColor Green
        .\List-AzureVMs.ps1 -ShowTags
    }
    "4" {
        Write-Host "`nRunning: Export to JSON format..." -ForegroundColor Green
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        .\List-AzureVMs.ps1 -OutputFormat JSON -OutputFile "example_output_$timestamp.json"
    }
    "5" {
        Write-Host "`nRunning: Export to CSV format..." -ForegroundColor Green
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        .\List-AzureVMs.ps1 -OutputFormat CSV -OutputFile "example_output_$timestamp.csv"
    }
    "6" {
        Write-Host "`nRunning: Filter by specific subscription..." -ForegroundColor Green
        $subscriptionId = Read-Host "Enter subscription ID (or press Enter to skip)"
        if ($subscriptionId) {
            .\List-AzureVMs.ps1 -SubscriptionId $subscriptionId
        } else {
            Write-Host "Skipping subscription filter example." -ForegroundColor Yellow
        }
    }
    "7" {
        Write-Host "`nRunning: Filter by resource group..." -ForegroundColor Green
        $resourceGroup = Read-Host "Enter resource group name (or press Enter to skip)"
        if ($resourceGroup) {
            .\List-AzureVMs.ps1 -ResourceGroup $resourceGroup
        } else {
            Write-Host "Skipping resource group filter example." -ForegroundColor Yellow
        }
    }
    "8" {
        Write-Host "`nRunning all examples..." -ForegroundColor Green
        
        # Example 1: Basic listing
        Write-Host "`n=== Example 1: Basic VM listing ===" -ForegroundColor Cyan
        .\List-AzureVMs.ps1
        
        # Example 2: Detailed listing
        Write-Host "`n=== Example 2: Detailed VM listing ===" -ForegroundColor Cyan
        .\List-AzureVMs.ps1 -Detailed
        
        # Example 3: With tags
        Write-Host "`n=== Example 3: List VMs with tags ===" -ForegroundColor Cyan
        .\List-AzureVMs.ps1 -ShowTags
        
        # Example 4: JSON export
        Write-Host "`n=== Example 4: Export to JSON ===" -ForegroundColor Cyan
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        .\List-AzureVMs.ps1 -OutputFormat JSON -OutputFile "all_examples_$timestamp.json"
        
        # Example 5: CSV export
        Write-Host "`n=== Example 5: Export to CSV ===" -ForegroundColor Cyan
        .\List-AzureVMs.ps1 -OutputFormat CSV -OutputFile "all_examples_$timestamp.csv"
        
        Write-Host "`nAll examples completed!" -ForegroundColor Green
    }
    default {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "`nExample completed!" -ForegroundColor Green
