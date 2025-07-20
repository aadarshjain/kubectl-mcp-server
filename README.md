# Kubectl MCP Server

A Model Context Protocol (MCP) server for Kubernetes cluster management and information gathering using kubectl commands and the Kubernetes Python client.

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Running the Server](#running-the-server)
  - [Basic Usage](#basic-usage)
- [Available Tools](#available-tools)
- [Configuration](#configuration)
  - [Kubeconfig Setup](#kubeconfig-setup)
  - [Claude Desktop Configuration](#claude-desktop-configuration)
- [Security](#security)
- [Example Usage](#example-usage)
- [Troubleshooting](#troubleshooting)

## Overview

This MCP server provides a seamless interface between LLMs (like Claude) and Kubernetes clusters. It enables natural language interactions with your Kubernetes resources without manually running kubectl commands or writing complex API calls. The server supports both read-only operations for safe information gathering and full kubectl command execution when needed.

## Project Structure

```
kubectl-mcp-server/
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies
└── server.py                  # Main server application with FastMCP setup
```

## Features

- **Cluster Management**: List and switch between different Kubernetes contexts
- **Read-only Operations**: Safe kubectl commands for information gathering (get, describe, explain)
- **Full kubectl Support**: Execute any kubectl command when needed
- **Kubernetes API Integration**: Direct access to Kubernetes APIs through Python client
- **Context Switching**: Seamlessly switch between different cluster contexts
- **Safety Controls**: Built-in protection against destructive operations in read-only mode

## Installation

### Prerequisites

For local development and testing, you'll need:

#### System Requirements
- **Python 3.8+** - The MCP server is built with Python
- **kubectl** - Kubernetes command-line tool installed and configured
- **Kubernetes cluster access** - Valid kubeconfig with cluster credentials

#### Optional (for Claude Desktop integration)
- **Claude Desktop** application installed
- **Node.js and npm** (if using npx for mcp-remote)

### Setup

1. Clone and navigate to the project:
   ```bash
   git clone <repository-url>
   cd kubectl-mcp-server
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure kubectl is installed and configured:
   ```bash
   kubectl version --client
   kubectl config get-contexts
   ```

## Running the Server

### Basic Usage

```bash
# Run with defaults
python server.py

# Run with debug logging
python server.py --log-level debug
```

## Available Tools

### 1. `list_clusters()`
Lists all available Kubernetes clusters from your kubeconfig file.

**Returns:**
- List of available clusters with names and cluster information
- Currently active context

**Example:**
```json
{
  "clusters": [
    {"name": "prod-cluster", "cluster": "prod-k8s"},
    {"name": "dev-cluster", "cluster": "dev-k8s"}
  ],
  "active_context": "prod-cluster"
}
```

### 2. `switch_context(context: str)`
Switches to a different Kubernetes context.

**Parameters:**
- `context` (string): Name of the context to switch to

**Returns:**
- Success message or error details

**Example:**
```python
switch_context("dev-cluster")
# Returns: {"message": "Switched to context: dev-cluster"}
```

### 3. `run_kubectl_command_ro(command: str)`
Executes read-only kubectl commands safely.

**Parameters:**
- `command` (string): kubectl command starting with "kubectl"

**Allowed Operations:**
- `get` - Retrieve resources
- `describe` - Show detailed resource information
- `explain` - Show resource documentation
- `config view` - View kubeconfig
- `config get-contexts` - List available contexts
- `version` - Show kubectl/cluster version
- `api-resources` - List available API resources
- `cluster-info` - Show cluster information

**Returns:**
- Command output or error message

**Example:**
```bash
run_kubectl_command_ro("kubectl get pods -n default")
```

### 4. `run_kubectl_command(command: str)`
Executes any kubectl command (use with caution).

**Parameters:**
- `command` (string): kubectl command starting with "kubectl"

**Returns:**
- Command output or error message

**Warning:** This tool can execute destructive operations. Use `run_kubectl_command_ro()` for safe information gathering.

## Configuration

### Kubeconfig Setup

Ensure your kubeconfig is properly configured:

```bash
# Check current context
kubectl config current-context

# List all contexts
kubectl config get-contexts

# Set default context
kubectl config use-context <context-name>
```

The server will automatically load from the default kubeconfig location (`~/.kube/config`) or from the `KUBECONFIG` environment variable.

### Claude Desktop Configuration

To integrate with Claude Desktop, add this configuration to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "kubectl-mcp-server": {
      "command": "/full/path/to/python",
      "args": ["/path/to/kubectl-mcp-server/server.py"]
    }
  }
}
```

Config file locations:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

## Security

### Read-only Mode
The `run_kubectl_command_ro()` tool provides safe access by:
- Allowing only information-gathering commands
- Blocking destructive operations (delete, update, patch, etc.)
- Preventing resource modifications

### Access Control
- Server inherits permissions from your kubeconfig
- No additional authentication layer (relies on Kubernetes RBAC)
- Commands execute with the same privileges as your kubectl setup

### Best Practices
- Use `run_kubectl_command_ro()` for general queries
- Reserve `run_kubectl_command()` for trusted operations only
- Regularly audit your kubeconfig permissions
- Consider using dedicated service accounts with limited permissions

## Example Usage

### Basic Cluster Information
```
User: What clusters do I have access to?
Claude: [Uses list_clusters() to show available contexts]

User: Switch to the development cluster
Claude: [Uses switch_context("dev-cluster")]

User: Show me all pods in the default namespace
Claude: [Uses run_kubectl_command_ro("kubectl get pods -n default")]
```

### Resource Inspection
```
User: Describe the nginx deployment
Claude: [Uses run_kubectl_command_ro("kubectl describe deployment nginx")]

User: What's the current cluster version?
Claude: [Uses run_kubectl_command_ro("kubectl version")]

User: Show me all namespaces
Claude: [Uses run_kubectl_command_ro("kubectl get namespaces")]
```

### Advanced Operations
```
User: Scale the nginx deployment to 3 replicas
Claude: [Uses run_kubectl_command("kubectl scale deployment nginx --replicas=3")]
```

## Troubleshooting

### Common Issues

**Connection Problems:**
- Verify kubectl connectivity: `kubectl cluster-info`
- Check kubeconfig: `kubectl config view`
- Ensure proper authentication to your clusters

**Permission Errors:**
- Check RBAC permissions in your cluster
- Verify service account has necessary permissions
- Review kubeconfig user credentials

**Context Switching Issues:**
- List available contexts: `kubectl config get-contexts`
- Verify context names match exactly
- Check if context exists in kubeconfig

**Import Errors:**
- Install required dependencies: `pip install -r requirements.txt`
- Verify Python version compatibility (3.8+)
- Check kubectl installation: `kubectl version --client`
