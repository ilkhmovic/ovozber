from rest_framework import serializers
from .models import TelegramUser, Channel, Region, District, Candidate, Vote


class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = ['id', 'telegram_id', 'username', 'full_name', 'phone_number', 
                  'is_subscribed', 'has_voted', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'channel_id', 'channel_username', 'title', 'description', 'is_active']
        read_only_fields = ['id']


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
    
    class Meta:
        model = Region
        fields = ['id', 'name', 'description', 'districts', 'total_votes', 'order']
        read_only_fields = ['id', 'total_votes']


class VoteSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    
    class Meta:
        model = Vote
        fields = ['id', 'user', 'candidate', 'user_name', 'candidate_name', 
                  'voted_at', 'ip_address']
        read_only_fields = ['id', 'voted_at']

    def validate(self, data):
        """Bir foydalanuvchi faqat bir marta ovoz berishi mumkin"""
        user = data.get('user')
        if user and user.has_voted:
            raise serializers.ValidationError("Siz allaqachon ovoz bergansiz!")
        return data

    def create(self, validated_data):
        """Ovoz yaratish"""
        vote = Vote.objects.create(**validated_data)
        return vote


class VoteCreateSerializer(serializers.Serializer):
    """Ovoz berish uchun soddalashtirilgan serializer"""
    telegram_id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    
    def validate(self, data):
        # Foydalanuvchini tekshirish
        try:
            user = TelegramUser.objects.get(telegram_id=data['telegram_id'])
        except TelegramUser.DoesNotExist:
            raise serializers.ValidationError("Foydalanuvchi topilmadi!")
        
        if user.has_voted:
            raise serializers.ValidationError("Siz allaqachon ovoz bergansiz!")
        
        # Nomzodni tekshirish
        try:
            candidate = Candidate.objects.get(id=data['candidate_id'], is_active=True)
        except Candidate.DoesNotExist:
            raise serializers.ValidationError("Nomzod topilmadi!")
        
        data['user'] = user
        data['candidate'] = candidate
        return data
    
    def create(self, validated_data):
        user = validated_data['user']
        candidate = validated_data['candidate']
        
        vote = Vote.objects.create(
            user=user,
            candidate=candidate
        )
        return vote
