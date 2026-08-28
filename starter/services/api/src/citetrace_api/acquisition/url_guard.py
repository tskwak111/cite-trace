import asyncio
import ipaddress
import socket
from enum import StrEnum
from urllib.parse import urlparse


class UrlDenialCode(StrEnum):
    SCHEME_NOT_ALLOWED = "SCHEME_NOT_ALLOWED"
    CREDENTIALS_NOT_ALLOWED = "CREDENTIALS_NOT_ALLOWED"
    PORT_NOT_ALLOWED = "PORT_NOT_ALLOWED"
    HOST_NOT_ALLOWED = "HOST_NOT_ALLOWED"
    PRIVATE_ADDRESS = "PRIVATE_ADDRESS"
    DNS_RESOLUTION_FAILED = "DNS_RESOLUTION_FAILED"
    REDIRECT_LIMIT_EXCEEDED = "REDIRECT_LIMIT_EXCEEDED"
    DNS_REBINDING_DETECTED = "DNS_REBINDING_DETECTED"

class UrlValidationError(Exception):
    def __init__(self, code: UrlDenialCode, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")

class ValidatedRemoteLocation:
    def __init__(self, url: str, canonical_host: str, resolved_ips: tuple[str, ...], port: int, scheme: str):
        self.url = url
        self.canonical_host = canonical_host
        self.resolved_ips = resolved_ips
        self.port = port
        self.scheme = scheme

class UrlGuard:
    def __init__(self, require_https: bool = True):
        self.require_https = require_https

    async def validate(self, url: str) -> ValidatedRemoteLocation:
        parsed = urlparse(url)
        
        # Check scheme
        if not parsed.scheme:
            raise UrlValidationError(UrlDenialCode.SCHEME_NOT_ALLOWED, "No scheme provided")
            
        allowed_schemes = ["https"] if self.require_https else ["http", "https"]
        if parsed.scheme.lower() not in allowed_schemes:
            raise UrlValidationError(UrlDenialCode.SCHEME_NOT_ALLOWED, f"Scheme {parsed.scheme} not allowed")

        # Check credentials
        if parsed.username or parsed.password:
            raise UrlValidationError(UrlDenialCode.CREDENTIALS_NOT_ALLOWED, "Credentials not allowed in URL")

        # Check host
        if not parsed.hostname:
            raise UrlValidationError(UrlDenialCode.HOST_NOT_ALLOWED, "No hostname provided")

        # Check port
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme.lower() == "https" else 80
        if port not in (80, 443):
            raise UrlValidationError(UrlDenialCode.PORT_NOT_ALLOWED, f"Port {port} not allowed")

        # DNS resolution and IP validation
        loop = asyncio.get_running_loop()
        try:
            # getaddrinfo returns a list of 5-tuples: (family, type, proto, canonname, sockaddr)
            # sockaddr is (address, port) for IPv4 or (address, port, flow info, scope id) for IPv6
            addr_info = await loop.getaddrinfo(parsed.hostname, port, proto=socket.IPPROTO_TCP)
        except socket.gaierror as e:
            raise UrlValidationError(UrlDenialCode.DNS_RESOLUTION_FAILED, f"DNS resolution failed for {parsed.hostname}") from e

        resolved_ips = []
        for info in addr_info:
            ip_str = info[4][0]
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue
                
            if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or str(ip) == "255.255.255.255":
                raise UrlValidationError(UrlDenialCode.PRIVATE_ADDRESS, f"IP {ip_str} is not a public address")
                
            resolved_ips.append(ip_str)
            
        if not resolved_ips:
            raise UrlValidationError(UrlDenialCode.DNS_RESOLUTION_FAILED, f"No valid IPs found for {parsed.hostname}")

        return ValidatedRemoteLocation(
            url=url,
            canonical_host=parsed.hostname,
            resolved_ips=tuple(resolved_ips),
            port=port,
            scheme=parsed.scheme.lower()
        )
