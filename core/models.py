from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

class Tag(models.Model):
    """Model for categorizing gifts and recipients."""
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Occasion(models.Model):
    """Model for special occasions and events."""
    name = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.date})"

class Recipient(models.Model):
    """Model for gift recipients."""
    RELATIONSHIP_CHOICES = [
        ('family', 'Family'),
        ('friend', 'Friend'),
        ('colleague', 'Colleague'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    birth_date = models.DateField(null=True, blank=True)
    interests = models.ManyToManyField(Tag, related_name='interested_recipients')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_relationship_display()})"

class GiftIdea(models.Model):
    """Model for gift ideas."""
    STATUS_CHOICES = [
        ('idea', 'Idea'),
        ('gifted', 'Gifted'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idea')
    recipients = models.ManyToManyField(Recipient, related_name='gift_ideas')
    occasions = models.ManyToManyField(Occasion, related_name='gift_ideas', blank=True)
    tags = models.ManyToManyField(Tag, related_name='gift_ideas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class UserPreferences(models.Model):
    """Model for storing user preferences including AI model settings."""
    AI_MODEL_CHOICES = [
        ('none', 'No model'),
        ('openai', 'OpenAI'),
        ('deepseek', 'Deepseek'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    current_ai_model = models.CharField(max_length=20, choices=AI_MODEL_CHOICES, default='none')
    openai_key = models.CharField(max_length=100, null=True, blank=True)
    deepseek_key = models.CharField(max_length=100, null=True, blank=True)
    openai_model = models.CharField(max_length=50, default='gpt-3.5-turbo', null=True, blank=True)
    deepseek_model = models.CharField(max_length=50, default='deepseek-chat', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.email}"

class PurchaseRecord(models.Model):
    """Model for tracking gift purchases and feedback."""
    gift = models.ForeignKey(GiftIdea, on_delete=models.CASCADE, related_name='purchases')
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, related_name='received_gifts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    purchase_date = models.DateField(default=timezone.now)
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchase_date']

    def save(self, *args, **kwargs):
        # Update gift status to 'gifted' when creating a purchase record
        if not self.pk:  # Only on creation
            self.gift.status = 'gifted'
            self.gift.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.gift.title} - Gifted to {self.recipient.name} on {self.purchase_date}"
