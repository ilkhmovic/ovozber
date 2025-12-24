from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TelegramUserViewSet, ChannelViewSet, RegionViewSet,
    DistrictViewSet, CandidateViewSet, VoteViewSet,
    statistics, check_subscription
)

router = DefaultRouter()
router.register(r'users', TelegramUserViewSet, basename='user')
router.register(r'channels', ChannelViewSet, basename='channel')
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'districts', DistrictViewSet, basename='district')
router.register(r'candidates', CandidateViewSet, basename='candidate')
router.register(r'votes', VoteViewSet, basename='vote')

urlpatterns = [
    path('', include(router.urls)),
    path('statistics/', statistics, name='statistics'),
    path('check-subscription/', check_subscription, name='check-subscription'),
]
