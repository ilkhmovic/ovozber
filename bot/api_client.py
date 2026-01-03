import requests
from typing import List, Dict, Optional
import logging
from bot.config import API_BASE_URL

logger = logging.getLogger(__name__)


class APIClient:
    """Django API bilan aloqa qilish uchun klient"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        # Use .strip() to remove hidden characters like \r or spaces from .env
        self.base_url = str(base_url).strip().rstrip('/')
        self.is_internal = self.base_url.upper() == 'INTERNAL'
        
        if self.is_internal:
            import os
            # Allow ORM calls from async context (Telegram bot event loop)
            os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
            logger.info("APIClient is running in INTERNAL mode (Direct ORM access) with ASYNC_UNSAFE=true")
        else:
            logger.info(f"APIClient initialized with base_url: {self.base_url}")

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """GET so'rov"""
        if self.is_internal:
            return self._handle_internal_get(endpoint, params)

        try:
            url = f"{self.base_url}/{endpoint}"
            logger.debug(f"GET request to: {url} with params: {params}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Response: {result}")
            return result
        except requests.RequestException as e:
            logger.error(f"API GET error: {e}")
            print(f"API xatolik: {e}")
            return {}
    
    def _post(self, endpoint: str, data: dict) -> dict:
        """POST so'rov"""
        if self.is_internal:
            return self._handle_internal_post(endpoint, data)

        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.post(url, json=data)
            try:
                response.raise_for_status()
            except requests.HTTPError as http_err:
                try:
                    return response.json()
                except Exception:
                    logger.error(f"HTTP error: {http_err}")
                    print(f"API xatolik: {http_err}")
                    return {}
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API POST error: {e}")
            print(f"API xatolik: {e}")
            return {}

    def _handle_internal_get(self, endpoint: str, params: dict = None) -> dict:
        """Internal Django logic for GET"""
        from django.db import close_old_connections
        from api.models import Channel, Poll, Region, District, Candidate, TelegramUser, Vote
        
        try:
            # Clean up old/broken connections before query
            close_old_connections()
            
            # Clean endpoint for matching
            clean_ep = endpoint.strip('/')
            
            if clean_ep == 'channels':
                channels = Channel.objects.filter(is_active=True)
                return {'results': [{'id': c.id, 'channel_id': c.channel_id, 'channel_username': c.channel_username, 'title': c.title} for c in channels]}
            
            if clean_ep == 'polls':
                polls = Poll.objects.filter(is_active=True)
                return {'results': [{'id': p.id, 'title': p.title, 'is_open': p.is_open()} for p in polls]}
            
            if clean_ep.startswith('polls/') and clean_ep.endswith('/regions'):
                poll_id = clean_ep.split('/')[1]
                regions = Region.objects.filter(poll_id=poll_id, is_active=True)
                return [{'id': r.id, 'name': r.name} for r in regions]
            
            if clean_ep == 'districts/by_region':
                region_id = params.get('region_id')
                districts = District.objects.filter(region_id=region_id, is_active=True)
                return [{'id': d.id, 'name': d.name} for d in districts]
            
            if clean_ep == 'candidates/by_district':
                district_id = params.get('district_id')
                candidates = Candidate.objects.filter(district_id=district_id, is_active=True)
                return [{'id': c.id, 'full_name': c.full_name, 'position': c.position, 'vote_count': c.vote_count} for c in candidates]
            
            # Candidate detail: candidates/ID or just ID
            if clean_ep.startswith('candidates/') or clean_ep.isdigit():
                candidate_id = clean_ep.split('/')[-1]
                c = Candidate.objects.get(id=candidate_id)
                return {
                    'id': c.id, 'full_name': c.full_name, 'position': c.position, 
                    'bio': c.bio, 'photo': c.photo.url if c.photo else None
                }

            if clean_ep == 'statistics':
                return {
                    'total_users': TelegramUser.objects.count(),
                    'total_votes': Vote.objects.count()
                }

        except Exception as e:
            logger.error(f"Internal GET error on {endpoint}: {e}")
        finally:
            # Crucial: Close connection AFTER query in internal/async mode
            close_old_connections()
        return {}

    def _handle_internal_post(self, endpoint: str, data: dict) -> dict:
        """Internal Django logic for POST"""
        from django.db import close_old_connections
        from api.models import TelegramUser, Poll, Candidate, Vote
        
        try:
            # Clean up before query
            close_old_connections()
            
            clean_ep = endpoint.strip('/')
            
            if clean_ep == 'users/register':
                user, created = TelegramUser.objects.update_or_create(
                    telegram_id=data['telegram_id'],
                    defaults={'username': data['username'], 'full_name': data['full_name']}
                )
                return {'status': 'success', 'telegram_id': user.telegram_id}
            
            if clean_ep.startswith('users/') and clean_ep.endswith('/mark_subscribed'):
                tid = clean_ep.split('/')[1]
                TelegramUser.objects.filter(telegram_id=tid).update(is_subscribed=True)
                return {'status': 'success'}
            
            if clean_ep == 'check-subscription':
                tid = data['telegram_id']
                poll_id = data.get('poll_id')
                try:
                    user = TelegramUser.objects.get(telegram_id=tid)
                    res = {'is_subscribed': user.is_subscribed}
                    if poll_id:
                        res['has_voted_in_poll'] = user.has_voted_in_poll(poll_id)
                    return res
                except TelegramUser.DoesNotExist:
                    return {'is_subscribed': False}
            
            if clean_ep == 'votes':
                user = TelegramUser.objects.get(telegram_id=data['telegram_id'])
                poll = Poll.objects.get(id=data['poll_id'])
                candidate = Candidate.objects.get(id=data['candidate_id'])
                
                # Check if poll is open
                if not poll.is_open():
                    return {'status': 'error', 'message': 'So\'rovnoma yopiq!'}
                
                # Check if already voted
                if user.has_voted_in_poll(poll.id):
                    return {'status': 'error', 'message': 'Siz bu so\'rovnomada allaqachon ovoz bergansiz!'}
                
                Vote.objects.create(user=user, poll=poll, candidate=candidate)
                return {'status': 'success'}

        except Exception as e:
            logger.error(f"Internal POST error on {endpoint}: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            # Crucial: Close connection AFTER query
            close_old_connections()
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
    
    def get_candidate_detail(self, candidate_id: int) -> dict:
        """Nomzodning batafsil ma'lumotlarini olish"""
        # Ensure correct endpoint format for internal matcher
        endpoint = f"{candidate_id}/" if self.is_internal else f"candidates/{candidate_id}/"
        return self._get(endpoint, {})
    
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
    
    def download_photo(self, photo_url: str) -> bytes:
        """Rasmni download qilish"""
        try:
            if not photo_url:
                return None
            
            # If INTERNAL mode and it's a local file, read it directly
            if self.is_internal and (photo_url.startswith('/media/') or not photo_url.startswith('http')):
                from django.conf import settings
                import os
                
                # Strip leading / if present to avoid absolute path issues with os.path.join
                rel_path = photo_url.replace('/media/', '') if photo_url.startswith('/media/') else photo_url
                full_path = os.path.join(settings.MEDIA_ROOT, rel_path)
                
                if os.path.exists(full_path):
                    with open(full_path, 'rb') as f:
                        return f.read()
            
            # Fallback to HTTP
            if photo_url.startswith('/media/'):
                photo_url = f"{self.base_url.replace('/api', '')}{photo_url}"
            elif not photo_url.startswith('http'):
                photo_url = f"{self.base_url.replace('/api', '')}/media/{photo_url}"
            
            logger.debug(f"Downloading photo from: {photo_url}")
            response = requests.get(photo_url, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Photo download error: {e}")
            return None
