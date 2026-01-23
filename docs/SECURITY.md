# Security Policy

## Overview

This document outlines the security features, best practices, and guidelines for the Jarvis AI Assistant project.

## Threat Model

Jarvis is designed for **personal, local use** on trusted devices. The security model assumes:

- **Trusted User**: The user running Jarvis is authorized and trusted
- **Local Network**: Frontend and backend run on the same machine or trusted local network
- **System Access**: Jarvis has legitimate need for system control (volume, apps, browser)

### Key Threats Mitigated

1. **Command Injection** - Prevented through subprocess usage and input validation
2. **Unauthorized Access** - Limited by CORS and network isolation
3. **Input Abuse** - Controlled through length limits and sanitization
4. **Denial of Service** - Mitigated by rate limiting and caching

## Implemented Security Features

### 1. Command Injection Prevention

**Risk**: Malicious commands executed through system agent

**Mitigation**:

- ✅ Application whitelist enforced in `system_tools.py`
- ✅ Use of `subprocess.run()` with `shell=False` instead of `os.system()`
- ✅ Input sanitization and validation
- ✅ Security logging of all system commands

**Whitelisted Applications**:

```python
# Windows: notepad, calc, mspaint, explorer, chrome, firefox, etc.
# See system_tools.py for full list
```

### 2. Input Validation & Sanitization

All user inputs are validated:

- **Command length**: Max 500 characters
- **Query length**: Max 500 characters for searches, 200 for media
- **URL validation**: Only HTTP/HTTPS schemes allowed, max 2048 chars
- **Empty input checks**: Reject null/empty commands

### 3. CORS Security

**Default Configuration**:

```python
ALLOWED_ORIGINS = ["http://localhost:5173"]  # Development
```

**Production Setup**:

```bash
# Set environment variable for production
export JARVIS_FRONTEND_URL="https://yourdomain.com"
```

### 4. Rate Limiting & Caching

- **Search caching**: 5-minute TTL, max 50 cached queries
- **Exponential backoff**: 1s, 2s, 4s retry delays
- **Request timeout**: 10 seconds max
- **Message size limit**: 10KB for WebSocket messages

### 5. Security Logging

All security-relevant events are logged to:

- `jarvis_security.log` - Security events (system commands, validation failures)
- `jarvis_api.log` - API requests and WebSocket connections

**Logged Events**:

- ✅ All routed commands
- ✅ Failed validation attempts
- ✅ Application launch requests
- ✅ Suspicious input (length violations, invalid URLs)
- ✅ WebSocket connections/disconnections

## Configuration Recommendations

### Production Deployment

1. **Set CORS Origins**:

   ```bash
   export JARVIS_FRONTEND_URL="https://your-frontend.com,https://backup.com"
   ```

2. **Review Application Whitelist**:
   Edit `jarvis_core/tools/system_tools.py` and add/remove apps as needed.

3. **Enable HTTPS** (if exposing beyond localhost):

   ```python
   # In server.py if __name__ == "__main__":
   uvicorn.run(app, host="localhost", port=8000,
               ssl_keyfile="./key.pem",
               ssl_certfile="./cert.pem")
   ```

4. **Monitor Logs**:
   Regularly review `jarvis_security.log` for suspicious activity.

### Network Isolation

For maximum security, run Jarvis only on localhost:

```bash
export JARVIS_HOST="127.0.0.1"  # Only accept local connections
export JARVIS_PORT="8000"
```

## Security Best Practices

### For Users

1. ✅ **Run on trusted devices only**
2. ✅ **Review application whitelist** before allowing new apps
3. ✅ **Monitor security logs** periodically
4. ✅ **Use localhost binding** unless remote access is required
5. ✅ **Keep dependencies updated** (`pip install -r requirements.txt --upgrade`)

### For Developers

1. ✅ **Never use `os.system()` or `eval()`** - Use subprocess with validated inputs
2. ✅ **Always validate user input** - Check length, format, and content
3. ✅ **Log security events** - Use the configured logging framework
4. ✅ **Maintain whitelist approach** - Allow only known-good, deny by default
5. ✅ **Test security features** - Verify input validation works

## Vulnerability Disclosure

If you discover a security vulnerability in Jarvis:

1. **Do NOT** open a public GitHub issue
2. Email the maintainer with details
3. Allow reasonable time for a fix before public disclosure
4. You will be credited in the fix acknowledgment

## Security Updates

This project follows semantic versioning. Security updates will be marked as:

- **PATCH** (0.0.X): Security bug fixes
- **MINOR** (0.X.0): Security improvements, new validations
- **MAJOR** (X.0.0): Breaking changes, major security overhauls

## Limitations & Known Risks

### Accepted Risks

1. **Local System Access**: Jarvis intentionally has system control capabilities
2. **No Authentication**: Designed for single-user, local use (no multi-user auth)
3. **Limited Rate Limiting**: Basic caching only, not enterprise-grade DoS protection

### Out of Scope

The following are **not** protected against:

- ❌ Malicious frontend code (trust your frontend)
- ❌ Compromised dependencies (use trusted sources)
- ❌ Physical access attacks (OS-level security responsibility)

## Compliance

This is personal software with no specific compliance requirements. Users deploying in regulated environments should:

- Review applicable regulations (GDPR, HIPAA, etc.)
- Implement additional controls as needed
- Consult legal/compliance teams

## Questions?

For security-related questions, see:

- [README.md](README.md) - General usage and setup
- [USER_GUIDE.md](USER_GUIDE.md) - User instructions
- GitHub Issues - For non-sensitive questions

---

**Last Updated**: January 2026  
**Version**: 2.0
