from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import GiftIdea, Tag, Recipient
from django.db.models import Min, Max
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .services.metadata_extractor import MetadataExtractor
from django.views.decorators.http import require_http_methods
import json

User = get_user_model()

class IndexView(TemplateView):
    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ['dashboard.html']
        return ['index.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            # Get test user if current user has no gifts
            user = self.request.user
            gifts = GiftIdea.objects.filter(user=user)
            
            if not gifts.exists():
                # Try to find the test user's gifts
                test_user = User.objects.filter(email='test@example.com').first()
                if test_user:
                    gifts = GiftIdea.objects.filter(user=test_user)
            
            # Apply filters
            price_range = self.request.GET.get('price_range')
            recipient_filter = self.request.GET.get('recipient')
            tag_filter = self.request.GET.get('tag')
            status_filter = self.request.GET.get('status')
            
            if price_range:
                ranges = {
                    'under_25': (0, 25),
                    '25_50': (25, 50),
                    '50_100': (50, 100),
                    'over_100': (100, 1000000)
                }
                if price_range in ranges:
                    min_price, max_price = ranges[price_range]
                    gifts = gifts.filter(price__gte=min_price, price__lt=max_price)
            
            if recipient_filter:
                gifts = gifts.filter(recipients__relationship=recipient_filter)
            
            if tag_filter:
                gifts = gifts.filter(tags__name=tag_filter)
                
            if status_filter:
                gifts = gifts.filter(status=status_filter)
            
            # Get filter options
            price_stats = gifts.aggregate(
                min_price=Min('price'),
                max_price=Max('price')
            )
            
            context.update({
                'gifts': gifts.distinct().order_by('-created_at'),
                'tags': Tag.objects.filter(gift_ideas__user=user).distinct(),
                'recipients': Recipient.objects.filter(user=user),
                'price_stats': price_stats,
                'relationship_choices': Recipient.RELATIONSHIP_CHOICES,
                'status_choices': GiftIdea.STATUS_CHOICES,
                'current_filters': {
                    'price_range': price_range,
                    'recipient': recipient_filter,
                    'tag': tag_filter,
                    'status': status_filter
                }
            })
            
        return context

@require_http_methods(["POST"])
def extract_metadata(request):
    """Extract metadata from a product URL."""
    try:
        data = json.loads(request.body)
        url = data.get('url')
        
        if not url:
            return JsonResponse({'error': 'URL is required'}, status=400)
        
        extractor = MetadataExtractor()
        metadata = extractor.extract(url)
        
        if 'error' in metadata:
            return JsonResponse({'error': metadata['error']}, status=400)
        
        return JsonResponse(metadata)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def add_gift(request):
    """Add a new gift idea."""
    try:
        data = json.loads(request.body)
        
        # Create the gift idea
        gift = GiftIdea.objects.create(
            user=request.user,
            title=data.get('title'),
            description=data.get('description', ''),
            price=data.get('price'),
            url=data.get('url', ''),
            status='idea'
        )
        
        # Add recipients if provided
        if 'recipients' in data:
            gift.recipients.set(data['recipients'])
        
        # Handle tags
        if 'tags' in data:
            gift.tags.set(data['tags'])
        
        return JsonResponse({
            'message': 'Gift idea added successfully',
            'id': gift.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
