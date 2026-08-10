import logging
import requests
from decimal import Decimal
from django.core.cache import cache

logger = logging.getLogger(__name__)

CITIES_CACHE_KEY = 'pk_cities_list'
CACHE_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days

FLAT_SHIPPING_COST = Decimal('299.00')

FALLBACK_CITIES = [
    'Attock', 'Bahawalpur', 'Bhakkar', 'Chiniot', 'Dera Ghazi Khan',
    'Faisalabad', 'Gujranwala', 'Gujrat', 'Hyderabad', 'Islamabad',
    'Jhang', 'Karachi', 'Kasur', 'Lahore', 'Larkana', 'Mardan',
    'Mirpur Khas', 'Multan', 'Murree', 'Nawabshah', 'Okara',
    'Peshawar', 'Quetta', 'Rahim Yar Khan', 'Rawalpindi', 'Sahiwal',
    'Sargodha', 'Sheikhupura', 'Sialkot', 'Sukkur', 'Vehari'
]


def fetch_pakistan_cities():
    cached = cache.get(CITIES_CACHE_KEY)
    if cached:
        return cached

    try:
        response = requests.post(
            'https://countriesnow.space/api/v0.1/countries/cities',
            json={'country': 'Pakistan'},
            timeout=4,
        )
        response.raise_for_status()
        data = response.json()

        if data.get('error') is False and data.get('data'):
            cities = sorted(data['data'])
            cache.set(CITIES_CACHE_KEY, cities, CACHE_TTL_SECONDS)
            return cities

        raise ValueError('Unexpected API response structure')

    except (requests.RequestException, ValueError) as exc:
        logger.warning(f'Failed to fetch live city list, using fallback: {exc}')
        return sorted(FALLBACK_CITIES)