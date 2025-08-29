# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| >= 2.1.0   | ✅     |
| <= 2.0.0   | ❌     |

## Reporting a Vulnerability

To report a security vulnerability:

1. **DO NOT** open a public issue
2. Send an email to **egydiobolonhezi@gmail.com** with:
   - Detailed description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Fix suggestions (if any)

### What to Expect

- **Confirmation**: Response within 48 hours
- **Analysis**: Complete investigation within 7 business days
- **Fix**: Patch released according to severity
- **Disclosure**: Communication about the resolution

### Types of Vulnerabilities

We are particularly interested in reports about:

- Arbitrary code execution
- Sensitive information leakage
- Git command injection
- Input validation issues
- Dependency chain vulnerabilities

### Response Process

1. **Triage**: We assess validity and severity
2. **Development**: We create a fix
3. **Testing**: We validate the solution
4. **Release**: We publish a patched version
5. **Communication**: We notify about the fix

### Recognition

Contributors who report valid vulnerabilities will be:
- Credited in the changelog (if desired)
- Mentioned in acknowledgments
- Informed about fix progress

## Security Best Practices

### For Users
- Keep CCG always updated
- Use only on trusted repositories
- Check permissions before execution
- Don't use shared credentials

### For Developers
- Validate all user inputs
- Use subprocess with safe parameters
- Sanitize Git commands
- Keep dependencies updated

## Security History

- **2025-08**: Release of v2.1.0 with security improvements
- **2023-12**: Implementation of security policy

For more information about security, see the [documentation](README.md) or contact us.
