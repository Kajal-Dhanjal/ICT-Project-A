import hashlib
import requests

# ✅ Check if the given password has been found in known data breaches via Have I Been Pwned (HIBP)
def check_pwned_password(password: str) -> bool:
    """
    Returns True if password has been pwned, else False.
    Implements k-Anonymity using SHA-1 hashing (safe, no full password ever leaves the server).
    """
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    try:
        response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=5)
        if response.status_code != 200:
            raise ConnectionError("Failed to fetch data from HIBP API")

        hashes = (line.split(":") for line in response.text.splitlines())
        return any(stored_suffix == suffix for stored_suffix, _ in hashes)

    except Exception as e:
        print(f"HIBP check error: {e}")
        return False  # Fallback to allow registration if HIBP API is unavailable
