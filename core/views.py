from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import GiftIdea, Tag, Recipient
from django.db.models import Min, Max
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .services.metadata_extractor import MetadataExtractor
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
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
                # Try to find the test user's gifts
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

class RecipientsView(LoginRequiredMixin, TemplateView):
    template_name = 'recipients.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context.update({
            'recipients': Recipient.objects.filter(user=user).order_by('name'),
            'tags': Tag.objects.all().order_by('name'),
            'relationship_choices': Recipient.RELATIONSHIP_CHOICES,
        })
        
        return context

@require_http_methods(["GET", "POST"])
def recipients_list(request):
    """Handle recipient listing and creation."""
    if request.method == "GET":
        recipients = Recipient.objects.filter(user=request.user)
        return JsonResponse([{
            'id': r.id,
            'name': r.name,
            'relationship': r.relationship,
            'birth_date': r.birth_date.isoformat() if r.birth_date else None,
            'interests': list(r.interests.values_list('id', flat=True)),
            'notes': r.notes,
            'gift_count': r.gift_ideas.count()
        } for r in recipients], safe=False)
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            recipient = Recipient.objects.create(
                user=request.user,
                name=data['name'],
                relationship=data['relationship'],
                birth_date=data.get('birth_date'),
                notes=data.get('notes', '')
            )
            
            if 'interests' in data:
                recipient.interests.set(data['interests'])
            
            return JsonResponse({
                'message': 'Recipient added successfully',
                'id': recipient.id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["GET", "PUT", "DELETE"])
def recipient_detail(request, recipient_id):
    """Handle individual recipient operations."""
    recipient = get_object_or_404(Recipient, id=recipient_id, user=request.user)
    
    if request.method == "GET":
        return JsonResponse({
            'id': recipient.id,
            'name': recipient.name,
            'relationship': recipient.relationship,
            'birth_date': recipient.birth_date.isoformat() if recipient.birth_date else None,
            'interests': list(recipient.interests.values_list('id', flat=True)),
            'notes': recipient.notes
        })
    
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            
            recipient.name = data['name']
            recipient.relationship = data['relationship']
            recipient.birth_date = data.get('birth_date')
            recipient.notes = data.get('notes', '')
            recipient.save()
            
            if 'interests' in data:
                recipient.interests.set(data['interests'])
            
            return JsonResponse({'message': 'Recipient updated successfully'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    elif request.method == "DELETE":
        try:
            recipient.delete()
            return JsonResponse({'message': 'Recipient deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

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
            image_url=data.get('image_url', ''),
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
