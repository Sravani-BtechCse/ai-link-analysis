import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException

def validate_public_url(url: str) -> str:
    """Allow only public HTTP(S) destinations and reject private/internal hosts."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=422, detail="Only http and https URLs are supported.")
    if not parsed.hostname:
        raise HTTPException(status_code=422, detail="URL must include a hostname.")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise HTTPException(status_code=400, detail="Local and internal hosts are not allowed.")
    try:
        literal_ip = ipaddress.ip_address(host)
        addresses = [literal_ip]
    except ValueError:
        try:
            records = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80),
                                         type=socket.SOCK_STREAM)
            addresses = [ipaddress.ip_address(record[4][0]) for record in records]
        except socket.gaierror:
            raise HTTPException(status_code=400, detail="Website hostname could not be resolved.")
    for address in addresses:
        if not address.is_global:
            raise HTTPException(status_code=400, detail="Private, loopback, reserved, or internal IPs are not allowed.")
    return url
