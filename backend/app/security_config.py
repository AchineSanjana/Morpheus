"""
Security configuration for Morpheus Sleep AI System
Environment-based security settings and validation
"""

import os
import re
from cryptography.fernet import Fernet
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration management"""
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load security configuration from environment"""
        # API Security
        self.api_rate_limit_enabled = os.getenv("API_RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.api_rate_limit_requests_per_minute = int(os.getenv("API_RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
        self.api_rate_limit_burst_size = int(os.getenv("API_RATE_LIMIT_BURST_SIZE", "10"))
        
        # Encryption
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        
        # Content Security
        self.content_validation_enabled = os.getenv("CONTENT_VALIDATION_ENABLED", "true").lower() == "true"
        self.prompt_injection_protection = os.getenv("PROMPT_INJECTION_PROTECTION", "true").lower() == "true"
        self.output_validation_enabled = os.getenv("OUTPUT_VALIDATION_ENABLED", "true").lower() == "true"
        
        # Logging Security
        self.security_log_level = os.getenv("SECURITY_LOG_LEVEL", "INFO")
        self.pii_logging_enabled = os.getenv("PII_LOGGING_ENABLED", "false").lower() == "true"
        self.content_hashing_enabled = os.getenv("CONTENT_HASHING_ENABLED", "true").lower() == "true"
        
        # AI Model Security
        self.ai_model_timeout = int(os.getenv("AI_MODEL_TIMEOUT", "30"))
        self.ai_model_max_tokens = int(os.getenv("AI_MODEL_MAX_TOKENS", "2000"))
        self.ai_model_temperature_limit = float(os.getenv("AI_MODEL_TEMPERATURE_LIMIT", "1.0"))
        
        # Initialize encryption if key is provided
        self.cipher = None
        if self.encryption_key:
            try:
                self.cipher = Fernet(self.encryption_key.encode())
            except Exception as e:
                logger.warning(f"Failed to initialize encryption: {e}")
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data"""
        if not self.cipher:
            return data  # Return as-is if encryption not available
        
        try:
            return self.cipher.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        if not self.cipher:
            return encrypted_data  # Return as-is if encryption not available
        
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://generativelanguage.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "frame-ancestors 'none';"
            ),
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()"
        }
    
    def validate_ai_parameters(self, temperature: float, max_tokens: int) -> bool:
        """Validate AI model parameters"""
        if temperature > self.ai_model_temperature_limit:
            logger.warning(f"Temperature {temperature} exceeds limit {self.ai_model_temperature_limit}")
            return False
        
        if max_tokens > self.ai_model_max_tokens:
            logger.warning(f"Max tokens {max_tokens} exceeds limit {self.ai_model_max_tokens}")
            return False
        
        return True

# Global security configuration instance
security_config = SecurityConfig()

# Validation functions
def is_safe_content(content: str) -> bool:
    """Check if content is safe for processing"""
    if not security_config.content_validation_enabled:
        return True
    
    # Basic content safety checks
    dangerous_patterns = [
        r"<script", r"javascript:", r"eval\(", r"document\.",
        r"window\.", r"alert\(", r"confirm\(", r"prompt\("
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return False
    
    return True

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging"""
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def sanitize_for_logging(data: Any) -> str:
    """Sanitize data for safe logging"""
    if isinstance(data, str):
        if security_config.content_hashing_enabled:
            return hash_sensitive_data(data)
        return data[:100] + "..." if len(data) > 100 else data
    return str(data)