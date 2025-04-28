"""
competition_config.py - Configuration for competition generation

Manages the selection of optional fields for competition generation.
Implements field categorization for proper placement in competition structure.
"""

from enum import Enum
from typing import Dict, List, Set, Optional
import json
from collections import defaultdict

class ConfigMode(Enum):
    REQUIRED_ONLY = "required_only"
    STANDARD = "standard"
    CUSTOM = "custom"

class FieldLevel(Enum):
    ROOT = "root"
    SERVICE_WINDOW = "service_window"

# Define field categories
ROOT_LEVEL_FIELDS = {
    "contact",
    "archive_on",
    "dps_record_reference",
    "product_type",
    "minimum_connection_voltage",
    "maximum_connection_voltage",
    "minimum_budget",
    "maximum_budget",
    "availability_guide_price",
    "utilisation_guide_price",
    "service_fee",
    "pricing_type"
}

SERVICE_WINDOW_FIELDS = {
    "public_holiday_handling",
    "minimum_run_time",
    "required_response_time",
    "dispatch_estimate",
    "dispatch_duration"
}

# Define standard optional fields commonly used
STANDARD_OPTIONAL_FIELDS = {
    "product_type",
    "minimum_connection_voltage",
    "maximum_connection_voltage",
    "dps_record_reference",
    "public_holiday_handling",
}

# Combined set of all optional fields
ALL_OPTIONAL_FIELDS = ROOT_LEVEL_FIELDS | SERVICE_WINDOW_FIELDS

# Field descriptions with categories
FIELD_METADATA = {
    # Root level fields
    "contact": {
        "description": "The email address for competition-related communications",
        "level": FieldLevel.ROOT
    },
    "archive_on": {
        "description": "Date and time at which the Competition archives",
        "level": FieldLevel.ROOT
    },
    "dps_record_reference": {
        "description": "Reference to a previously uploaded DPS Record",
        "level": FieldLevel.ROOT
    },
    "product_type": {
        "description": "Branded names for service products",
        "level": FieldLevel.ROOT
    },
    "minimum_connection_voltage": {
        "description": "Minimum voltage level in KV",
        "level": FieldLevel.ROOT
    },
    "maximum_connection_voltage": {
        "description": "Maximum voltage level in KV",
        "level": FieldLevel.ROOT
    },
    "minimum_budget": {
        "description": "The minimum budget value per year, in £ GBP",
        "level": FieldLevel.ROOT
    },
    "maximum_budget": {
        "description": "The maximum budget value per year, in £ GBP",
        "level": FieldLevel.ROOT
    },
    "availability_guide_price": {
        "description": "Guide price for Availability (£/MW/h or £/MVAr/h)",
        "level": FieldLevel.ROOT
    },
    "utilisation_guide_price": {
        "description": "Guide price for Utilisation (£/MW/h or £/MVAr/h)",
        "level": FieldLevel.ROOT
    },
    "service_fee": {
        "description": "Annual fee paid for capacity (£/MW/year or £/MVAr/year)",
        "level": FieldLevel.ROOT
    },
    "pricing_type": {
        "description": "Determines if prices are fixed or part of bid",
        "level": FieldLevel.ROOT
    },
    
    # Service window level fields
    "public_holiday_handling": {
        "description": "Designation of public holidays to be included or excluded",
        "level": FieldLevel.SERVICE_WINDOW
    },
    "minimum_run_time": {
        "description": "Minimum time required of the asset to provide flexibility",
        "level": FieldLevel.SERVICE_WINDOW
    },
    "required_response_time": {
        "description": "Time within which an Asset must respond to a utilisation request",
        "level": FieldLevel.SERVICE_WINDOW
    },
    "dispatch_estimate": {
        "description": "The estimated number of Dispatch events expected during the Service Period",
        "level": FieldLevel.SERVICE_WINDOW
    },
    "dispatch_duration": {
        "description": "The estimated duration of each Dispatch event",
        "level": FieldLevel.SERVICE_WINDOW
    }
}

class FieldSelector:
    """Enhanced field selector with support for field categorization."""
    
    def __init__(self):
        self.required_fields = {
            "reference",
            "name",
            "open",
            "closed",
            "area_buffer",
            "qualification_open",
            "qualification_closed",
            "boundary",
            "need_type",
            "type",
            "need_direction",
            "power_type",
            "service_periods"
        }
    
    def get_fields_for_mode(
        self,
        mode: ConfigMode,
        custom_fields: Optional[Set[str]] = None
    ) -> Dict[FieldLevel, Set[str]]:
        """
        Get the set of fields to include based on the configuration mode.
        Returns a dictionary mapping FieldLevel to sets of field names.
        
        Args:
            mode: Configuration mode (REQUIRED_ONLY, STANDARD, or CUSTOM)
            custom_fields: Set of optional fields to include when using CUSTOM mode
            
        Returns:
            Dict mapping FieldLevel to sets of field names to include
            
        Raises:
            ValueError: If invalid optional fields are specified in custom_fields
        """
        # Initialize result with empty sets for each level
        fields = {
            FieldLevel.ROOT: set(),
            FieldLevel.SERVICE_WINDOW: set()
        }
        
        if mode == ConfigMode.REQUIRED_ONLY:
            # Only include voltage requirements
            fields[FieldLevel.ROOT].update({"minimum_connection_voltage", "maximum_connection_voltage"})
        
        elif mode == ConfigMode.STANDARD:
            # Include commonly used optional fields
            for field in STANDARD_OPTIONAL_FIELDS:
                level = FIELD_METADATA[field]["level"]
                fields[level].add(field)
        
        elif mode == ConfigMode.CUSTOM and custom_fields is not None:
            # Validate custom fields
            invalid_fields = custom_fields - ALL_OPTIONAL_FIELDS
            if invalid_fields:
                raise ValueError(f"Invalid optional fields specified: {invalid_fields}")
            
            # Categorize selected fields
            for field in custom_fields:
                level = FIELD_METADATA[field]["level"]
                fields[level].add(field)
        
        return fields
    
    def validate_field_placement(self, fields: Set[str]) -> bool:
        """
        Validate that fields are properly categorized.
        
        Args:
            fields: Set of field names to validate
            
        Returns:
            bool: True if all fields are properly categorized
        """
        for field in fields:
            if field not in FIELD_METADATA:
                return False
        return True
    
    def get_field_description(self, field: str) -> str:
        """
        Get the description and level for a field.
        
        Args:
            field: Name of the field
            
        Returns:
            str: Description of the field
        """
        if field in FIELD_METADATA:
            return FIELD_METADATA[field]["description"]
        return "No description available"
    
    def get_field_level(self, field: str) -> Optional[FieldLevel]:
        """
        Get the level (root or service window) for a field.
        
        Args:
            field: Name of the field
            
        Returns:
            Optional[FieldLevel]: The field's level or None if not found
        """
        if field in FIELD_METADATA:
            return FIELD_METADATA[field]["level"]
        return None

    @staticmethod
    def generate_ui_template() -> Dict:
        """
        Generate a template for UI configuration showing all optional fields.
        
        Returns:
            Dict with optional fields configuration for UI
        """
        selector = FieldSelector()
        
        optional_fields = []
        for field in sorted(ALL_OPTIONAL_FIELDS):
            metadata = FIELD_METADATA[field]
            optional_fields.append({
                "name": field,
                "description": metadata["description"],
                "level": metadata["level"].value,
                "included_in_standard": field in STANDARD_OPTIONAL_FIELDS,
                "selected": field in STANDARD_OPTIONAL_FIELDS
            })
        
        return {
            "optional_fields": optional_fields
        }

def load_custom_config(config_path: str) -> Dict[FieldLevel, Set[str]]:
    """
    Load custom field selection from JSON file.
    Expected format:
    {
        "root_fields": ["field1", "field2"],
        "service_window_fields": ["field3", "field4"]
    }
    """
    with open(config_path) as f:
        config = json.load(f)
    
    fields = {
        FieldLevel.ROOT: set(config.get("root_fields", [])),
        FieldLevel.SERVICE_WINDOW: set(config.get("service_window_fields", []))
    }
    
    return fields