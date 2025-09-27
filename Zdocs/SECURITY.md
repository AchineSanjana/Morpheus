# 🔒 Morpheus Sleep AI - Security Implementation Guide

Status note (Sep 27, 2025): Frontend now includes an in-app Privacy Policy modal (`PrivacyPolicy.tsx`), and authentication supports both persistent (localStorage) and session-only (sessionStorage) tokens via dual Supabase clients. Ensure your CSP and cookie/storage policies reflect this behavior.

## ✅ **Security Features Implemented**

### **1. Input Security & Sanitization**
- ✅ **Prompt Injection Protection**: Filters dangerous patterns like "ignore previous instructions"
- ✅ **XSS Prevention**: Removes script tags and JavaScript injections
- ✅ **SQL Injection Protection**: Sanitizes database-related patterns
- ✅ **Input Length Limiting**: Prevents buffer overflow attacks
- ✅ **Special Character Filtering**: Removes potentially harmful characters

### **2. Output Validation & Content Safety**
- ✅ **Harmful Content Detection**: Blocks violence, explicit content, scary material
- ✅ **PII Protection**: Prevents personal information leakage
- ✅ **Medical Advice Filtering**: Blocks inappropriate medical content
- ✅ **Content Length Validation**: Ensures proper story length
- ✅ **Safe Fallback Stories**: Pre-validated backup content

### **3. User Data Protection**
- ✅ **Name Sanitization**: Validates and cleans user names
- ✅ **Email Protection**: Prevents email exposure in logs
- ✅ **Content Hashing**: Safe logging without data exposure
- ✅ **Preference Encryption**: Secure storage of user preferences

### **4. Rate Limiting & DoS Protection**
- ✅ **Per-IP Rate Limiting**: Prevents abuse from single sources
- ✅ **Endpoint-Specific Limits**: Different limits for different features
- ✅ **Graceful Error Handling**: User-friendly rate limit messages
- ✅ **Memory-Efficient Tracking**: Automatic cleanup of old requests

### **5. Security Headers & HTTPS**
- ✅ **Content Security Policy (CSP)**: Prevents XSS attacks
- ✅ **HSTS Headers**: Enforces HTTPS connections
- ✅ **X-Frame-Options**: Prevents clickjacking
- ✅ **X-Content-Type-Options**: Prevents MIME sniffing
- ✅ **Referrer Policy**: Controls referrer information

### **6. Security Monitoring & Logging**
- ✅ **Comprehensive Audit Trail**: All security events logged
- ✅ **Suspicious Activity Detection**: Automatic threat identification
- ✅ **Safe Logging Practices**: No sensitive data in logs
- ✅ **Security Event Classification**: Different severity levels

---

## 🚀 **Quick Start - Security Setup**

### **1. Environment Configuration**
```bash
# Copy the security template
cp .env.security.template .env

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Update .env with your keys
ENCRYPTION_KEY=your-generated-key-here
JWT_SECRET_KEY=your-jwt-secret-change-me
```

### **2. Install Security Dependencies**
```bash
pip install cryptography slowapi redis
```

### **3. Test Security Features**
```bash
# Run security test suite
python test_security.py
```

### **4. Enable Security in Production**
```bash
# Set production environment
ENVIRONMENT=production
DEBUG_MODE=false
CONTENT_VALIDATION_ENABLED=true
PROMPT_INJECTION_PROTECTION=true
```

---

## 🔧 **Configuration Options**

### **Rate Limiting**
```bash
API_RATE_LIMIT_REQUESTS_PER_MINUTE=60  # Requests per minute
API_RATE_LIMIT_BURST_SIZE=10           # Burst allowance
```

### **Content Security**
```bash
CONTENT_VALIDATION_ENABLED=true       # Enable content filtering
OUTPUT_VALIDATION_ENABLED=true        # Validate AI outputs
PROMPT_INJECTION_PROTECTION=true      # Block prompt injections
```

### **AI Model Security**
```bash
AI_MODEL_TIMEOUT=30                    # Request timeout (seconds)
AI_MODEL_MAX_TOKENS=2000              # Maximum tokens per request
AI_MODEL_TEMPERATURE_LIMIT=1.0        # Maximum creativity level
```

---

## 🛡️ **Security Best Practices**

### **For Development**
1. **Always use the security test suite** before deploying changes
2. **Keep sensitive data out of logs** using the hashing functions
3. **Test with malicious inputs** to verify sanitization works
4. **Monitor security logs** for suspicious activity
5. **Use HTTPS in all environments** including development

### **For Production**
1. **Change all default keys** in .env file
2. **Enable all security features** (validation, rate limiting, etc.)
3. **Set up proper logging** and monitoring
4. **Use secure database connections** with encryption
5. **Regularly update dependencies** for security patches

### **For Scaling**
1. **Use Redis for distributed rate limiting** across multiple servers
2. **Implement proper session management** with secure tokens
3. **Set up centralized security monitoring** and alerting
4. **Use a Web Application Firewall (WAF)** for additional protection
5. **Regular security audits** and penetration testing

---

## 🔍 **Security Testing Checklist**

### **Before Each Deployment**
- [ ] Run `python test_security.py` successfully
- [ ] Verify all environment variables are set
- [ ] Check that rate limiting is working
- [ ] Test input sanitization with malicious inputs
- [ ] Validate output filtering is active
- [ ] Confirm security headers are present
- [ ] Review security logs for anomalies

### **Monthly Security Review**
- [ ] Update dependencies for security patches
- [ ] Review and rotate encryption keys
- [ ] Analyze security logs for patterns
- [ ] Test disaster recovery procedures
- [ ] Update security documentation
- [ ] Verify backup security measures

---

## 🚨 **Incident Response**

### **If Security Breach Detected**
1. **Immediate Actions**:
   - Enable maintenance mode
   - Block suspicious IP addresses
   - Review security logs
   - Document the incident

2. **Investigation**:
   - Analyze attack vectors
   - Identify affected data
   - Check for data exfiltration
   - Assess system integrity

3. **Recovery**:
   - Patch security vulnerabilities
   - Update security configurations
   - Monitor for continued attacks
   - Communicate with users if needed

### **Security Contact Information**
- **Security Team**: security@morpheus-ai.com
- **Emergency Contact**: +1-XXX-XXX-XXXX
- **Incident Reporting**: incidents@morpheus-ai.com

---

## 📊 **Security Metrics & Monitoring**

### **Key Security Indicators**
- Rate limit violations per hour
- Suspicious input attempts per day
- Failed authentication attempts
- Content filtering blocks
- Security event severity distribution

### **Alerting Thresholds**
- **High**: >100 suspicious inputs per hour
- **Medium**: >50 rate limit violations per hour
- **Low**: Any successful prompt injection attempts

---

## 🔄 **Security Updates & Maintenance**

### **Regular Tasks**
- **Daily**: Review security logs and alerts
- **Weekly**: Update security configurations if needed
- **Monthly**: Security dependency updates
- **Quarterly**: Complete security audit and testing

### **Version History**
- **v1.0**: Initial security implementation
- **v1.1**: Enhanced input sanitization
- **v1.2**: Advanced rate limiting with Redis support
- **v2.0**: Comprehensive security monitoring (Current)

---

## 📞 **Support & Resources**

### **Documentation**
- [FastAPI Security Guide](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.org/dev/security/)

### **Security Tools**
- [Bandit](https://bandit.readthedocs.io/) - Python security linter
- [Safety](https://github.com/pyupio/safety) - Dependency vulnerability scanner
- [Semgrep](https://semgrep.dev/) - Static analysis security scanner

---

*Last Updated: December 2024*
*Security Implementation Version: 2.0*