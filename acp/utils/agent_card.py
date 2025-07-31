"""
ACP Agent Card Utilities

Provides validation, loading, and management utilities for ACP Agent Cards.
Handles both the schema definition and example instances.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


logger = logging.getLogger(__name__)


def get_agent_card_schema_path() -> Path:
    """Get the path to the agent card JSON schema"""
    return Path(__file__).parent.parent / "schemas" / "agent-card.schema.json"


def get_examples_dir() -> Path:
    """Get the path to the agent card examples directory"""
    # Look in package root examples/agent-cards for better organization
    package_root = Path(__file__).parent.parent.parent
    return package_root / "examples" / "agent-cards"


def load_agent_card_schema() -> Dict[str, Any]:
    """
    Load the agent card JSON schema.
    
    Returns:
        Dictionary containing the JSON schema
        
    Raises:
        FileNotFoundError: If schema file is not found
        ValueError: If schema cannot be parsed
    """
    schema_path = get_agent_card_schema_path()
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Agent card schema not found at: {schema_path}")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        logger.debug(f"Loaded agent card schema from: {schema_path}")
        return schema
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse agent card schema: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load agent card schema: {e}")


def load_example_agent_cards() -> Dict[str, Dict[str, Any]]:
    """
    Load all example agent cards from the examples directory.
    
    Returns:
        Dictionary mapping filenames to agent card data
        
    Raises:
        FileNotFoundError: If examples directory is not found
    """
    examples_dir = get_examples_dir()
    
    if not examples_dir.exists():
        raise FileNotFoundError(f"Examples directory not found at: {examples_dir}")
    
    examples = {}
    
    # Find all JSON files in examples directory
    for json_file in examples_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                card_data = json.load(f)
            
            # Use filename without extension as key
            key = json_file.stem
            examples[key] = card_data
            
            logger.debug(f"Loaded example agent card: {key}")
            
        except Exception as e:
            logger.warning(f"Failed to load example {json_file}: {e}")
    
    return examples


def validate_agent_card(agent_card: Dict[str, Any], strict: bool = True) -> Dict[str, Any]:
    """
    Validate an agent card against the JSON schema.
    
    Args:
        agent_card: Agent card data to validate
        strict: Whether to use strict validation (requires jsonschema library)
        
    Returns:
        Validation result with 'valid', 'errors', and 'warnings' keys
    """
    result = {
        "valid": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        schema = load_agent_card_schema()
        
        if strict and JSONSCHEMA_AVAILABLE:
            # Use jsonschema for strict validation
            try:
                jsonschema.validate(instance=agent_card, schema=schema)
                result["valid"] = True
                logger.debug("Agent card passed strict validation")
                
            except jsonschema.ValidationError as e:
                result["errors"].append(f"Schema validation error: {e.message}")
                logger.error(f"Agent card validation failed: {e.message}")
                
            except jsonschema.SchemaError as e:
                result["errors"].append(f"Schema error: {e.message}")
                logger.error(f"Schema error: {e.message}")
                
        else:
            # Basic validation without jsonschema library
            if not strict:
                result["warnings"].append("Using basic validation (install jsonschema for strict validation)")
            
            # Check required fields
            required_fields = schema.get("required", [])
            missing_fields = [field for field in required_fields if field not in agent_card]
            
            if missing_fields:
                result["errors"].extend([f"Missing required field: {field}" for field in missing_fields])
            else:
                result["valid"] = True
                logger.debug("Agent card passed basic validation")
    
    except Exception as e:
        result["errors"].append(f"Validation error: {str(e)}")
        logger.error(f"Agent card validation failed: {e}")
    
    return result


def create_agent_card_template(
    name: str,
    description: str,
    version: str,
    url: str,
    organization: str
) -> Dict[str, Any]:
    """
    Create a basic agent card template with required fields.
    
    Args:
        name: Agent name
        description: Agent description
        version: Agent version (semantic versioning)
        url: ACP JSON-RPC endpoint URL
        organization: Provider organization
        
    Returns:
        Basic agent card template
    """
    return {
        "name": name,
        "description": description,
        "version": version,
        "url": url,
        "provider": {
            "organization": organization
        },
        "capabilities": {
            "streaming": True,
            "pushNotifications": True,
            "fileUpload": False,
            "multimodal": False
        },
        "authentication": {
            "schemes": ["oauth2"],
            "scopes": ["acp:agent:read"]
        },
        "skills": [],
        "metadata": {
            "tags": [],
            "category": "general",
            "lastUpdated": datetime.utcnow().isoformat() + "Z"
        }
    }


def add_skill_to_agent_card(
    agent_card: Dict[str, Any],
    skill_id: str,
    skill_name: str,
    skill_description: str,
    input_modes: Optional[List[str]] = None,
    output_modes: Optional[List[str]] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add a skill to an existing agent card.
    
    Args:
        agent_card: Existing agent card
        skill_id: Unique skill identifier
        skill_name: Human-readable skill name
        skill_description: Skill description
        input_modes: Types of input the skill accepts
        output_modes: Types of output the skill produces
        parameters: Optional skill parameters schema
        
    Returns:
        Updated agent card with new skill
    """
    if input_modes is None:
        input_modes = ["text"]
    if output_modes is None:
        output_modes = ["text"]
    
    skill = {
        "id": skill_id,
        "name": skill_name,
        "description": skill_description,
        "inputModes": input_modes,
        "outputModes": output_modes
    }
    
    if parameters:
        skill["parameters"] = parameters
    
    # Initialize skills array if it doesn't exist
    if "skills" not in agent_card:
        agent_card["skills"] = []
    
    # Add skill if not already present
    existing_ids = [s.get("id") for s in agent_card["skills"]]
    if skill_id not in existing_ids:
        agent_card["skills"].append(skill)
        logger.debug(f"Added skill '{skill_id}' to agent card")
    else:
        logger.warning(f"Skill '{skill_id}' already exists in agent card")
    
    return agent_card


def update_agent_card_metadata(
    agent_card: Dict[str, Any],
    tags: Optional[List[str]] = None,
    category: Optional[str] = None,
    popularity: Optional[float] = None
) -> Dict[str, Any]:
    """
    Update agent card metadata.
    
    Args:
        agent_card: Agent card to update
        tags: List of tags
        category: Agent category
        popularity: Popularity rating (0-5)
        
    Returns:
        Updated agent card
    """
    if "metadata" not in agent_card:
        agent_card["metadata"] = {}
    
    if tags is not None:
        agent_card["metadata"]["tags"] = tags
    
    if category is not None:
        agent_card["metadata"]["category"] = category
    
    if popularity is not None:
        if 0 <= popularity <= 5:
            agent_card["metadata"]["popularity"] = popularity
        else:
            logger.warning(f"Invalid popularity rating: {popularity} (must be 0-5)")
    
    # Always update lastUpdated
    agent_card["metadata"]["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
    
    return agent_card


def save_agent_card(agent_card: Dict[str, Any], file_path: str) -> bool:
    """
    Save an agent card to a JSON file.
    
    Args:
        agent_card: Agent card data
        file_path: Path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate before saving
        validation = validate_agent_card(agent_card, strict=False)
        if not validation["valid"]:
            logger.error(f"Cannot save invalid agent card: {validation['errors']}")
            return False
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(agent_card, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Agent card saved to: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save agent card: {e}")
        return False


def load_agent_card(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load an agent card from a JSON file.
    
    Args:
        file_path: Path to the agent card file
        
    Returns:
        Agent card data or None if loading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            agent_card = json.load(f)
        
        # Validate loaded card
        validation = validate_agent_card(agent_card, strict=False)
        if validation["warnings"]:
            for warning in validation["warnings"]:
                logger.warning(warning)
        
        logger.info(f"Agent card loaded from: {file_path}")
        return agent_card
        
    except Exception as e:
        logger.error(f"Failed to load agent card from {file_path}: {e}")
        return None


def find_agents_by_capability(
    capability: str,
    examples: Optional[Dict[str, Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Find example agents that support a specific capability.
    
    Args:
        capability: Capability to search for (e.g., 'streaming', 'fileUpload')
        examples: Optional examples dict (loads if not provided)
        
    Returns:
        List of matching agent cards
    """
    if examples is None:
        try:
            examples = load_example_agent_cards()
        except Exception as e:
            logger.error(f"Failed to load examples: {e}")
            return []
    
    matching_agents = []
    
    for name, card in examples.items():
        capabilities = card.get("capabilities", {})
        if capabilities.get(capability, False):
            matching_agents.append(card)
    
    return matching_agents


def find_agents_by_skill(
    skill_type: str,
    examples: Optional[Dict[str, Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Find example agents that provide a specific type of skill.
    
    Args:
        skill_type: Type of skill to search for (matches skill names/descriptions)
        examples: Optional examples dict (loads if not provided)
        
    Returns:
        List of matching agent cards
    """
    if examples is None:
        try:
            examples = load_example_agent_cards()
        except Exception as e:
            logger.error(f"Failed to load examples: {e}")
            return []
    
    matching_agents = []
    skill_type_lower = skill_type.lower()
    
    for name, card in examples.items():
        skills = card.get("skills", [])
        for skill in skills:
            skill_name = skill.get("name", "").lower()
            skill_desc = skill.get("description", "").lower()
            skill_id = skill.get("id", "").lower()
            
            if (skill_type_lower in skill_name or 
                skill_type_lower in skill_desc or 
                skill_type_lower in skill_id):
                matching_agents.append(card)
                break  # Don't add the same agent multiple times
    
    return matching_agents


# CLI utility functions

def print_agent_card_info(agent_card: Dict[str, Any]):
    """Print formatted agent card information"""
    print("🤖 Agent Card Information")
    print("=" * 40)
    print(f"Name: {agent_card.get('name', 'Unknown')}")
    print(f"Version: {agent_card.get('version', 'Unknown')}")
    print(f"Description: {agent_card.get('description', 'No description')}")
    print(f"URL: {agent_card.get('url', 'No URL')}")
    
    provider = agent_card.get("provider", {})
    print(f"Provider: {provider.get('organization', 'Unknown')}")
    
    capabilities = agent_card.get("capabilities", {})
    print("\nCapabilities:")
    for cap, enabled in capabilities.items():
        status = "✅" if enabled else "❌"
        print(f"  {status} {cap}")
    
    skills = agent_card.get("skills", [])
    print(f"\nSkills ({len(skills)}):")
    for skill in skills:
        print(f"  • {skill.get('name', 'Unknown')} ({skill.get('id', 'no-id')})")


def main():
    """Main CLI entry point for agent card utilities"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "validate":
            if len(sys.argv) < 3:
                print("Usage: python -m acp.utils.agent_card validate <file_path>")
                return
            
            file_path = sys.argv[2]
            agent_card = load_agent_card(file_path)
            
            if agent_card:
                validation = validate_agent_card(agent_card)
                if validation["valid"]:
                    print(f"✅ Agent card is valid: {file_path}")
                else:
                    print(f"❌ Agent card validation failed: {file_path}")
                    for error in validation["errors"]:
                        print(f"  • {error}")
            
        elif command == "examples":
            try:
                examples = load_example_agent_cards()
                print(f"📁 Found {len(examples)} example agent cards:")
                for name, card in examples.items():
                    print(f"  • {name}: {card.get('name', 'Unknown')}")
            except Exception as e:
                print(f"❌ Failed to load examples: {e}")
        
        elif command == "schema":
            try:
                schema = load_agent_card_schema()
                print("📋 Agent Card Schema Information")
                print("=" * 40)
                print(f"Title: {schema.get('title', 'Unknown')}")
                print(f"Description: {schema.get('description', 'No description')}")
                print(f"Required fields: {', '.join(schema.get('required', []))}")
            except Exception as e:
                print(f"❌ Failed to load schema: {e}")
        
        else:
            print("Available commands: validate <file>, examples, schema")
    else:
        # Show schema info by default
        try:
            schema = load_agent_card_schema()
            examples = load_example_agent_cards()
            
            print("📋 ACP Agent Card System")
            print("=" * 30)
            print(f"Schema: {schema.get('title', 'Unknown')}")
            print(f"Examples: {len(examples)} available")
            print("\nCommands: validate, examples, schema")
            
        except Exception as e:
            print(f"❌ System error: {e}")


if __name__ == "__main__":
    main() 