from rest_framework import serializers
from .models import TelegramUser, Channel, Poll, Region, District, Candidate, Vote


class TelegramUserSerializer(serializers.ModelSerializer):
    voted_polls_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TelegramUser
        fields = ['id', 'telegram_id', 'username', 'full_name', 'phone_number', 
                  'is_subscribed', 'voted_polls_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_voted_polls_count(self, obj):
        return obj.votes.values('poll').distinct().count()


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'channel_id', 'channel_username', 'title', 'description', 'is_active']
        read_only_fields = ['id']


class PollSerializer(serializers.ModelSerializer):
    total_votes = serializers.IntegerField(read_only=True)
    total_participants = serializers.IntegerField(read_only=True)
    is_open = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Poll
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 
                  'is_active', 'is_open', 'total_votes', 'total_participants', 'order']
        read_only_fields = ['id', 'total_votes', 'total_participants']


class CandidateSerializer(serializers.ModelSerializer):
    vote_count = serializers.IntegerField(read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    
    class Meta:
        model = Candidate
        fields = ['id', 'full_name', 'photo', 'bio', 'position', 'vote_count', 
                  'district_name', 'order']
        read_only_fields = ['id', 'vote_count']


class DistrictSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)
    total_votes = serializers.IntegerField(read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)
    
    class Meta:
        model = District
        fields = ['id', 'name', 'description', 'candidates', 'total_votes', 
                  'region_name', 'order']
        read_only_fields = ['id', 'total_votes']


class RegionSerializer(serializers.ModelSerializer):
    districts = DistrictSerializer(many=True, read_only=True)
    total_votes = serializers.IntegerField(read_only=True)
    poll_id = serializers.IntegerField(source='poll.id', read_only=True)
    poll_title = serializers.CharField(source='poll.title', read_only=True)
    
    class Meta:
        model = Region
        fields = ['id', 'name', 'description', 'districts', 'total_votes', 
                  'poll_id', 'poll_title', 'order']
        read_only_fields = ['id', 'total_votes']


class VoteSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    poll_title = serializers.CharField(source='poll.title', read_only=True)
    
    class Meta:
        model = Vote
        fields = ['id', 'poll', 'user', 'candidate', 'user_name', 'candidate_name', 
                  'poll_title', 'voted_at', 'ip_address']
        read_only_fields = ['id', 'poll', 'voted_at']


class VoteCreateSerializer(serializers.Serializer):
    """Ovoz berish uchun soddalashtirilgan serializer"""
    telegram_id = serializers.IntegerField()
    poll_id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    
    def validate(self, data):
        # Foydalanuvchini tekshirish
        try:
            user = TelegramUser.objects.get(telegram_id=data['telegram_id'])
        except TelegramUser.DoesNotExist:
            raise serializers.ValidationError("Foydalanuvchi topilmadi!")
        
        # Pollni tekshirish
        try:
            poll = Poll.objects.get(id=data['poll_id'], is_active=True)
        except Poll.DoesNotExist:
            raise serializers.ValidationError("So'rovnoma topilmadi!")
        
        if not poll.is_open():
            raise serializers.ValidationError("So'rovnoma yopiq!")
        
        # Foydalanuvchi bu pollda ovoz berganmi?
        if user.has_voted_in_poll(poll.id):
            raise serializers.ValidationError("Siz bu so'rovnomada allaqachon ovoz bergansiz!")
        
        # Nomzodni tekshirish
        try:
            candidate = Candidate.objects.get(
                id=data['candidate_id'], 
                is_active=True,
                district__region__poll=poll
            )
        except Candidate.DoesNotExist:
            raise serializers.ValidationError("Nomzod topilmadi yoki bu so'rovnomaga tegishli emas!")
        
        data['user'] = user
        data['poll'] = poll
        data['candidate'] = candidate
        return data
    
    def create(self, validated_data):
        user = validated_data['user']
        poll = validated_data['poll']
        candidate = validated_data['candidate']
        
        vote = Vote.objects.create(
            user=user,
            poll=poll,
            candidate=candidate
        )
        return vote
