#!/usr/bin/env python3
"""Simulate Java/Gradle HTTP HEAD via python with forced IPv4 (to mimic preferIPv4Stack=true)."""
import sys, socket, urllib.request, urllib.error

urls = [
    "https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/2.0.21/kotlin-stdlib-2.0.21.pom",
    "https://maven.google.com/org/jetbrains/kotlin/kotlin-stdlib/2.0.21/kotlin-stdlib-2.0.21.pom",
    "https://plugins.gradle.org/m2/org/jetbrains/kotlin/kotlin-gradle-plugin/2.0.21/kotlin-gradle-plugin-2.0.21.pom",
    "https://maven.aliyun.com/repository/public/org/jetbrains/kotlin/kotlin-stdlib/2.0.21/kotlin-stdlib-2.0.21.pom",
]

# Monkey-patch socket to ONLY return IPv4 → emulate -Djava.net.preferIPv4Stack=true
_orig_getaddrinfo = socket.getaddrinfo
def only_ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = only_ipv4_getaddrinfo

for u in urls:
    try:
        req = urllib.request.Request(u, method="HEAD", headers={"User-Agent":"curl/8.8.0"})
        r = urllib.request.urlopen(req, timeout=15)
        print(f"OK HTTP {r.status} {u}")
        print(f"   Length: {r.headers.get('Content-Length','?')}")
    except urllib.error.HTTPError as e:
        ok = 200 <= e.code < 400 or e.code == 404 or e.code == 405
        print(f"{'OK' if ok else 'FAIL'} HTTP {e.code} {u}")
    except Exception as e:
        print(f"FAIL {u}: {type(e).__name__}: {e}")
