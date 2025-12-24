from django.db import models
from django.utils import timezone


class TelegramUser(models.Model):
    """Telegram foydalanuvchilari"""
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name="Username")
    full_name = models.CharField(max_length=255, verbose_name="To'liq ism")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon raqam")
    is_subscribed = models.BooleanField(default=False, verbose_name="Obuna bo'lganmi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ro'yxatdan o'tgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    class Meta:
        verbose_name = "Telegram foydalanuvchi"
        verbose_name_plural = "Telegram foydalanuvchilar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} (@{self.username})" if self.username else self.full_name
    
    def has_voted_in_poll(self, poll_id):
        """Foydalanuvchi bu pollda ovoz berganmi?"""
        return self.votes.filter(poll_id=poll_id).exists()
    
    def get_voted_polls(self):
        """Foydalanuvchi ovoz bergan polllar"""
        return Poll.objects.filter(votes__user=self).distinct()


class Channel(models.Model):
    """Majburiy obuna kanallari"""
    channel_id = models.CharField(max_length=255, unique=True, verbose_name="Kanal ID")
    channel_username = models.CharField(max_length=255, verbose_name="Kanal username (@siz)")
    title = models.CharField(max_length=255, verbose_name="Kanal nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Tavsif")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan vaqt")

    class Meta:
        verbose_name = "Kanal"
        verbose_name_plural = "Kanallar"
        ordering = ['title']

    def __str__(self):
        return f"{self.title} (@{self.channel_username})"


class Poll(models.Model):
    """So'rovnomalar"""
    title = models.CharField(max_length=255, verbose_name="So'rovnoma nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Tavsif")
    start_date = models.DateTimeField(blank=True, null=True, verbose_name="Boshlanish sanasi")
    end_date = models.DateTimeField(blank=True, null=True, verbose_name="Tugash sanasi")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    order = models.IntegerField(default=0, verbose_name="Tartib raqami")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    class Meta:
        verbose_name = "So'rovnoma"
        verbose_name_plural = "So'rovnomalar"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title
    
    @property
    def total_votes(self):
        """Polldagi jami ovozlar"""
        return self.votes.count()
    
    @property
    def total_participants(self):
        """Pollda ishtirok etgan foydalanuvchilar soni"""
        return self.votes.values('user').distinct().count()
    
    def is_open(self):
        """Poll ochiqmi?"""
        if not self.is_active:
            return False
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True


class Region(models.Model):
    """Viloyatlar"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='regions', verbose_name="So'rovnoma")
    name = models.CharField(max_length=255, verbose_name="Viloyat nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Tavsif")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    order = models.IntegerField(default=0, verbose_name="Tartib raqami")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    class Meta:
        verbose_name = "Viloyat"
        verbose_name_plural = "Viloyatlar"
        ordering = ['order', 'name']
        unique_together = ['poll', 'name']

    def __str__(self):
        return f"{self.name} ({self.poll.title})"

    @property
    def total_votes(self):
        """Viloyatdagi jami ovozlar"""
        return Vote.objects.filter(candidate__district__region=self).count()


class District(models.Model):
    """Tumanlar"""
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='districts', verbose_name="Viloyat")
    name = models.CharField(max_length=255, verbose_name="Tuman nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Tavsif")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    order = models.IntegerField(default=0, verbose_name="Tartib raqami")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    class Meta:
        verbose_name = "Tuman"
        verbose_name_plural = "Tumanlar"
        ordering = ['order', 'name']
        unique_together = ['region', 'name']

    def __str__(self):
        return f"{self.name} ({self.region.name})"

    @property
    def total_votes(self):
        """Tumandagi jami ovozlar"""
        return Vote.objects.filter(candidate__district=self).count()


class Candidate(models.Model):
    """Nomzodlar"""
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='candidates', verbose_name="Tuman")
    full_name = models.CharField(max_length=255, verbose_name="To'liq ism")
    photo = models.ImageField(upload_to='candidates/', blank=True, null=True, verbose_name="Rasm")
    bio = models.TextField(blank=True, null=True, verbose_name="Biografiya")
    position = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lavozim")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    order = models.IntegerField(default=0, verbose_name="Tartib raqami")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan vaqt")

    class Meta:
        verbose_name = "Nomzod"
        verbose_name_plural = "Nomzodlar"
        ordering = ['order', 'full_name']

    def __str__(self):
        return f"{self.full_name} - {self.district.name}"

    @property
    def vote_count(self):
        """Nomzod uchun berilgan ovozlar soni"""
        return self.votes.count()


class Vote(models.Model):
    """Ovozlar"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes', verbose_name="So'rovnoma")
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='votes', verbose_name="Foydalanuvchi")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes', verbose_name="Nomzod")
    voted_at = models.DateTimeField(default=timezone.now, verbose_name="Ovoz berilgan vaqt")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP manzil")

    class Meta:
        verbose_name = "Ovoz"
        verbose_name_plural = "Ovozlar"
        ordering = ['-voted_at']
        unique_together = ['user', 'poll']

    def __str__(self):
        return f"{self.user.full_name} → {self.candidate.full_name} ({self.poll.title})"

    def save(self, *args, **kwargs):
        """Ovoz berilganda poll ni avtomatik belgilash"""
        if not self.poll_id and self.candidate:
            self.poll = self.candidate.district.region.poll
        super().save(*args, **kwargs)
