from django.contrib import admin
from django.utils.html import format_html
from .models import TelegramUser, Channel, Region, District, Candidate, Vote


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'username', 'telegram_id', 'is_subscribed', 'has_voted', 'created_at']
    list_filter = ['is_subscribed', 'has_voted', 'created_at']
    search_fields = ['full_name', 'username', 'telegram_id']
    readonly_fields = ['telegram_id', 'created_at', 'updated_at']
    list_per_page = 50

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('telegram_id', 'username', 'full_name', 'phone_number')
        }),
        ('Holat', {
            'fields': ('is_subscribed', 'has_voted')
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['title', 'channel_username', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'channel_username', 'channel_id']
    list_editable = ['is_active']


class DistrictInline(admin.TabularInline):
    model = District
    extra = 1
    fields = ['name', 'order', 'is_active']


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active', 'get_districts_count', 'get_total_votes']
    list_filter = ['is_active']
    search_fields = ['name']
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
    list_display = ['name', 'region', 'order', 'is_active', 'get_candidates_count', 'get_total_votes']
    list_filter = ['region', 'is_active']
    search_fields = ['name', 'region__name']
    list_editable = ['order', 'is_active']
    inlines = [CandidateInline]

    def get_candidates_count(self, obj):
        return obj.candidates.count()
    get_candidates_count.short_description = 'Nomzodlar soni'

    def get_total_votes(self, obj):
        return obj.total_votes
    get_total_votes.short_description = 'Jami ovozlar'


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'district', 'position', 'order', 'is_active', 'get_vote_count', 'get_photo_preview']
    list_filter = ['district__region', 'district', 'is_active']
    search_fields = ['full_name', 'position', 'district__name']
    list_editable = ['order', 'is_active']
    readonly_fields = ['get_photo_preview', 'get_vote_count']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('district', 'full_name', 'position', 'bio')
        }),
        ('Rasm', {
            'fields': ('photo', 'get_photo_preview')
        }),
        ('Sozlamalar', {
            'fields': ('order', 'is_active')
        }),
        ('Statistika', {
            'fields': ('get_vote_count',),
            'classes': ('collapse',)
        }),
    )

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
    list_display = ['user', 'candidate', 'get_district', 'get_region', 'voted_at']
    list_filter = ['voted_at', 'candidate__district__region', 'candidate__district']
    search_fields = ['user__full_name', 'user__username', 'candidate__full_name']
    readonly_fields = ['user', 'candidate', 'voted_at', 'ip_address']
    date_hierarchy = 'voted_at'

    def get_district(self, obj):
        return obj.candidate.district.name
    get_district.short_description = 'Tuman'

    def get_region(self, obj):
        return obj.candidate.district.region.name
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
