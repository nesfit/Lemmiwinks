import socket
import urllib3.util

def get_netinfo(url: str):
    url_parts = urllib3.util.parse_url(url)
    info = socket.getaddrinfo(url_parts.host, url_parts.port)
    ipv4 = set()
    ipv6 = set()

    for i in info:
        if i[0] == socket.AF_INET6:
            ipv6.add(i[4][0])
        elif i[0] == socket.AF_INET:
            ipv4.add(i[4][0])

    return ipv4, ipv6

