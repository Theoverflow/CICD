#!/usr/bin/env python3
import os
import json
import subprocess
import yaml

def get_container_ids():
    """Run 'podman ps -q' to get a list of running container IDs."""
    result = subprocess.run(["podman", "ps", "-q"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error running podman ps")
        return []
    return result.stdout.strip().splitlines()

def inspect_container(container_id):
    """Run 'podman inspect' and return the parsed JSON for a container."""
    result = subprocess.run(["podman", "inspect", container_id], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error inspecting container {container_id}")
        return None
    data = json.loads(result.stdout)
    if data:
        return data[0]  # podman inspect returns a list
    return None

def extract_container_info(container_data):
    """
    Extract container name, container IP, and host SSH port.
    Assumes that port mappings appear in the 'NetworkSettings.Ports' dict,
    similar to Docker's output.
    """
    # Container name: remove leading '/' if present.
    container_name = container_data.get("Name", "").lstrip("/")
    
    # Network info: fallback to empty dict if not present.
    net = container_data.get("NetworkSettings", {})
    # Use the container's IP if available.
    container_ip = net.get("IPAddress", "")
    
    # Attempt to extract the host mapping for port 22/tcp.
    ssh_port = None
    ports = net.get("Ports", {})
    # Ports is expected to be a dict like: "22/tcp": [{"HostIp": "0.0.0.0", "HostPort": "2222"}]
    for port_proto, mappings in ports.items():
        if port_proto.startswith("22") and mappings:
            ssh_port = mappings[0].get("HostPort")
            break
    return container_name, container_ip, ssh_port

def generate_inventory():
    # Ensure directories exist
    os.makedirs("host_vars", exist_ok=True)
    os.makedirs("group_vars", exist_ok=True)
    
    # Discover running containers
    container_ids = get_container_ids()
    
    # Build inventory dictionary for --list output.
    inventory = {"_meta": {"hostvars": {}}}
    inventory["podman"] = {"hosts": []}
    
    for cid in container_ids:
        data = inspect_container(cid)
        if not data:
            continue
        name, ip, port = extract_container_info(data)
        if not name:
            name = cid[:12]
        # Use the container IP if available; otherwise, assume localhost.
        ansible_host = ip if ip else "localhost"
        host_vars = {
            "ansible_host": ansible_host,
            "ansible_port": int(port) if port else 22,
            "container_id": cid,
            "container_name": name
        }
        # Write host-specific variable file.
        host_file = os.path.join("host_vars", f"{name}.yml")
        with open(host_file, "w") as f:
            yaml.dump(host_vars, f, default_flow_style=False)
        print(f"Created host_vars file: {host_file}")
        
        # Add this host to our inventory.
        inventory["podman"]["hosts"].append(name)
        inventory["_meta"]["hostvars"][name] = host_vars

    # Define fixed filesystem values plus creative application environment variables.
    group_vars = {
        "filesystem_mount": "/mnt/podman",
        "backup_path": "/backup/podman",
        "log_path": "/var/log/podman",
        "app_environment": "podman",
        "debug_mode": False,
        "api_endpoint": "https://api.podman.example.com",
        "db_connection": "postgresql://podmanuser:podmanpass@dbserver/podmandb",
        "feature_toggle": {"experimental_ui": True, "auto_scale": False},
        "env_color": "purple"  # A creative color cue for Podman environments.
    }
    group_file = os.path.join("group_vars", "podman.yml")
    with open(group_file, "w") as f:
        yaml.dump(group_vars, f, default_flow_style=False)
    print(f"Created group_vars file: {group_file}")
    
    # Optionally, write the complete inventory as JSON for ansible-inventory --list.
    with open("inventory.json", "w") as f:
        json.dump(inventory, f, indent=2)
    print("Generated inventory.json")

if __name__ == "__main__":
    generate_inventory()

