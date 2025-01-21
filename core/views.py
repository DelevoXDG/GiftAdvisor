from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import GiftIdea, Tag, Recipient, UserPreferences
from django.db.models import Min, Max
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .services.metadata_extractor import MetadataExtractor
from django.views.decorators.http import require_http_methods, require_POST
from django.shortcuts import get_object_or_404
import json
from django.db.models import Q
from django.contrib.auth.decorators import login_required

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

class RecipientProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'recipient_profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipient_id = kwargs.get('recipient_id')
        recipient = get_object_or_404(Recipient, id=recipient_id, user=self.request.user)
        
        context.update({
            'recipient': recipient,
            'gifts': recipient.gift_ideas.all().order_by('-created_at'),
            'tags': Tag.objects.all().order_by('name'),
            'relationship_choices': Recipient.RELATIONSHIP_CHOICES,
        })
        
        return context

@require_http_methods(["GET"])
def search_gifts(request):
    """Search through all gift ideas."""
    query = request.GET.get('q', '')
    user = request.user
    
    gifts = GiftIdea.objects.filter(user=user)
    
    if query:
        gifts = gifts.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    
    gifts = gifts.order_by('-created_at')[:20]  # Limit to 20 most recent matches
    
    return JsonResponse([{
        'id': gift.id,
        'title': gift.title,
        'description': gift.description,
        'price': float(gift.price) if gift.price else None,
        'image_url': gift.image_url,
        'tags': [{'id': tag.id, 'name': tag.name} for tag in gift.tags.all()]
    } for gift in gifts], safe=False)

@require_http_methods(["GET"])
def recent_gifts(request):
    """Get recent gift ideas."""
    user = request.user
    gifts = GiftIdea.objects.filter(user=user).order_by('-created_at')[:12]  # Last 12 gifts
    
    return JsonResponse([{
        'id': gift.id,
        'title': gift.title,
        'description': gift.description,
        'price': float(gift.price) if gift.price else None,
        'image_url': gift.image_url,
        'tags': [{'id': tag.id, 'name': tag.name} for tag in gift.tags.all()]
    } for gift in gifts], safe=False)

@require_http_methods(["POST"])
def add_gift_to_recipient(request, recipient_id):
    """Add an existing gift idea to a recipient."""
    try:
        data = json.loads(request.body)
        gift_id = data.get('gift_id')
        
        recipient = get_object_or_404(Recipient, id=recipient_id, user=request.user)
        gift = get_object_or_404(GiftIdea, id=gift_id, user=request.user)
        
        recipient.gift_ideas.add(gift)
        
        return JsonResponse({
            'message': 'Gift added successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def gift_detail(request, gift_id):
    gift = get_object_or_404(GiftIdea, id=gift_id)
    
    # Get similar gifts based on shared tags
    similar_gifts = GiftIdea.objects.filter(
        tags__in=gift.tags.all()
    ).exclude(
        id=gift.id
    ).distinct()[:6]  # Limit to 6 similar gifts
    
    context = {
        'gift': gift,
        'similar_gifts': similar_gifts,
        'status_choices': GiftIdea.STATUS_CHOICES,
        'all_tags': Tag.objects.all(),
        'all_recipients': Recipient.objects.all(),
    }
    
    return render(request, 'gift_detail.html', context)

@require_http_methods(["GET", "PUT", "DELETE"])
def gift_detail_api(request, gift_id):
    """Handle individual gift operations."""
    gift = get_object_or_404(GiftIdea, id=gift_id, user=request.user)
    
    if request.method == "GET":
        return JsonResponse({
            'id': gift.id,
            'title': gift.title,
            'description': gift.description,
            'price': float(gift.price) if gift.price else None,
            'url': gift.url,
            'image_url': gift.image_url,
            'status': gift.status,
            'notes': gift.notes,
            'tags': list(gift.tags.values_list('id', flat=True)),
            'recipients': list(gift.recipients.values_list('id', flat=True))
        })
    
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            
            gift.title = data['title']
            gift.price = data['price']
            gift.status = data['status']
            gift.url = data.get('url', '')
            gift.image_url = data.get('image_url', '')
            gift.description = data.get('description', '')
            gift.notes = data.get('notes', '')
            gift.save()
            
            if 'tags' in data:
                gift.tags.set(data['tags'])
            
            if 'recipients' in data:
                gift.recipients.set(data['recipients'])
            
            return JsonResponse({'message': 'Gift updated successfully'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    elif request.method == "DELETE":
        try:
            gift.delete()
            return JsonResponse({'message': 'Gift deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class PreferencesView(LoginRequiredMixin, TemplateView):
    template_name = 'preferences.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            preferences = UserPreferences.objects.get(user=self.request.user)
            context['has_openai_key'] = bool(preferences.openai_key)
            context['has_deepseek_key'] = bool(preferences.deepseek_key)
            context['current_ai_model'] = preferences.current_ai_model
            context['openai_model'] = preferences.openai_model
            context['deepseek_model'] = preferences.deepseek_model
            
            # Pass the sliced API keys for display
            if preferences.openai_key:
                context['openai_key_display'] = f"{preferences.openai_key[:8]}...{preferences.openai_key[-4:]}"
            if preferences.deepseek_key:
                context['deepseek_key_display'] = f"{preferences.deepseek_key[:8]}...{preferences.deepseek_key[-4:]}"
                
        except UserPreferences.DoesNotExist:
            context['has_openai_key'] = False
            context['has_deepseek_key'] = False
            context['current_ai_model'] = 'none'
            context['openai_model'] = 'gpt-3.5-turbo'
            context['deepseek_model'] = 'deepseek-chat'
        return context

@login_required
@require_POST
def update_openai_model(request):
    try:
        data = json.loads(request.body)
        model = data.get('model')
        
        if not model:
            return JsonResponse({'error': 'Model selection is required'}, status=400)
            
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        preferences.openai_model = model
        preferences.save()
        
        return JsonResponse({'message': 'OpenAI model updated successfully'})
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def update_deepseek_model(request):
    try:
        data = json.loads(request.body)
        model = data.get('model')
        
        if not model:
            return JsonResponse({'error': 'Model selection is required'}, status=400)
            
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        preferences.deepseek_model = model
        preferences.save()
        
        return JsonResponse({'message': 'Deepseek model updated successfully'})
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def update_openai_key(request):
    try:
        data = json.loads(request.body)
        api_key = data.get('api_key')
        
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        
        if api_key is None:
            # Remove the key
            preferences.openai_key = None
            preferences.save()
            return JsonResponse({'message': 'OpenAI API key removed successfully'})
        else:
            # Validate and save the key
            if not api_key.startswith('sk-'):
                return JsonResponse({'error': 'Invalid API key format'}, status=400)
            
            preferences.openai_key = api_key
            preferences.save()
            return JsonResponse({'message': 'OpenAI API key saved successfully'})
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def update_deepseek_key(request):
    try:
        data = json.loads(request.body)
        api_key = data.get('api_key')
        
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        
        if api_key is None:
            # Remove the key
            preferences.deepseek_key = None
            preferences.save()
            return JsonResponse({'message': 'Deepseek API key removed successfully'})
        else:
            # Validate and save the key
            if not api_key.startswith('sk-'):
                return JsonResponse({'error': 'Invalid API key format'}, status=400)
            
            preferences.deepseek_key = api_key
            preferences.save()
            return JsonResponse({'message': 'Deepseek API key saved successfully'})
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def update_current_model(request):
    try:
        data = json.loads(request.body)
        current_model = data.get('current_ai_model')
        
        if current_model not in dict(UserPreferences.AI_MODEL_CHOICES):
            return JsonResponse({'error': 'Invalid model selection'}, status=400)
        
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        preferences.current_ai_model = current_model
        preferences.save()
        
        return JsonResponse({'message': 'AI model preference updated successfully'})
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def fetch_openai_models(request):
    try:
        preferences = UserPreferences.objects.get(user=request.user)
        if not preferences.openai_key:
            return JsonResponse({'error': 'OpenAI API key not configured'}, status=400)
            
        from openai import OpenAI
        client = OpenAI(api_key=preferences.openai_key)
        
        models = client.models.list()
        available_models = []
        
        # Filter for GPT models only
        for model in models:
            if any(prefix in model.id for prefix in ['gpt-3.5', 'gpt-4']):
                available_models.append({
                    'id': model.id,
                    'name': model.id.replace('gpt-', 'GPT-').replace('-turbo', ' Turbo')
                })
        
        return JsonResponse({'models': available_models})
        
    except UserPreferences.DoesNotExist:
        return JsonResponse({'error': 'User preferences not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def fetch_deepseek_models(request):
    try:
        preferences = UserPreferences.objects.get(user=request.user)
        if not preferences.deepseek_key:
            return JsonResponse({'error': 'Deepseek API key not configured'}, status=400)
            
        from openai import OpenAI
        client = OpenAI(api_key=preferences.deepseek_key, base_url="https://api.deepseek.com/v1")
        
        models = client.models.list()
        available_models = []
        
        for model in models:
            available_models.append({
                'id': model.id,
                'name': model.id.replace('-', ' ').title()
            })
        
        return JsonResponse({'models': available_models})
        
    except UserPreferences.DoesNotExist:
        return JsonResponse({'error': 'User preferences not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
