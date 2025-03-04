#!/usr/bin/env python3
import os
import yaml

# Define your servers with IP, SSH port, and corresponding environment.
servers = [
    {"ip": "192.168.1.2", "port": 1234, "env": "dev"},
    {"ip": "192.168.1.3", "port": 1235, "env": "staging"},
    {"ip": "192.168.1.4", "port": 1236, "env": "production"}
]

# Create necessary directories for host_vars and group_vars if they don't exist.
os.makedirs("host_vars", exist_ok=True)
os.makedirs("group_vars", exist_ok=True)

# Generate host_vars files for each server.
for server in servers:
    host_file = os.path.join("host_vars", f"{server['ip']}.yml")
    host_data = {
        "ansible_host": server["ip"],
        "ansible_port": server["port"],
        "environment": server["env"],
        # Example of a unique application instance identifier.
        "app_instance_id": f"app-{server['ip'].replace('.', '-')}"
    }
    with open(host_file, "w") as f:
        yaml.dump(host_data, f, default_flow_style=False)
    print(f"Created host_vars file: {host_file}")

# Define fixed filesystem values and creative environment variables per environment.
env_group_vars = {
    "dev": {
        "filesystem_mount": "/mnt/dev",
        "backup_path": "/backup/dev",
        "log_path": "/var/log/dev",
        "app_environment": "development",
        "debug_mode": True,
        "api_endpoint": "https://api-dev.example.com",
        "db_connection": "postgresql://devuser:devpass@localhost/devdb",
        "feature_toggle": {"new_ui": True, "beta_features": True},
        "env_color": "blue"  # Visual cue: blue for development.
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
        "env_color": "yellow"  # Visual cue: yellow for staging.
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
        "env_color": "green"  # Visual cue: green for production.
    }
}

# Generate group_vars files for each environment with the fixed filesystem and creative app settings.
for env, vars_dict in env_group_vars.items():
    group_file = os.path.join("group_vars", f"{env}.yml")
    with open(group_file, "w") as f:
        yaml.dump(vars_dict, f, default_flow_style=False)
    print(f"Created group_vars file: {group_file}")

