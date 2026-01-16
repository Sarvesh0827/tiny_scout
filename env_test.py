import sys
print(f"Python: {sys.version}")

try:
    import httpx
    print("httpx imported successfully")
except Exception as e:
    print(f"httpx failed: {e}")

try:
    import urllib.request
    print("urllib imported successfully")
except Exception as e:
    print(f"urllib failed: {e}")
