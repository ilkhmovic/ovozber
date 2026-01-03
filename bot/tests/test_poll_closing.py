import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ovozber.settings')
django.setup()

from api.models import Poll, Candidate, TelegramUser, Region, District
from bot.api_client import APIClient

def test_poll_closing():
    print("--- Testing Poll Closing Logic ---")
    
    # 1. Create a test poll that is closed
    now = timezone.now()
    poll = Poll.objects.create(
        title="Test Closed Poll",
        start_date=now - timedelta(days=2),
        end_date=now - timedelta(days=1),
        is_active=True
    )
    
    region = Region.objects.create(poll=poll, name="Test Region")
    district = District.objects.create(region=region, name="Test District")
    candidate = Candidate.objects.create(poll=poll, district=district, full_name="Test Candidate")
    
    # 2. Create a test user
    user, _ = TelegramUser.objects.get_or_create(
        telegram_id=999999,
        defaults={'full_name': 'Test User'}
    )
    
    # 3. Try to vote via APIClient (Internal Mode)
    client = APIClient(base_url='INTERNAL')
    
    print(f"Attempting to vote in closed poll (ID: {poll.id})...")
    result = client.submit_vote(user.telegram_id, poll.id, candidate.id)
    
    if result.get('status') == 'error' and 'yopiq' in result.get('message', ''):
        print("✅ Success: APIClient correctly rejected vote for closed poll.")
    else:
        print(f"❌ Failure: APIClient accepted vote or returned unexpected error: {result}")
        
    # 4. Clean up
    poll.delete()
    print("Test finished.")

if __name__ == "__main__":
    test_poll_closing()
