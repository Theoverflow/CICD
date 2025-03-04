#!/usr/bin/env python3
import os
import json
import random
import subprocess
import yaml

# List of available environments
environments = ["dev", "staging", "production"]

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
    return data[0] if data else None

def extract_container_info(container_data):
    """
    Extract container name, container IP, and host SSH port.
    Assumes port mappings appear in 'NetworkSettings.Ports' similar to Docker's output.
    """
    # Use container's name (strip leading '/')
    container_name = container_data.get("Name", "").lstrip("/")
    # Try to get the container IP from NetworkSettings (if available)
    net = container_data.get("NetworkSettings", {})
    container_ip = net.get("IPAddress", "")
    # Default SSH port if no mapping is found
    ssh_port = None
    ports = net.get("Ports", {})
    for port_proto, mappings in ports.items():
        if port_proto.startswith("22") and mappings:
            ssh_port = mappings[0].get("HostPort")
            break
    return container_name, container_ip, ssh_port

def generate_inventory():
    # Ensure directories exist
    os.makedirs("host_vars", exist_ok=True)
    os.makedirs("group_vars", exist_ok=True)

    # Prepare a dictionary for environment groups (to be placed under "all: children:")
    groups = {env: {"hosts": []} for env in environments}

    # Discover containers
    container_ids = get_container_ids()
    if not container_ids:
        print("No running containers found.")
        return

    # Process each container
    for cid in container_ids:
        data = inspect_container(cid)
        if not data:
            continue
        name, ip, port = extract_container_info(data)
        if not name:
            name = cid[:12]
        # Randomly assign an environment to this container
        assigned_env = random.choice(environments)
        # Use container's IP if available; otherwise fallback to localhost
        ansible_host = ip if ip else "localhost"
        host_vars = {
            "ansible_host": ansible_host,
            "ansible_port": int(port) if port else 22,
            "container_id": cid,
            "container_name": name,
            "env_assigned": assigned_env  # Assigned environment
        }
        # Write host-specific variable file in host_vars/
        host_file = os.path.join("host_vars", f"{name}.yml")
        with open(host_file, "w") as f:
            yaml.dump(host_vars, f, default_flow_style=False)
        print(f"Created host_vars file: {host_file}")

        # Add host to its assigned environment group
        groups[assigned_env]["hosts"].append(name)

    # Define creative group variables for each environment.
    group_vars_definitions = {
        "dev": {
            "filesystem_mount": "/mnt/dev",
            "backup_path": "/backup/dev",
            "log_path": "/var/log/dev",
            "app_environment": "development",
            "debug_mode": True,
            "api_endpoint": "https://api-dev.example.com",
            "db_connection": "postgresql://devuser:devpass@localhost/devdb",
            "feature_toggle": {"new_ui": True, "beta_features": True},
            "env_color": "blue",
            "custom_message": "Welcome to the DEV playground!"
        },
        "staging": {
            "filesystem_mount": "/mnt/staging",
            "backup_path": "/backup/staging",
            "log_path": "/var/log/staging",
            "app_environment": "staging",
            "debug_mode": True,
            "api_endpoint": "https://api-staging.example.com",
            "db_connection": "postgresql://staginguser:stagingpass@staginghost/stagingdb",
            "feature_toggle": {"new_ui": False, "beta_features": True},
            "env_color": "orange",
            "custom_message": "Staging: Test before production!"
        },
        "production": {
            "filesystem_mount": "/mnt/prod",
            "backup_path": "/backup/prod",
            "log_path": "/var/log/prod",
            "app_environment": "production",
            "debug_mode": False,
            "api_endpoint": "https://api.example.com",
            "db_connection": "postgresql://produser:prodpass@prodhost/proddb",
            "feature_toggle": {"new_ui": False, "beta_features": False, "enable_monitoring": True},
            "env_color": "green",
            "custom_message": "Production: Stability is key."
        }
    }

    # Write group_vars files for each environment.
    for env, vars_dict in group_vars_definitions.items():
        group_file = os.path.join("group_vars", f"{env}.yml")
        with open(group_file, "w") as f:
            yaml.dump(vars_dict, f, default_flow_style=False)
        print(f"Created group_vars file: {group_file}")

    # Build a static inventory in YAML format.
    # Static inventory format requires a top-level "all:" key.
    static_inventory = {
        "all": {
            "children": groups
        }
    }
    with open("inventory.yml", "w") as f:
        yaml.dump(static_inventory, f, default_flow_style=False)
    print("Generated static inventory.yml")

if __name__ == "__main__":
    generate_inventory()

