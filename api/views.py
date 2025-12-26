from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import TelegramUser, Channel, Poll, Region, District, Candidate, Vote
from .serializers import (
    TelegramUserSerializer, ChannelSerializer, PollSerializer, RegionSerializer,
    DistrictSerializer, CandidateSerializer, VoteSerializer, VoteCreateSerializer
)


class TelegramUserViewSet(viewsets.ModelViewSet):
    """Telegram foydalanuvchilar API"""
    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer
    lookup_field = 'telegram_id'

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Foydalanuvchini ro'yxatdan o'tkazish yoki yangilash"""
        telegram_id = request.data.get('telegram_id')
        
        if not telegram_id:
            return Response(
                {'error': 'telegram_id talab qilinadi'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user, created = TelegramUser.objects.update_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': request.data.get('username', ''),
                'full_name': request.data.get('full_name', ''),
                'phone_number': request.data.get('phone_number', ''),
            }
        )
        
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def mark_subscribed(self, request, telegram_id=None):
        """Foydalanuvchini obuna bo'lgan deb belgilash"""
        try:
            user = self.get_object()
            user.is_subscribed = True
            user.save()
            return Response({'status': 'success', 'message': 'Obuna tasdiqlandi'})
        except TelegramUser.DoesNotExist:
            return Response(
                {'error': 'Foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def voted_polls(self, request, telegram_id=None):
        """Foydalanuvchi ovoz bergan polllar"""
        try:
            user = self.get_object()
            polls = user.get_voted_polls()
            serializer = PollSerializer(polls, many=True)
            return Response(serializer.data)
        except TelegramUser.DoesNotExist:
            return Response(
                {'error': 'Foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )


class ChannelViewSet(viewsets.ReadOnlyModelViewSet):
    """Kanallar API (faqat o'qish)"""
    queryset = Channel.objects.filter(is_active=True)
    serializer_class = ChannelSerializer


class PollViewSet(viewsets.ReadOnlyModelViewSet):
    """So'rovnomalar API (faqat o'qish)"""
    queryset = Poll.objects.filter(is_active=True)
    serializer_class = PollSerializer
    
    @action(detail=True, methods=['get'])
    def regions(self, request, pk=None):
        """Poll uchun viloyatlar"""
        poll = self.get_object()
        regions = Region.objects.filter(poll=poll, is_active=True).prefetch_related('districts__candidates')
        serializer = RegionSerializer(regions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Poll statistikasi"""
        poll = self.get_object()
        
        total_votes = poll.total_votes
        total_participants = poll.total_participants
        
        # Viloyatlar bo'yicha
        regions_stats = Region.objects.filter(poll=poll, is_active=True).annotate(
            vote_count=Count('districts__candidates__votes')
        ).values('id', 'name', 'vote_count').order_by('-vote_count')
        
        # Top nomzodlar
        top_candidates = Candidate.objects.filter(
            poll=poll, is_active=True
        ).annotate(
            vote_count=Count('votes')
        ).select_related('district__region').order_by('-vote_count')[:10]
        
        top_candidates_data = []
        for c in top_candidates:
            district = c.district.name if c.district else None
            region = c.district.region.name if c.district else None
            top_candidates_data.append({
                'id': c.id,
                'name': c.full_name,
                'district': district,
                'region': region,
                'votes': c.vote_count
            })
        
        return Response({
            'poll': PollSerializer(poll).data,
            'total_votes': total_votes,
            'total_participants': total_participants,
            'regions': list(regions_stats),
            'top_candidates': top_candidates_data
        })


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    """Viloyatlar API (faqat o'qish)"""
    queryset = Region.objects.filter(is_active=True).prefetch_related(
        'districts__candidates'
    )
    serializer_class = RegionSerializer


class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    """Tumanlar API (faqat o'qish)"""
    queryset = District.objects.filter(is_active=True).prefetch_related('candidates')
    serializer_class = DistrictSerializer

    @action(detail=False, methods=['get'])
    def by_region(self, request):
        """Viloyat bo'yicha tumanlarni olish"""
        region_id = request.query_params.get('region_id')
        if not region_id:
            return Response(
                {'error': 'region_id parametri talab qilinadi'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        districts = self.queryset.filter(region_id=region_id)
        serializer = self.get_serializer(districts, many=True)
        return Response(serializer.data)


class CandidateViewSet(viewsets.ReadOnlyModelViewSet):
    """Nomzodlar API (faqat o'qish)"""
    queryset = Candidate.objects.filter(is_active=True).select_related('poll', 'district__region')
    serializer_class = CandidateSerializer

    @action(detail=False, methods=['get'])
    def by_district(self, request):
        """Tuman bo'yicha nomzodlarni olish"""
        district_id = request.query_params.get('district_id')
        if not district_id:
            return Response(
                {'error': 'district_id parametri talab qilinadi'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        candidates = self.queryset.filter(district_id=district_id)
        serializer = self.get_serializer(candidates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_poll(self, request):
        """So'rovnoma bo'yicha nomzodlarni olish"""
        poll_id = request.query_params.get('poll_id')
        if not poll_id:
            return Response(
                {'error': 'poll_id parametri talab qilinadi'},
                status=status.HTTP_400_BAD_REQUEST
            )

        candidates = self.queryset.filter(poll_id=poll_id)
        serializer = self.get_serializer(candidates, many=True)
        return Response(serializer.data)


class VoteViewSet(viewsets.ModelViewSet):
    """Ovozlar API"""
    queryset = Vote.objects.all().select_related('user', 'candidate')
    serializer_class = VoteSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return VoteCreateSerializer
        return VoteSerializer

    def create(self, request, *args, **kwargs):
        """Ovoz berish"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vote = serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Ovozingiz qabul qilindi!',
            'vote': VoteSerializer(vote).data
        }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def statistics(request):
    """Umumiy statistika"""
    total_users = TelegramUser.objects.count()


# Webhook for Telegram (used when deploying via webhook instead of polling)
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import json
import asyncio
import telegram
from bot.bot import create_application
from bot.config import BOT_TOKEN as BOT_TOKEN_CONFIG

import logging
logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
def telegram_webhook(request, token=None):
    """Receive Telegram updates via webhook and forward to application."""
    # Basic token check for security
    if token != BOT_TOKEN_CONFIG:
        logger.warning(f"Invalid webhook token received: {token}")
        return HttpResponse(status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        logger.error(f"Invalid JSON payload: {e}")
        return HttpResponse(status=400)

    async def process_update_async(app, update):
        try:
            await app.initialize()
            await app.process_update(update)
            # Explicitly save persistence state after processing
            if app.persistence:
                await app.update_persistence()
            await app.shutdown()
        except Exception as e:
            logger.error(f"Async processing error: {e}", exc_info=True)

    try:
        # Create a fresh application instance for this request
        # This is required because we are using asyncio.run() which creates a new event loop
        # Reusing a global application would cause it to be bound to a closed loop from a previous request.
        app = create_application()
        
        # Manually decode update using the bot instance from the new app
        update = telegram.Update.de_json(payload, app.bot)
        
        # Process asynchronously
        asyncio.run(process_update_async(app, update))
            
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}", exc_info=True)
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

    return JsonResponse({'ok': True})
    total_votes = Vote.objects.count()
    subscribed_users = TelegramUser.objects.filter(is_subscribed=True).count()
    voted_users = TelegramUser.objects.filter(has_voted=True).count()
    
    # Viloyatlar bo'yicha statistika
    regions_stats = Region.objects.filter(is_active=True).annotate(
        vote_count=Count('districts__candidates__votes')
    ).values('id', 'name', 'vote_count').order_by('-vote_count')
    
    # Top nomzodlar
    top_candidates = Candidate.objects.filter(is_active=True).annotate(
        vote_count=Count('votes')
    ).select_related('district__region').order_by('-vote_count')[:10]
    
    top_candidates_data = []
    for c in top_candidates:
        district = c.district.name if c.district else None
        region = c.district.region.name if c.district else None
        top_candidates_data.append({
            'id': c.id,
            'name': c.full_name,
            'district': district,
            'region': region,
            'votes': c.vote_count
        })
    
    return Response({
        'total_users': total_users,
        'total_votes': total_votes,
        'subscribed_users': subscribed_users,
        'voted_users': voted_users,
        'regions': list(regions_stats),
        'top_candidates': top_candidates_data
    })


@api_view(['POST', 'GET'])
def check_subscription(request):
    """Foydalanuvchining obuna holatini tekshirish"""
    if request.method == 'POST':
        telegram_id = request.data.get('telegram_id')
        poll_id = request.data.get('poll_id')
    else:
        telegram_id = request.query_params.get('telegram_id')
        poll_id = request.query_params.get('poll_id')
    
    if not telegram_id:
        return Response(
            {'error': 'telegram_id talab qilinadi'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        response_data = {
            'is_subscribed': user.is_subscribed,
        }
        
        if poll_id:
            response_data['has_voted_in_poll'] = user.has_voted_in_poll(poll_id)
        
        return Response(response_data)
    except TelegramUser.DoesNotExist:
        return Response({
            'is_subscribed': False,
            'has_voted_in_poll': False
        })


@api_view(['GET'])
def poll_statistics(request):
    """So'rovnoma bo'yicha nomzodlarning ovoz statistikasi"""
    poll_id = request.query_params.get('poll_id')
    
    if not poll_id:
        return Response(
            {'error': 'poll_id parametri talab qilinadi'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        poll = Poll.objects.get(id=poll_id)
        candidates_stats = poll.candidates.annotate(
            votes_count=Count('votes')
        ).order_by('-votes_count').values(
            'id', 'full_name', 'position', 'votes_count'
        )
        
        total_votes = poll.total_votes
        
        stats_data = {
            'poll_id': poll.id,
            'poll_title': poll.title,
            'total_votes': total_votes,
            'total_participants': poll.total_participants,
            'candidates': []
        }
        
        rank = 1
        for candidate in candidates_stats:
            percentage = (candidate['votes_count'] / total_votes * 100) if total_votes > 0 else 0
            stats_data['candidates'].append({
                'rank': rank,
                'candidate_id': candidate['id'],
                'full_name': candidate['full_name'],
                'position': candidate['position'],
                'votes': candidate['votes_count'],
                'percentage': round(percentage, 1)
            })
            rank += 1
        
        return Response(stats_data)
    except Poll.DoesNotExist:
        return Response(
            {'error': 'So\'rovnoma topilmadi'},
            status=status.HTTP_404_NOT_FOUND
        )
