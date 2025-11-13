#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build and push EVE Incursions Companion Docker image

.DESCRIPTION
    Builds the Docker image for the EVE Incursions Companion Flask application and optionally pushes to Docker Hub.
    Supports both WSL2 and Windows environments.

.PARAMETER Login
    Authenticate with Docker Hub before building

.PARAMETER Push
    Push the image to Docker Hub after building

.EXAMPLE
    .\build-and-push.ps1
    Build the image locally

.EXAMPLE
    .\build-and-push.ps1 -Login -Push
    Login to Docker Hub, build, and push the image

.NOTES
    Author: Shaun Prince
    Last Modified: 2025-11-13
#>

[CmdletBinding()]
param(
    [Parameter(HelpMessage = "Login to Docker Hub before building")]
    [switch]$Login,

    [Parameter(HelpMessage = "Push image to Docker Hub after building")]
    [switch]$Push
)

#region Configuration
$ErrorActionPreference = "Stop"
$IMAGE_NAME = "suparious/eve-incursions"
$IMAGE_TAG = "latest"
$FULL_IMAGE = "${IMAGE_NAME}:${IMAGE_TAG}"

# Get script directory (cross-platform)
$SCRIPT_DIR = $PSScriptRoot
if ([string]::IsNullOrEmpty($SCRIPT_DIR)) {
    $SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# Convert to Unix-style path for Docker if in WSL
if ($IsLinux -or $env:WSL_DISTRO_NAME) {
    $BUILD_CONTEXT = $SCRIPT_DIR
} else {
    # Windows - Docker Desktop
    $BUILD_CONTEXT = $SCRIPT_DIR
}
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

function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Test-DockerHubAuth {
    try {
        $authCheck = docker info 2>&1 | Select-String "Username:"
        return $null -ne $authCheck
    } catch {
        return $false
    }
}
#endregion

#region Main Script
Write-Step "EVE Incursions Companion - Build and Push Script"
Write-Host "Image: $FULL_IMAGE"
Write-Host "Context: $BUILD_CONTEXT"

# Check Docker
if (-not (Test-DockerRunning)) {
    Write-Error "Docker is not running. Please start Docker and try again."
    exit 1
}
Write-Success "Docker is running"

# Login if requested
if ($Login) {
    Write-Step "Logging in to Docker Hub"
    docker login
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker Hub login failed"
        exit 1
    }
    Write-Success "Logged in to Docker Hub"
}

# Check authentication if push is requested
if ($Push -and -not (Test-DockerHubAuth)) {
    Write-Error "Not authenticated with Docker Hub. Use -Login flag to authenticate."
    exit 1
}

# Build image
Write-Step "Building Docker image: $FULL_IMAGE"
Write-Host "This may take several minutes..."

docker build -t $FULL_IMAGE $BUILD_CONTEXT

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed"
    exit 1
}
Write-Success "Docker image built successfully"

# Test image
Write-Step "Testing Docker image"
$testContainer = docker run --rm -d -p 5000:5000 $FULL_IMAGE
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start test container"
    exit 1
}

Start-Sleep -Seconds 3
docker stop $testContainer | Out-Null
Write-Success "Image test passed"

# Push if requested
if ($Push) {
    Write-Step "Pushing image to Docker Hub: $FULL_IMAGE"
    docker push $FULL_IMAGE

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker push failed"
        exit 1
    }
    Write-Success "Image pushed to Docker Hub"
}

# Summary
Write-Step "Build Summary"
Write-Host "Image: $FULL_IMAGE"
docker images $IMAGE_NAME --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

if ($Push) {
    Write-Success "`nImage available at: https://hub.docker.com/r/$IMAGE_NAME"
} else {
    Write-Host "`nTo push this image, run:" -ForegroundColor Yellow
    Write-Host "  .\build-and-push.ps1 -Login -Push" -ForegroundColor Yellow
}

Write-ColorOutput "`n✓ Build complete!" "Green"
#endregion
