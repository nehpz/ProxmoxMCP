# Available MCP Tools in ProxmoxMCP

## Node Management

### get_nodes
- **Purpose**: Lists all nodes in the Proxmox cluster
- **Parameters**: None
- **Returns**: Formatted list of nodes with status, uptime, CPU, memory info

### get_node_status
- **Purpose**: Get detailed status of a specific node
- **Parameters**: 
  - `node` (string, required): Name of the node
- **Returns**: Detailed node information including CPU, memory, network, temperature

## VM Management

### get_vms
- **Purpose**: List all VMs across the cluster
- **Parameters**: None
- **Returns**: List of VMs with status, node, CPU, memory information

### execute_vm_command
- **Purpose**: Execute a command in a VM's console using QEMU Guest Agent
- **Parameters**:
  - `node` (string, required): Node where VM is running
  - `vmid` (string, required): VM ID
  - `command` (string, required): Command to execute
- **Returns**: Command output and execution status
- **Requirements**: VM must be running with QEMU Guest Agent installed

### start_vm
- **Purpose**: Start a stopped VM
- **Parameters**:
  - `node` (string, required): Node name
  - `vmid` (string, required): VM ID

### stop_vm
- **Purpose**: Force stop a VM (immediate)
- **Parameters**:
  - `node` (string, required): Node name
  - `vmid` (string, required): VM ID

### shutdown_vm
- **Purpose**: Gracefully shutdown a VM
- **Parameters**:
  - `node` (string, required): Node name
  - `vmid` (string, required): VM ID

### restart_vm
- **Purpose**: Restart a VM
- **Parameters**:
  - `node` (string, required): Node name
  - `vmid` (string, required): VM ID

### create_vm
- **Purpose**: Create a new VM
- **Parameters**: Various VM configuration parameters

### delete_vm
- **Purpose**: Delete a VM
- **Parameters**:
  - `node` (string, required): Node name
  - `vmid` (string, required): VM ID

## Container Management

### get_containers
- **Purpose**: List all containers across the cluster
- **Parameters**: None
- **Returns**: List of containers with status information

## Storage Management

### get_storage
- **Purpose**: List available storage pools
- **Parameters**: None
- **Returns**: Storage pools with type, usage, IOPS information

## Cluster Management

### get_cluster_status
- **Purpose**: Get overall cluster status
- **Parameters**: None
- **Returns**: Cluster health, quorum, nodes, resources, workload information

## Tool Implementation Pattern
All tools:
- Inherit from `ProxmoxTool` base class
- Use Proxmox API via `ProxmoxManager`
- Return formatted responses using templates
- Include error handling and logging
- Support both sync and async operation