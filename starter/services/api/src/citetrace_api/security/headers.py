def get_security_headers(env: str = "development") -> dict[str, str]:
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }
    
    if env == "production":
        headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    else:
        headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline'; frame-ancestors 'none';"
        
    return headers
