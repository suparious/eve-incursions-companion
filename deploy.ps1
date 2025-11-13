#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy EVE Incursions Companion to Kubernetes

.DESCRIPTION
    Deploys the EVE Incursions Companion Flask application to the srt-hq-k8s cluster.
    Optionally builds and pushes the Docker image before deployment.

.PARAMETER Build
    Build the Docker image before deploying

.PARAMETER Push
    Push the Docker image to Docker Hub before deploying (implies -Build)

.PARAMETER Uninstall
    Remove the deployment from Kubernetes

.EXAMPLE
    .\deploy.ps1
    Deploy using existing image from Docker Hub

.EXAMPLE
    .\deploy.ps1 -Build -Push
    Build, push, and deploy the application

.EXAMPLE
    .\deploy.ps1 -Uninstall
    Remove the deployment from Kubernetes

.NOTES
    Author: Shaun Prince
    Last Modified: 2025-11-13
    Requires: kubectl, Docker (if building)
#>

[CmdletBinding()]
param(
    [Parameter(HelpMessage = "Build Docker image before deploying")]
    [switch]$Build,

    [Parameter(HelpMessage = "Push Docker image before deploying")]
    [switch]$Push,

    [Parameter(HelpMessage = "Uninstall deployment from Kubernetes")]
    [switch]$Uninstall
)

#region Configuration
$ErrorActionPreference = "Stop"
$NAMESPACE = "eve-incursions"
$APP_NAME = "eve-incursions"
$DEPLOYMENT_NAME = "eve-incursions"

# Get script directory
$SCRIPT_DIR = $PSScriptRoot
if ([string]::IsNullOrEmpty($SCRIPT_DIR)) {
    $SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$K8S_DIR = Join-Path $SCRIPT_DIR "k8s"
#endregion

#region Functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "`n==> $Message" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✓ $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "✗ $Message" "Red"
}

function Test-KubectlAvailable {
    try {
        kubectl version --client --output=json | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Wait-ForRollout {
    param(
        [string]$Namespace,
        [string]$DeploymentName,
        [int]$TimeoutSeconds = 300
    )

    Write-Step "Waiting for rollout to complete (timeout: ${TimeoutSeconds}s)"
    try {
        kubectl rollout status deployment/$DeploymentName -n $Namespace --timeout="${TimeoutSeconds}s"
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Get-DeploymentStatus {
    param(
        [string]$Namespace,
        [string]$AppName
    )

    Write-Step "Deployment Status"

    # Pods
    Write-Host "`nPods:" -ForegroundColor Yellow
    kubectl get pods -n $Namespace -l app=$AppName

    # Service
    Write-Host "`nService:" -ForegroundColor Yellow
    kubectl get service -n $Namespace $AppName

    # Ingress
    Write-Host "`nIngress:" -ForegroundColor Yellow
    kubectl get ingress -n $Namespace $AppName

    # Certificate
    Write-Host "`nCertificate:" -ForegroundColor Yellow
    kubectl get certificate -n $Namespace -l app=$AppName 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "No certificates found (may take 1-2 minutes to appear)" -ForegroundColor Gray
    }
}
#endregion

#region Main Script
Write-Step "EVE Incursions Companion - Kubernetes Deployment"

# Check kubectl
if (-not (Test-KubectlAvailable)) {
    Write-Error "kubectl is not available. Please install kubectl and try again."
    exit 1
}
Write-Success "kubectl is available"

# Uninstall if requested
if ($Uninstall) {
    Write-Step "Uninstalling EVE Incursions Companion"

    if (Test-Path $K8S_DIR) {
        kubectl delete -f $K8S_DIR --ignore-not-found=true
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Uninstall complete"
        } else {
            Write-Error "Uninstall failed"
            exit 1
        }
    } else {
        Write-Error "K8s directory not found: $K8S_DIR"
        exit 1
    }

    exit 0
}

# Build if requested
if ($Build -or $Push) {
    Write-Step "Building Docker image"

    $buildScript = Join-Path $SCRIPT_DIR "build-and-push.ps1"
    if (-not (Test-Path $buildScript)) {
        Write-Error "Build script not found: $buildScript"
        exit 1
    }

    if ($Push) {
        & $buildScript -Push
    } else {
        & $buildScript
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed"
        exit 1
    }
    Write-Success "Build complete"
}

# Deploy to Kubernetes
Write-Step "Deploying to Kubernetes"

if (-not (Test-Path $K8S_DIR)) {
    Write-Error "K8s directory not found: $K8S_DIR"
    exit 1
}

# Apply manifests
kubectl apply -f $K8S_DIR

if ($LASTEXITCODE -ne 0) {
    Write-Error "Deployment failed"
    exit 1
}
Write-Success "Manifests applied"

# Wait for rollout
if (Wait-ForRollout -Namespace $NAMESPACE -DeploymentName $DEPLOYMENT_NAME) {
    Write-Success "Rollout complete"
} else {
    Write-Error "Rollout failed or timed out"
    Get-DeploymentStatus -Namespace $NAMESPACE -AppName $APP_NAME
    exit 1
}

# Show status
Get-DeploymentStatus -Namespace $NAMESPACE -AppName $APP_NAME

# Summary
Write-Step "Deployment Summary"
Write-Success "EVE Incursions Companion deployed successfully!"
Write-Host "`nAccess the application at:" -ForegroundColor Yellow
Write-Host "  https://eve-incursions.lab.hq.solidrust.net" -ForegroundColor Cyan

Write-Host "`nUseful commands:" -ForegroundColor Yellow
Write-Host "  View logs:       kubectl logs -n $NAMESPACE -l app=$APP_NAME -f"
Write-Host "  View pods:       kubectl get pods -n $NAMESPACE"
Write-Host "  View events:     kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'"
Write-Host "  Shell access:    kubectl exec -n $NAMESPACE -it <pod-name> -- /bin/bash"
Write-Host "  Uninstall:       .\deploy.ps1 -Uninstall"

Write-Host "`nNote: Certificate provisioning may take 1-2 minutes." -ForegroundColor Gray
Write-Host "      Check status: kubectl get certificate -n $NAMESPACE" -ForegroundColor Gray

Write-ColorOutput "`n✓ Deployment complete!" "Green"
#endregion
