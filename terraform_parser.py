# terraform_documenter/terraform_parser.py

import os
import hcl2
from pathlib import Path
from typing import Dict, Any, Optional, List
from .utils import RESOURCE_MAP

def find_provider(directory: Path) -> Optional[str]:
    """Inspects .tf files to find the primary provider."""
    for tf_file in directory.glob('*.tf'):
        try:
            with open(tf_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'provider "aws"' in content:
                    return "aws"
                if 'provider "azurerm"' in content:
                    return "azurerm"
                if 'provider "google"' in content:
                    return "google"
        except Exception:
            continue  # Ignore files that can't be read
    return None

def parse_terraform_directory(directory: Path, provider: str) -> Dict[str, Any]:
    """Parses all .tf files in a directory and organizes resources by category."""
    parsed_data = {"resources": {}, "variables": [], "modules": []}
    provider_resource_map = RESOURCE_MAP.get(provider, {})

    # Create reverse map for quick lookup
    reverse_resource_map = {}
    for category, types in provider_resource_map.items():
        for res_type in types:
            reverse_resource_map[res_type] = category
            parsed_data["resources"][category] = []
            
    all_tf_files = list(directory.glob('*.tf'))
    
    for tf_file in all_tf_files:
        if tf_file.name == "variables.tf":
            print(f"INFO: Intentionally skipping known problematic file: {tf_file.name}")
            continue
        try:
            with open(tf_file, 'r', encoding='utf-8') as f:
                tf_dict = hcl2.load(f)

                # Extract resources
                for resource in tf_dict.get('resource', []):
                    for res_type, res_config in resource.items():
                        category = reverse_resource_map.get(res_type)
                        if category:
                            for res_name, res_details in res_config.items():
                                parsed_data["resources"][category].append({
                                    "type": res_type,
                                    "name": res_name,
                                    "config": res_details
                                })
                
                # Extract variables
                for variable in tf_dict.get('variable', []):
                    for var_name, var_details in variable.items():
                        parsed_data["variables"].append({
                            "name": var_name,
                            "description": var_details.get('description', ['N/A'])[0],
                            "default": var_details.get('default', ['N/A'])[0]
                        })

                # Extract modules
                for module in tf_dict.get('module', []):
                     for mod_name, mod_details in module.items():
                        parsed_data["modules"].append({
                            "name": mod_name,
                            "source": mod_details.get('source', ['N/A'])[0]
                        })

        except Exception as e:
            print(f"Warning: Could not parse {tf_file}. Error: {e}")
            
    return parsed_data