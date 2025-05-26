import requests
import json
from datetime import datetime, timedelta
from database import Database
from config import Config

class CurrencyAPI:
    def __init__(self):
        self.db = Database()
        self.api_url = Config.CURRENCY_API_URL
        self.supported_currencies = Config.SUPPORTED_CURRENCIES
        
    def get_exchange_rate(self, from_currency, to_currency):
        """Get exchange rate between two currencies"""
        try:
            # First check if we have a recent rate in database
            cached_rate = self.db.get_exchange_rate(from_currency, to_currency)
            if cached_rate:
                return float(cached_rate)
            
            # If not cached or outdated, fetch from API
            rate = self.fetch_from_api(from_currency, to_currency)
            if rate:
                # Cache the rate in database
                self.db.update_exchange_rate(from_currency, to_currency, rate)
                return rate
            
            # Fallback to hardcoded rates if API fails
            return self.get_fallback_rate(from_currency, to_currency)
            
        except Exception as e:
            print(f"Error getting exchange rate: {e}")
            self.db.log_error("currency_api_error", str(e))
            return self.get_fallback_rate(from_currency, to_currency)
    
    def fetch_from_api(self, from_currency, to_currency):
        """Fetch exchange rate from external API"""
        try:
            # Using a free API service (exchangerate-api.com)
            url = f"{self.api_url}{from_currency}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'rates' in data and to_currency in data['rates']:
                    return float(data['rates'][to_currency])
            
            return None
            
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            return None
    
    def get_fallback_rate(self, from_currency, to_currency):
        """Fallback exchange rates when API is unavailable"""
        fallback_rates = {
            ('GBP', 'USD'): 1.2650,
            ('GBP', 'EUR'): 1.1580,
            ('GBP', 'BRL'): 6.2450,
            ('GBP', 'JPY'): 188.75,
            ('GBP', 'TRY'): 37.85,
            ('USD', 'GBP'): 0.7905,
            ('USD', 'EUR'): 0.9155,
            ('USD', 'BRL'): 4.9380,
            ('USD', 'JPY'): 149.25,
            ('USD', 'TRY'): 29.92,
            ('EUR', 'GBP'): 0.8635,
            ('EUR', 'USD'): 1.0925,
            ('EUR', 'BRL'): 5.3940,
            ('EUR', 'JPY'): 163.05,
            ('EUR', 'TRY'): 32.70,
            ('BRL', 'GBP'): 0.1601,
            ('BRL', 'USD'): 0.2025,
            ('BRL', 'EUR'): 0.1854,
            ('BRL', 'JPY'): 30.22,
            ('BRL', 'TRY'): 6.06,
            ('JPY', 'GBP'): 0.0053,
            ('JPY', 'USD'): 0.0067,
            ('JPY', 'EUR'): 0.0061,
            ('JPY', 'BRL'): 0.0331,
            ('JPY', 'TRY'): 0.2005,
            ('TRY', 'GBP'): 0.0264,
            ('TRY', 'USD'): 0.0334,
            ('TRY', 'EUR'): 0.0306,
            ('TRY', 'BRL'): 0.1650,
            ('TRY', 'JPY'): 4.985
        }
        
        # Same currency
        if from_currency == to_currency:
            return 1.0
        
        # Direct rate
        if (from_currency, to_currency) in fallback_rates:
            return fallback_rates[(from_currency, to_currency)]
        
        # Inverse rate
        if (to_currency, from_currency) in fallback_rates:
            return 1.0 / fallback_rates[(to_currency, from_currency)]
        
        # Cross rate via USD
        if from_currency != 'USD' and to_currency != 'USD':
            usd_from = fallback_rates.get((from_currency, 'USD'))
            usd_to = fallback_rates.get(('USD', to_currency))
            if usd_from and usd_to:
                return usd_from * usd_to
        
        # Default fallback
        return 1.0
    
    def update_all_rates(self):
        """Update all supported currency pairs"""
        updated_count = 0
        for base in self.supported_currencies:
            for target in self.supported_currencies:
                if base != target:
                    rate = self.fetch_from_api(base, target)
                    if rate:
                        self.db.update_exchange_rate(base, target, rate)
                        updated_count += 1
        
        print(f"Updated {updated_count} exchange rates")
        return updated_count
    
    def get_all_rates_for_currency(self, base_currency):
        """Get all exchange rates for a base currency"""
        rates = {}
        for target_currency in self.supported_currencies:
            if target_currency != base_currency:
                rates[target_currency] = self.get_exchange_rate(base_currency, target_currency)
        return rates
