from django.db import models
from django.conf import settings

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
        ('pending', 'Pending'),
        ('purchased', 'Purchased'),
        ('given', 'Given'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    recipients = models.ManyToManyField(Recipient, related_name='gift_ideas')
    occasions = models.ManyToManyField(Occasion, related_name='gift_ideas', blank=True)
    tags = models.ManyToManyField(Tag, related_name='gift_ideas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
