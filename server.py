from kubernetes import client, config
# from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP
import logging
import subprocess
import os

mcp = FastMCP("Kubernetes MCP server")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global API clients that will be reinitialized when context changes
coreV1 = None
appsV1 = None
batchV1 = None
networkingV1 = None
customObjectsApi = None

def initialize_clients():
    """Initialize or reinitialize all Kubernetes API clients."""
    global coreV1, appsV1, batchV1, networkingV1, customObjectsApi
    
    # Create API clients
    coreV1 = client.CoreV1Api()
    appsV1 = client.AppsV1Api()
    batchV1 = client.BatchV1Api()
    networkingV1 = client.NetworkingV1Api()
    customObjectsApi = client.CustomObjectsApi()
    
    logger.info("Kubernetes API clients initialized")

# Load initial kubeconfig (usually from ~/.kube/config)
config.load_kube_config()

@mcp.tool()
def list_clusters():
    """
    List all available Kubernetes clusters and contexts from your kubeconfig file.
    
    This tool retrieves all configured Kubernetes contexts from your kubeconfig file,
    showing both the context names and their associated cluster information. It also
    indicates which context is currently active.
    
    Returns:
        dict: A dictionary containing:
            - clusters: List of dictionaries with 'name' and 'cluster' keys
            - active_context: String name of the currently active context
            - error: Error message if the operation fails
    
    Example:
        Returns: {
            "clusters": [
                {"name": "prod-cluster", "cluster": "prod-k8s"},
                {"name": "dev-cluster", "cluster": "dev-k8s"}
            ],
            "active_context": "prod-cluster"
        }
    """
    try:
        contexts, active_context = config.list_kube_config_contexts()
        clusters = [{"name": context['name'], "cluster": context['context']['cluster']} for context in contexts]
        return {"clusters": clusters, "active_context": active_context['name']}
    except Exception as e:
        logger.error(f"Error listing clusters: {e}")
        return {"error": str(e)}

@mcp.tool()
def switch_context(context: str):
    """
    Switch the active Kubernetes context to connect to a different cluster.
    
    This tool changes the current Kubernetes context to the specified one, allowing
    you to switch between different clusters or namespaces. After switching, all
    subsequent kubectl commands and API calls will be directed to the new context.
    The Kubernetes API clients are automatically reinitialized for the new context.
    
    Args:
        context (str): The name of the context to switch to. Must be a valid context
                      name from your kubeconfig file. Use list_clusters() to see
                      available contexts.
    
    Returns:
        dict: A dictionary containing:
            - message: Success message if context switch was successful
            - error: Error message if the context switch failed
    
    Example:
        Input: "dev-cluster"
        Returns: {"message": "Switched to context: dev-cluster"}
    """
    try:
        config.load_kube_config(context=context)
        initialize_clients()  # Reinitialize clients with new context
        return {"message": f"Switched to context: {context}"}
    except Exception as e:
        logger.error(f"Error switching context to {context}: {e}")
        return {"error": str(e)}
    
@mcp.tool()
def run_kubectl_command(command: str):
    """
    Execute any kubectl command with full privileges (use with caution).
    
    This tool allows execution of any kubectl command, including potentially
    destructive operations like delete, update, patch, apply, etc. It provides
    complete access to your Kubernetes cluster with the same permissions as
    your kubectl configuration.
    
    WARNING: This tool can perform destructive operations. Use run_kubectl_command_ro()
    for safe, read-only operations when you only need to gather information.
    
    Args:
        command (str): The complete kubectl command to execute. Must start with "kubectl".
                      Examples: "kubectl delete pod nginx", "kubectl apply -f config.yaml"
    
    Returns:
        str: The stdout output from the kubectl command, or an error message if the
             command fails or doesn't start with "kubectl".
    
    Example:
        Input: "kubectl scale deployment nginx --replicas=3"
        Returns: "deployment.apps/nginx scaled"
    """
    try:
        # Check if command starts with kubectl
        if not command.startswith("kubectl "):
            return "Error: Command must start with 'kubectl'"
        
        # Execute the full command as provided
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running kubectl command: {e.stderr}")
        return f"Error: {e.stderr}"

@mcp.tool()
def run_kubectl_command_ro(command: str):
    """
    Execute read-only kubectl commands safely for information gathering.
    
    This tool provides a safe way to run kubectl commands that only read information
    from your Kubernetes cluster without making any modifications. It blocks potentially
    destructive operations and only allows commands that gather information.
    
    Allowed operations:
    - get: Retrieve resources (pods, deployments, services, etc.)
    - describe: Show detailed information about resources
    - explain: Show documentation for resource types
    - config view: View kubeconfig settings
    - config get-contexts: List available contexts
    - version: Show kubectl and cluster version information
    - api-resources: List available API resources
    - cluster-info: Show cluster information
    
    Blocked operations include: delete, update, patch, apply, create, replace, edit,
    scale, cordon, drain, taint, and any command with --overwrite flags.
    
    Args:
        command (str): The kubectl command to execute. Must start with "kubectl" and
                      be a read-only operation. Examples: "kubectl get pods",
                      "kubectl describe deployment nginx"
    
    Returns:
        str: The stdout output from the kubectl command, or an error message if the
             command fails, doesn't start with "kubectl", or contains disallowed operations.
    
    Example:
        Input: "kubectl get pods -n default"
        Returns: "NAME    READY   STATUS    RESTARTS   AGE\nnginx   1/1     Running   0          2d"
    """
    try:
        # Check if command starts with kubectl
        if not command.startswith("kubectl "):
            return "Error: Command must start with 'kubectl'"
        
        # Extract the actual kubectl subcommand (after "kubectl ")
        kubectl_subcommand = command[8:]  # Remove "kubectl " prefix
        
        # List of allowed command prefixes (read-only operations)
        allowed_prefixes = ["get", "describe", "explain", 
                            "config view", "config get-contexts",
                            "version", "api-resources", "cluster-info"]
        
        # List of disallowed terms that might modify resources
        disallowed_terms = ["delete", "update", "patch", "apply", "create", 
                           "replace", "edit", "scale", "cordon", "drain", 
                           "taint", "label --overwrite", "annotate --overwrite"]
        
        # Check if command is allowed
        is_allowed = any(kubectl_subcommand.startswith(prefix) for prefix in allowed_prefixes)
        has_disallowed = any(term in kubectl_subcommand for term in disallowed_terms)
        
        if not is_allowed or has_disallowed:
            return "Error: Only read-only kubectl commands are allowed (get, describe, etc.)"

        # Execute the full command as provided
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running kubectl command: {e.stderr}")
        return f"Error: {e.stderr}"
    
# main entry point to run the MCP server

if __name__ == '__main__':
    logger.info("Starting Kubernetes MCP.")
    mcp.run()
