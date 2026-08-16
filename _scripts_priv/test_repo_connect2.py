#!/usr/bin/env python3
"""Force IPv4 only → test connectivity for key URLs (AGP on mavenCentral? androidx on mavenCentral? aliyun dl.google proxy?)."""
import socket, urllib.request, urllib.error

urls = [
    # kotlin-stdlib on mavenCentral (required for buildSrc)
    ("mavenCentral: kotlin-stdlib 2.0.21 pom",
     "https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/2.0.21/kotlin-stdlib-2.0.21.pom"),
    # AGP on mavenCentral?
    ("mavenCentral: AGP 8.5.0 pom",
     "https://repo.maven.apache.org/maven2/com/android/tools/build/gradle/8.5.0/gradle-8.5.0.pom"),
    # androidx.appcompat on mavenCentral?
    ("mavenCentral: appcompat 1.7.0 pom",
     "https://repo.maven.apache.org/maven2/androidx/appcompat/appcompat/1.7.0/appcompat-1.7.0.pom"),
    # kotlin on aliyun public (fallback)
    ("aliyun public: kotlin-stdlib 2.0.21 pom",
     "https://maven.aliyun.com/repository/public/org/jetbrains/kotlin/kotlin-stdlib/2.0.21/kotlin-stdlib-2.0.21.pom"),
    # aliyun google proxy (dl.google.com → maven.aliyun.com/repository/google)
    ("aliyun google: appcompat 1.7.0 pom",
     "https://maven.aliyun.com/repository/google/androidx/appcompat/appcompat/1.7.0/appcompat-1.7.0.pom"),
    # aliyun google proxy: AGP 8.5.0
    ("aliyun google: AGP 8.5.0 pom",
     "https://maven.aliyun.com/repository/google/com/android/tools/build/gradle/8.5.0/gradle-8.5.0.pom"),
    # direct dl.google.com (this is the one FAILING)
    ("dl.google.com direct: appcompat 1.7.0 pom (TIMEOUT EXPECTED)",
     "https://dl.google.com/dl/android/maven2/androidx/appcompat/appcompat/1.7.0/appcompat-1.7.0.pom"),
    # jitpack basic
    ("jitpack jitpack.io root",
     "https://jitpack.io/builds.txt"),
]

_orig_getaddrinfo = socket.getaddrinfo
def only_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = only_ipv4

for name, u in urls:
    tag = "⏱ " if "TIMEOUT EXPECTED" in name else ""
    try:
        req = urllib.request.Request(u, method="HEAD", headers={"User-Agent":"curl/8.8.0"})
        timeout = 6 if "TIMEOUT EXPECTED" in name else 15
        r = urllib.request.urlopen(req, timeout=timeout)
        print(f"{tag}✅ {name}\n   → HTTP {r.status}  len={r.headers.get('Content-Length','?')}")
    except urllib.error.HTTPError as e:
        ok = 200 <= e.code < 400 or e.code == 404 or e.code == 405
        print(f"{tag}{'✅' if ok else '❌'} {name}  HTTP {e.code}")
    except Exception as e:
        print(f"{tag}❌ {name}  {type(e).__name__}: {str(e)[:120]}")
    print()
