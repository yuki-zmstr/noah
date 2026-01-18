"""Bedrock model configuration helper for different regions."""

import os
from typing import Dict, Optional


class BedrockModelConfig:
    """Helper class to get the correct Bedrock model ID based on region and requirements."""
    
    # Regional inference profiles for Claude models
    REGIONAL_PROFILES = {
        # US regions - use US inference profile
        "us-east-1": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "us-east-2": "us.anthropic.claude-3-5-sonnet-20241022-v2:0", 
        "us-west-2": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        
        # Japan regions - use Japan inference profile (Claude 4.5)
        "ap-northeast-1": "jp.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "ap-northeast-3": "jp.anthropic.claude-sonnet-4-5-20250929-v1:0",
        
        # Australia regions - use Australia inference profile (Claude 4.5)
        "ap-southeast-2": "au.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "ap-southeast-4": "au.anthropic.claude-sonnet-4-5-20250929-v1:0",
    }
    
    # Fallback direct models (older versions that support direct access)
    DIRECT_MODELS = {
        "us-east-1": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "us-west-2": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "eu-west-1": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "ap-northeast-1": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "ap-southeast-2": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    }
    
    # Global inference profile (no data residency requirements)
    GLOBAL_PROFILE = "anthropic.claude-sonnet-4-5-20250929-v1:0"
    
    @classmethod
    def get_model_id(
        cls, 
        region: Optional[str] = None,
        prefer_latest: bool = True,
        data_residency_required: bool = True
    ) -> str:
        """
        Get the appropriate model ID based on region and requirements.
        
        Args:
            region: AWS region (defaults to AWS_REGION env var)
            prefer_latest: Whether to prefer latest models (Claude 4.5 vs 3.5)
            data_residency_required: Whether data must stay in specific geography
            
        Returns:
            Model ID string to use with Bedrock
        """
        if not region:
            region = os.getenv("AWS_REGION", "us-east-1")
        
        # If no data residency requirements, use global profile for latest model
        if not data_residency_required and prefer_latest:
            return cls.GLOBAL_PROFILE
        
        # Try regional inference profile first (latest models)
        if prefer_latest and region in cls.REGIONAL_PROFILES:
            return cls.REGIONAL_PROFILES[region]
        
        # Fall back to direct model access (older but more widely available)
        if region in cls.DIRECT_MODELS:
            return cls.DIRECT_MODELS[region]
        
        # Default fallback
        return "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    @classmethod
    def get_config_for_region(cls, region: str) -> Dict[str, str]:
        """
        Get all available model options for a specific region.
        
        Args:
            region: AWS region
            
        Returns:
            Dictionary with model configuration options
        """
        config = {
            "region": region,
            "recommended": cls.get_model_id(region, prefer_latest=True, data_residency_required=True),
            "fallback": cls.get_model_id(region, prefer_latest=False, data_residency_required=True),
        }
        
        # Add global option if no data residency requirements
        config["global"] = cls.GLOBAL_PROFILE
        
        return config
    
    @classmethod
    def validate_model_for_region(cls, model_id: str, region: str) -> Dict[str, any]:
        """
        Validate if a model ID is appropriate for a given region.
        
        Args:
            model_id: Model ID to validate
            region: AWS region
            
        Returns:
            Validation result with recommendations
        """
        result = {
            "valid": True,
            "warnings": [],
            "recommendations": []
        }
        
        # Check for common issues
        if model_id.startswith("us.") and not region.startswith("us-"):
            result["warnings"].append(f"Using US inference profile in non-US region {region}")
            result["recommendations"].append(f"Consider using regional profile: {cls.get_model_id(region)}")
        
        if model_id.startswith("jp.") and not region.startswith("ap-northeast-"):
            result["warnings"].append(f"Using Japan inference profile in non-Japan region {region}")
            result["recommendations"].append(f"Consider using regional profile: {cls.get_model_id(region)}")
        
        if model_id.startswith("au.") and not region.startswith("ap-southeast-"):
            result["warnings"].append(f"Using Australia inference profile in non-Australia region {region}")
            result["recommendations"].append(f"Consider using regional profile: {cls.get_model_id(region)}")
        
        # Check for v2 models that require inference profiles
        if "20241022-v2:0" in model_id and not any(model_id.startswith(prefix) for prefix in ["us.", "jp.", "au."]):
            result["valid"] = False
            result["warnings"].append("Claude 3.5 Sonnet v2 requires inference profile")
            result["recommendations"].append(f"Use inference profile: {cls.get_model_id(region)}")
        
        return result


def get_bedrock_model_id() -> str:
    """
    Convenience function to get the appropriate Bedrock model ID for current environment.
    
    Returns:
        Model ID string configured for the current AWS region
    """
    return BedrockModelConfig.get_model_id()


if __name__ == "__main__":
    # Example usage
    regions = ["us-east-1", "ap-northeast-1", "ap-southeast-2", "eu-west-1"]
    
    for region in regions:
        config = BedrockModelConfig.get_config_for_region(region)
        print(f"\n{region}:")
        print(f"  Recommended: {config['recommended']}")
        print(f"  Fallback: {config['fallback']}")
        print(f"  Global: {config['global']}")