import requests
from typing import List, Dict, Optional
from .config import API_BASE_URL


class APIClient:
    """Django API bilan aloqa qilish uchun klient"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
    
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """GET so'rov"""
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API xatolik: {e}")
            return {}
    
    def _post(self, endpoint: str, data: dict) -> dict:
        """POST so'rov"""
        try:
            response = requests.post(f"{self.base_url}/{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API xatolik: {e}")
            return {}
    
    # Foydalanuvchilar
    def register_user(self, telegram_id: int, username: str, full_name: str) -> dict:
        """Foydalanuvchini ro'yxatdan o'tkazish"""
        return self._post('users/register/', {
            'telegram_id': telegram_id,
            'username': username,
            'full_name': full_name
        })
    
    def mark_subscribed(self, telegram_id: int) -> dict:
        """Foydalanuvchini obuna bo'lgan deb belgilash"""
        return self._post(f'users/{telegram_id}/mark_subscribed/', {})
    
    def check_subscription(self, telegram_id: int, poll_id: int = None) -> dict:
        """Obuna holatini tekshirish"""
        data = {'telegram_id': telegram_id}
        if poll_id:
            data['poll_id'] = poll_id
        return self._post('check-subscription/', data)
    
    # Kanallar
    def get_channels(self) -> List[Dict]:
        """Barcha faol kanallarni olish"""
        result = self._get('channels/')
        return result.get('results', [])
    
    # So'rovnomalar
    def get_polls(self) -> List[Dict]:
        """Barcha faol so'rovnomalarni olish"""
        result = self._get('polls/')
        return result.get('results', [])
    
    # Viloyatlar
    def get_regions(self, poll_id: int = None) -> List[Dict]:
        """Poll bo'yicha viloyatlarni olish"""
        if poll_id:
            result = self._get(f'polls/{poll_id}/regions/')
            return result if isinstance(result, list) else []
        result = self._get('regions/')
        return result.get('results', [])
    
    # Tumanlar
    def get_districts_by_region(self, region_id: int) -> List[Dict]:
        """Viloyat bo'yicha tumanlarni olish"""
        return self._get('districts/by_region/', {'region_id': region_id})
    
    # Nomzodlar
    def get_candidates_by_district(self, district_id: int) -> List[Dict]:
        """Tuman bo'yicha nomzodlarni olish"""
        return self._get('candidates/by_district/', {'district_id': district_id})
    
    # Ovoz berish
    def submit_vote(self, telegram_id: int, poll_id: int, candidate_id: int) -> dict:
        """Ovoz berish"""
        return self._post('votes/', {
            'telegram_id': telegram_id,
            'poll_id': poll_id,
            'candidate_id': candidate_id
        })
    
    # Statistika
    def get_statistics(self) -> dict:
        """Umumiy statistikani olish"""
        return self._get('statistics/')
