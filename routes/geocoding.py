"""
Geocoding helper for the Property Location Map feature.

Uses OpenStreetMap's Nominatim search API to turn a free-text address into
latitude/longitude. Nominatim is free and requires no API key, which keeps
this feature cost-free to run and simple to maintain (per the project's
"cost-effective and easy to maintain" requirement).

Nominatim's usage policy (https://operations.osmfoundation.org/policies/nominatim/)
asks for a descriptive User-Agent and no more than ~1 request/second, which is
fine here since geocoding only runs once, synchronously, when a property is
created or edited -- not on every page view.

If a lookup fails for any reason (no network, address not found, rate limit),
this returns (None, None) rather than raising, so saving a property never
breaks just because geocoding didn't work.
"""
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "PropVerify-PropertyVerificationApp/1.0 (contact: admin@example.com)"
TIMEOUT_SECONDS = 5


def geocode_address(address_text):
    """
    Returns (latitude, longitude) as floats, or (None, None) if the address
    could not be resolved.
    """
    if not address_text or not address_text.strip():
        return None, None

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": address_text, "format": "json", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            return None, None

        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
        return lat, lon
    except Exception:  # noqa: BLE001 - any geocoding failure should degrade gracefully
        return None, None
