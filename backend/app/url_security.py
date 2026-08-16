import ipaddress
import os
import socket
from urllib.parse import urlparse

from fastapi import HTTPException


def validate_public_http_url(url: str) -> str:
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {exc}")

    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=400,
            detail="Only http:// and https:// URLs are allowed",
        )

    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL hostname is required")

    if parsed.username or parsed.password:
        raise HTTPException(
            status_code=400,
            detail="URLs containing credentials are not allowed",
        )

    allowed_ports = {
        int(x.strip())
        for x in os.getenv("CRAWLER_ALLOWED_PORTS", "80,443").split(",")
        if x.strip().isdigit()
    }

    if parsed.port and parsed.port not in allowed_ports:
        raise HTTPException(
            status_code=400,
            detail=f"Port {parsed.port} is not allowed",
        )

    hostname = parsed.hostname.lower()

    if hostname in {"localhost", "localhost.localdomain"}:
        raise HTTPException(status_code=400, detail="Localhost URLs are blocked")

    try:
        addresses = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Hostname could not be resolved")

    for address in addresses:
        ip_text = address[4][0]
        try:
            ip = ipaddress.ip_address(ip_text)
        except ValueError:
            continue

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise HTTPException(
                status_code=400,
                detail="Private or non-public network destinations are blocked",
            )

    return url
