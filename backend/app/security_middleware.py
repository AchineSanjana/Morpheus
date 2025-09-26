"""
Security middleware for Morpheus Sleep AI System
Provides rate limiting, request validation, and security monitoring
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import hashlib
import json

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}  # {ip: [timestamps]}
        self.cleanup_interval = 300  # Clean up every 5 minutes
        self.last_cleanup = time.time()
    
    def _cleanup_old_requests(self):
        """Remove old request timestamps"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # Keep last hour
        for ip in list(self.requests.keys()):
            self.requests[ip] = [ts for ts in self.requests[ip] if ts > cutoff_time]
            if not self.requests[ip]:
                del self.requests[ip]
        
        self.last_cleanup = current_time
    
    def is_rate_limited(self, ip: str, requests_per_hour: int = 60) -> bool:
        """Check if IP is rate limited"""
        self._cleanup_old_requests()
        
        current_time = time.time()
        hour_ago = current_time - 3600
        
        if ip not in self.requests:
            self.requests[ip] = []
        
        # Count requests in last hour
        recent_requests = [ts for ts in self.requests[ip] if ts > hour_ago]
        
        if len(recent_requests) >= requests_per_hour:
            return True
        
        # Add current request
        self.requests[ip].append(current_time)
        return False

class SecurityMonitor:
    """Monitor and log security events"""
    
    def __init__(self):
        self.suspicious_patterns = [
            r"<script", r"javascript:", r"eval\(", r"document\.",
            r"window\.", r"alert\(", r"confirm\(", r"prompt\(",
            r"ignore\s+previous\s+instructions", r"system\s*:",
            r"admin\s*:", r"override\s+settings"
        ]
        self.security_events = []
    
    async def log_security_event(
        self, 
        event_type: str, 
        severity: str,
        user_id: str = "anonymous",
        ip_address: str = "unknown",
        details: Dict[str, Any] = None,
        action_taken: str = "none"
    ):
        """Log a security event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {},
            "action_taken": action_taken
        }
        
        self.security_events.append(event)
        
        # Log to security logger
        security_logger.log(
            level=getattr(logging, severity.upper()),
            msg=f"SECURITY_EVENT: {event_type} | User: {user_id} | IP: {ip_address} | Action: {action_taken}"
        )
        
        # Keep only recent events in memory (last 1000)
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-500:]
    
    async def validate_request_content(self, content: str, ip_address: str) -> bool:
        """Validate request content for suspicious patterns"""
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                await self.log_security_event(
                    event_type="suspicious_input_detected",
                    severity="WARNING",
                    ip_address=ip_address,
                    details={"pattern": pattern, "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16]},
                    action_taken="content_filtered"
                )
                return False
        return True

class SecurityMiddleware:
    """Main security middleware for request validation"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.security_monitor = SecurityMonitor()
        
        # Rate limits for different endpoints
        self.rate_limits = {
            "/chat": 30,  # 30 requests per hour
            "/agents/storyteller": 20,  # 20 stories per hour
            "/chat/stream": 15,  # 15 streams per hour
        }
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded IP first (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"
    
    async def validate_request_security(self, request: Request, content: str = "") -> bool:
        """Comprehensive request security validation"""
        client_ip = self.get_client_ip(request)
        path = str(request.url.path)
        
        # Check rate limits
        rate_limit = self._get_rate_limit_for_path(path)
        if self.rate_limiter.is_rate_limited(client_ip, rate_limit):
            await self.security_monitor.log_security_event(
                event_type="rate_limit_exceeded",
                severity="WARNING",
                ip_address=client_ip,
                details={"path": path, "limit": rate_limit},
                action_taken="request_blocked"
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {rate_limit} requests per hour."
            )
        
        # Validate content if provided
        if content:
            is_valid = await self.security_monitor.validate_request_content(content, client_ip)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail="Request contains potentially harmful content"
                )
        
        # Log successful request
        await self.security_monitor.log_security_event(
            event_type="request_processed",
            severity="INFO",
            ip_address=client_ip,
            details={"path": path, "content_length": len(content)},
            action_taken="request_allowed"
        )
        
        return True
    
    def _get_rate_limit_for_path(self, path: str) -> int:
        """Get rate limit for specific path"""
        for endpoint, limit in self.rate_limits.items():
            if endpoint in path:
                return limit
        return 60  # Default rate limit

# Global security middleware instance
security_middleware = SecurityMiddleware()

# Security headers middleware function
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://generativelanguage.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "frame-ancestors 'none';"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    
    return response

# Rate limit error handler
def rate_limit_error_handler(request: Request, exc: HTTPException):
    """Handle rate limit errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Rate limit exceeded",
            "detail": exc.detail,
            "retry_after": 3600  # 1 hour
        }
    )