"""
ACP Schema Utilities

Provides runtime access to the OpenAPI schema and agent card examples
for validation, documentation, and tooling purposes.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


logger = logging.getLogger(__name__)


def get_package_root() -> Path:
    """Get the root directory of the acp package"""
    return Path(__file__).parent.parent


def get_schema_path() -> Path:
    """Get the path to the OpenAPI schema file"""
    return get_package_root() / "schemas" / "acp-schema.yaml"


def load_openapi_schema() -> Dict[str, Any]:
    """
    Load the OpenAPI schema from the package.
    
    Returns:
        Dictionary containing the OpenAPI schema
        
    Raises:
        FileNotFoundError: If schema file is not found
        ImportError: If PyYAML is not available
        ValueError: If schema cannot be parsed
    """
    if not YAML_AVAILABLE:
        raise ImportError(
            "PyYAML is required to load the OpenAPI schema. "
            "Install it with: pip install PyYAML"
        )
    
    schema_path = get_schema_path()
    
    if not schema_path.exists():
        raise FileNotFoundError(f"OpenAPI schema not found at: {schema_path}")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        logger.debug(f"Loaded OpenAPI schema from: {schema_path}")
        return schema
        
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse OpenAPI schema: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load OpenAPI schema: {e}")


def get_schema_version() -> Optional[str]:
    """
    Get the version of the OpenAPI schema.
    
    Returns:
        Schema version string or None if not found
    """
    try:
        schema = load_openapi_schema()
        return schema.get("info", {}).get("version")
    except Exception as e:
        logger.warning(f"Failed to get schema version: {e}")
        return None


def get_schema_info() -> Dict[str, Any]:
    """
    Get basic information about the OpenAPI schema.
    
    Returns:
        Dictionary with schema metadata
    """
    try:
        schema = load_openapi_schema()
        info = schema.get("info", {})
        
        return {
            "title": info.get("title", "Unknown"),
            "version": info.get("version", "Unknown"),
            "description": info.get("description", ""),
            "schema_path": str(get_schema_path()),
            "available": True
        }
    except Exception as e:
        logger.warning(f"Failed to get schema info: {e}")
        return {
            "title": "ACP OpenAPI Schema",
            "version": "Unknown",
            "description": "Schema not available",
            "schema_path": str(get_schema_path()),
            "available": False,
            "error": str(e)
        }


def get_available_methods() -> Dict[str, Any]:
    """
    Get list of available ACP methods from the schema.
    
    Returns:
        Dictionary with method information
    """
    try:
        schema = load_openapi_schema()
        
        # Extract method enum from JsonRpcRequest schema
        method_enum = None
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        
        # Look for method enum in JsonRpcRequest.properties.method.enum
        if "JsonRpcRequest" in schemas:
            request_schema = schemas["JsonRpcRequest"]
            properties = request_schema.get("properties", {})
            method_prop = properties.get("method", {})
            if "enum" in method_prop:
                method_enum = method_prop["enum"]
        
        # Also try looking for a standalone Method enum (fallback)
        if not method_enum and "Method" in schemas:
            method_schema = schemas["Method"]
            if "enum" in method_schema:
                method_enum = method_schema["enum"]
        
        # Extract paths info
        paths = schema.get("paths", {})
        
        return {
            "methods": method_enum or [],
            "endpoints": list(paths.keys()),
            "total_methods": len(method_enum) if method_enum else 0,
            "total_endpoints": len(paths)
        }
    except Exception as e:
        logger.warning(f"Failed to get available methods: {e}")
        return {
            "methods": [],
            "endpoints": [],
            "total_methods": 0,
            "total_endpoints": 0,
            "error": str(e)
        }


def validate_against_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """
    Validate data against a specific schema component.
    
    Args:
        data: Data to validate
        schema_name: Name of the schema component
        
    Returns:
        True if valid, False otherwise
        
    Note:
        This is a basic implementation. For full JSON Schema validation,
        use the jsonschema library with the extracted schema component.
    """
    try:
        schema = load_openapi_schema()
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        
        if schema_name not in schemas:
            logger.error(f"Schema component '{schema_name}' not found")
            return False
        
        # This is a basic check - for full validation, use jsonschema library
        component_schema = schemas[schema_name]
        required_fields = component_schema.get("required", [])
        
        # Check required fields are present
        for field in required_fields:
            if field not in data:
                logger.error(f"Required field '{field}' missing from data")
                return False
        
        logger.debug(f"Basic validation passed for schema: {schema_name}")
        return True
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False


def export_schema_as_json(output_path: Optional[str] = None) -> str:
    """
    Export the OpenAPI schema as JSON.
    
    Args:
        output_path: Optional path to save JSON file
        
    Returns:
        JSON string representation of the schema
    """
    schema = load_openapi_schema()
    json_content = json.dumps(schema, indent=2, default=str)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        logger.info(f"Schema exported as JSON to: {output_path}")
    
    return json_content


def get_model_schemas() -> Dict[str, Any]:
    """
    Get all model schemas from the OpenAPI specification.
    
    Returns:
        Dictionary containing all schema components
    """
    try:
        schema = load_openapi_schema()
        return schema.get("components", {}).get("schemas", {})
    except Exception as e:
        logger.error(f"Failed to get model schemas: {e}")
        return {}


# CLI utility functions

def print_schema_info():
    """Print schema information to console"""
    info = get_schema_info()
    
    print("📋 ACP OpenAPI Schema Information")
    print("=" * 40)
    print(f"Title: {info['title']}")
    print(f"Version: {info['version']}")
    print(f"Description: {info['description']}")
    print(f"Schema Path: {info['schema_path']}")
    print(f"Available: {'✅ Yes' if info['available'] else '❌ No'}")
    
    if not info['available']:
        print(f"Error: {info.get('error', 'Unknown error')}")
    else:
        methods = get_available_methods()
        print(f"Total Methods: {methods['total_methods']}")
        print(f"Total Endpoints: {methods['total_endpoints']}")


def print_available_methods():
    """Print available ACP methods to console"""
    methods = get_available_methods()
    
    print("🔧 Available ACP Methods")
    print("=" * 30)
    
    if methods['methods']:
        for i, method in enumerate(methods['methods'], 1):
            print(f"{i:2d}. {method}")
    else:
        print("No methods found or schema not available")
    
    print(f"\nTotal: {methods['total_methods']} methods")


def main():
    """Main CLI entry point for schema utilities"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "info":
            print_schema_info()
        elif command == "methods":
            print_available_methods()
        elif command == "export":
            output_file = sys.argv[2] if len(sys.argv) > 2 else "acp-schema.json"
            try:
                export_schema_as_json(output_file)
                print(f"✅ Schema exported to: {output_file}")
            except Exception as e:
                print(f"❌ Export failed: {e}")
        else:
            print("Available commands: info, methods, export [filename]")
    else:
        print_schema_info()


if __name__ == "__main__":
    main() 