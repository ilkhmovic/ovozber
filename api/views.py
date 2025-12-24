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
            district__region__poll=poll, is_active=True
        ).annotate(
            vote_count=Count('votes')
        ).select_related('district__region').order_by('-vote_count')[:10]
        
        top_candidates_data = [{
            'id': c.id,
            'name': c.full_name,
            'district': c.district.name,
            'region': c.district.region.name,
            'votes': c.vote_count
        } for c in top_candidates]
        
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
    queryset = Candidate.objects.filter(is_active=True).select_related('district__region')
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
    
    top_candidates_data = [{
        'id': c.id,
        'name': c.full_name,
        'district': c.district.name,
        'region': c.district.region.name,
        'votes': c.vote_count
    } for c in top_candidates]
    
    return Response({
        'total_users': total_users,
        'total_votes': total_votes,
        'subscribed_users': subscribed_users,
        'voted_users': voted_users,
        'regions': list(regions_stats),
        'top_candidates': top_candidates_data
    })


@api_view(['POST'])
def check_subscription(request):
    """Foydalanuvchining obuna holatini tekshirish"""
    telegram_id = request.data.get('telegram_id')
    poll_id = request.data.get('poll_id')
    
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
