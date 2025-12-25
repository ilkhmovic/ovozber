from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import TelegramUser, Channel, Poll, Region, District, Candidate, Vote
from django.urls import path
from django.http import JsonResponse


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'username', 'telegram_id', 'is_subscribed', 'get_voted_polls_count', 'created_at']
    list_filter = ['is_subscribed', 'created_at']
    search_fields = ['full_name', 'username', 'telegram_id']
    readonly_fields = ['telegram_id', 'created_at', 'updated_at', 'get_voted_polls_list']
    list_per_page = 50

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('telegram_id', 'username', 'full_name', 'phone_number')
        }),
        ('Holat', {
            'fields': ('is_subscribed', 'get_voted_polls_list')
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_voted_polls_count(self, obj):
        return obj.votes.values('poll').distinct().count()
    get_voted_polls_count.short_description = 'Ovoz bergan polllar'
    
    def get_voted_polls_list(self, obj):
        polls = obj.get_voted_polls()
        if polls:
            return format_html_join(
                mark_safe('<br>'),
                '• {}',
                ((poll.title,) for poll in polls)
            )
        return 'Hali ovoz bermagan'
    get_voted_polls_list.short_description = 'Ovoz bergan so\'rovnomalar'


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['title', 'channel_username', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'channel_username', 'channel_id']
    list_editable = ['is_active']


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'get_status', 'get_total_votes', 'get_participants', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['order', 'is_active']
    readonly_fields = ['get_total_votes', 'get_participants', 'created_at', 'get_candidates_stats']
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('title', 'description', 'order')
        }),
        ('Vaqt sozlamalari', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Statistika', {
            'fields': ('get_total_votes', 'get_participants', 'get_candidates_stats', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_status(self, obj):
        if obj.is_open():
            return format_html('<span style="color: green;">{}</span>', '✓ Ochiq')
        return format_html('<span style="color: red;">{}</span>', '✗ Yopiq')
    get_status.short_description = 'Holat'
    
    def get_total_votes(self, obj):
        return obj.total_votes
    get_total_votes.short_description = 'Jami ovozlar'
    
    def get_participants(self, obj):
        return obj.total_participants
    get_participants.short_description = 'Ishtirokchilar'
    
    def get_candidates_stats(self, obj):
        """Nomzodlarning ovoz statistikasini ko'rsatish"""
        candidates = obj.candidates.annotate(
            votes_count=Count('votes')
        ).order_by('-votes_count').values('id', 'full_name', 'votes_count')
        
        if not candidates.exists():
            return 'Nomzodlar mavjud emas'
        
        stats_html = '<table style="width:100%; border-collapse: collapse;"><tr style="background-color: #f0f0f0;"><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Nomzod</th><th style="border: 1px solid #ddd; padding: 8px; text-align: center;">Ovozlar</th><th style="border: 1px solid #ddd; padding: 8px; text-align: center;">Foiz (%)</th></tr>'
        
        total = obj.total_votes if obj.total_votes > 0 else 1
        
        for candidate in candidates:
            votes_count = candidate['votes_count']
            percentage = (votes_count / total * 100) if total > 0 else 0
            # Color code based on percentage
            if percentage > 50:
                color = '#28a745'  # Green
            elif percentage > 25:
                color = '#ffc107'  # Yellow
            else:
                color = '#dc3545'  # Red
            
            stats_html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;">{candidate["full_name"]}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: {color}; font-weight: bold;">{votes_count}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{percentage:.1f}%</td></tr>'
        
        stats_html += '</table>'
        return mark_safe(stats_html)
    
    get_candidates_stats.short_description = 'Nomzodlar bo\'yicha ovozlar'


class RegionInline(admin.TabularInline):
    model = Region
    extra = 1
    fields = ['name', 'order', 'is_active']


class DistrictInline(admin.TabularInline):
    model = District
    extra = 1
    fields = ['name', 'order', 'is_active']


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'poll', 'order', 'is_active', 'get_districts_count', 'get_total_votes']
    list_filter = ['poll', 'is_active']
    search_fields = ['name', 'poll__title']
    list_editable = ['order', 'is_active']
    inlines = [DistrictInline]

    def get_districts_count(self, obj):
        return obj.districts.count()
    get_districts_count.short_description = 'Tumanlar soni'

    def get_total_votes(self, obj):
        return obj.total_votes
    get_total_votes.short_description = 'Jami ovozlar'


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1
    fields = ['full_name', 'position', 'order', 'is_active']


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'get_poll', 'order', 'is_active', 'get_candidates_count', 'get_total_votes']
    list_filter = ['region__poll', 'region', 'is_active']
    search_fields = ['name', 'region__name', 'region__poll__title']
    list_editable = ['order', 'is_active']
    inlines = [CandidateInline]
    
    def get_poll(self, obj):
        return obj.region.poll.title
    get_poll.short_description = 'So\'rovnoma'

    def get_candidates_count(self, obj):
        return obj.candidates.count()
    get_candidates_count.short_description = 'Nomzodlar soni'

    def get_total_votes(self, obj):
        return obj.total_votes
    get_total_votes.short_description = 'Jami ovozlar'


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'district', 'get_poll', 'position', 'order', 'is_active', 'get_vote_count_display', 'get_rank', 'get_photo_preview']
    list_filter = ['poll', 'district__region', 'district', 'is_active']
    search_fields = ['full_name', 'position', 'district__name', 'poll__title']
    list_editable = ['order', 'is_active']
    readonly_fields = ['get_photo_preview', 'get_vote_count_display']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('poll', 'district', 'full_name', 'position', 'bio')
        }),
        ('Rasm', {
            'fields': ('photo', 'get_photo_preview')
        }),
        ('Sozlamalar', {
            'fields': ('order', 'is_active')
        }),
        ('Statistika', {
            'fields': ('get_vote_count_display',),
            'classes': ('collapse',)
        }),
    )
    
    def get_poll(self, obj):
        return obj.poll.title if obj.poll else (obj.district.region.poll.title if obj.district else None)
    get_poll.short_description = 'So\'rovnoma'
    
    def get_vote_count_display(self, obj):
        """Ovozlar sonini rang bilan ko'rsatish"""
        vote_count = obj.votes.count()
        if vote_count == 0:
            color = '#999'
        elif vote_count < 5:
            color = '#dc3545'  # Red
        elif vote_count < 20:
            color = '#ffc107'  # Yellow
        else:
            color = '#28a745'  # Green
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, vote_count)
    get_vote_count_display.short_description = 'Ovozlar'
    
    def get_rank(self, obj):
        """Nomzodning so'rovnomada ranki"""
        if not obj.poll:
            return '-'
        
        # Use values() to avoid property conflicts when iterating
        candidates_with_votes = list(obj.poll.candidates.annotate(
            votes_count=Count('votes')
        ).order_by('-votes_count').values('id', 'votes_count'))
        
        rank = 1
        for candidate_data in candidates_with_votes:
            if candidate_data['id'] == obj.id:
                if rank == 1:
                    return format_html('<span style="color: gold; font-weight: bold;">🥇 {}</span>', rank)
                elif rank == 2:
                    return format_html('<span style="color: silver; font-weight: bold;">🥈 {}</span>', rank)
                elif rank == 3:
                    return format_html('<span style="color: #CD7F32; font-weight: bold;">🥉 {}</span>', rank)
                else:
                    return format_html('<span>{}</span>', rank)
            rank += 1
        return '-'
    get_rank.short_description = 'Rang'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('districts-by-poll/', self.admin_site.admin_view(self.districts_by_poll), name='api_candidate_districts_by_poll'),
        ]
        return custom_urls + urls

    def districts_by_poll(self, request):
        poll_id = request.GET.get('poll_id')
        if not poll_id:
            return JsonResponse({'error': 'poll_id is required'}, status=400)

        qs = District.objects.filter(region__poll_id=poll_id, is_active=True).select_related('region').order_by('name')
        data = [{'id': d.id, 'name': f"{d.name} ({d.region.name})"} for d in qs]
        return JsonResponse(data, safe=False)

    class Media:
        js = ('admin/js/candidate_admin.js',)

    def get_photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover; border-radius: 8px;" />', obj.photo.url)
        return "Rasm yo'q"
    get_photo_preview.short_description = 'Rasm ko\'rinishi'

    def get_vote_count(self, obj):
        count = obj.vote_count
        return format_html('<strong style="color: green; font-size: 16px;">{}</strong>', count)
    get_vote_count.short_description = 'Ovozlar soni'


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'poll', 'candidate', 'get_district', 'get_region', 'voted_at']
    list_filter = ['poll', 'voted_at', 'candidate__district__region', 'candidate__district']
    search_fields = ['user__full_name', 'user__username', 'candidate__full_name', 'poll__title']
    readonly_fields = ['poll', 'user', 'candidate', 'voted_at', 'ip_address']
    date_hierarchy = 'voted_at'

    def get_district(self, obj):
        return obj.candidate.district.name if obj.candidate.district else None
    get_district.short_description = 'Tuman'

    def get_region(self, obj):
        return obj.candidate.district.region.name if obj.candidate.district else None
    get_region.short_description = 'Viloyat'

    def has_add_permission(self, request):
        """Admin paneldan ovoz qo'shishni cheklash"""
        return False

    def has_change_permission(self, request, obj=None):
        """Ovozlarni o'zgartirishni cheklash"""
        return False


# Admin panel sarlavhasini o'zgartirish
admin.site.site_header = "Ovoz Berish Tizimi"
admin.site.site_title = "Ovoz Berish Admin"
admin.site.index_title = "Boshqaruv Paneli"
