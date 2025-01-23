from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import GiftIdea, Tag, Recipient, UserPreferences, PurchaseRecord
from django.db.models import Min, Max
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .services.metadata_extractor import MetadataExtractor
from django.views.decorators.http import require_http_methods, require_POST
from django.shortcuts import get_object_or_404
import json
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.ai_processor import AIProcessor
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

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
            
            # Apply search
            search_query = self.request.GET.get('search')
            if search_query:
                gifts = gifts.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(tags__name__icontains=search_query) |
                    Q(recipients__name__icontains=search_query)
                ).distinct()
            
            # Apply filters
            price_range = self.request.GET.get('price_range')
            recipient_filter = self.request.GET.get('recipient')
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
                
            if status_filter:
                gifts = gifts.filter(status=status_filter)
            
            # Apply sorting
            sort_by = self.request.GET.get('sort', 'recent')
            if sort_by == 'price_low':
                gifts = gifts.order_by('price')
            elif sort_by == 'price_high':
                gifts = gifts.order_by('-price')
            else:  # recent
                gifts = gifts.order_by('-created_at')
            
            # Get filter options
            price_stats = gifts.aggregate(
                min_price=Min('price'),
                max_price=Max('price')
            )
            
            # Apply pagination
            page = self.request.GET.get('page', 1)
            paginator = Paginator(gifts, 12)  # Show 12 gifts per page
            
            try:
                gifts = paginator.page(page)
            except PageNotAnInteger:
                gifts = paginator.page(1)
            except EmptyPage:
                gifts = paginator.page(paginator.num_pages)
            
            # Build current filters dict only including non-None values
            current_filters = {}
            if price_range:
                current_filters['price_range'] = price_range
            if recipient_filter:
                current_filters['recipient'] = recipient_filter
            if status_filter:
                current_filters['status'] = status_filter
            if sort_by != 'recent':
                current_filters['sort'] = sort_by
            if search_query:
                current_filters['search'] = search_query
            
            context.update({
                'gifts': gifts,
                'tags': Tag.objects.filter(gift_ideas__user=user).distinct(),
                'recipients': Recipient.objects.filter(user=user),
                'price_stats': price_stats,
                'relationship_choices': Recipient.RELATIONSHIP_CHOICES,
                'status_choices': GiftIdea.STATUS_CHOICES,
                'current_filters': current_filters
            })
            
        return context

class RecipientsView(LoginRequiredMixin, TemplateView):
    template_name = 'recipients.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get base queryset
        recipients = Recipient.objects.filter(user=user)
        
        # Apply search if provided
        search_query = self.request.GET.get('search')
        if search_query:
            recipients = recipients.filter(
                Q(name__icontains=search_query) |
                Q(notes__icontains=search_query) |
                Q(interests__name__icontains=search_query)
            ).distinct()
        
        # Order by name
        recipients = recipients.order_by('name')
        
        context.update({
            'recipients': recipients,
            'tags': Tag.objects.all().order_by('name'),
            'relationship_choices': Recipient.RELATIONSHIP_CHOICES,
            'search_query': search_query,
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

@require_http_methods(["GET", "PUT"])
def recipient_detail(request, recipient_id):
    """Handle individual recipient operations."""
    recipient = get_object_or_404(Recipient, id=recipient_id, user=request.user)
    
    if request.method == "GET":
        return JsonResponse({
            'id': recipient.id,
            'name': recipient.name,
            'relationship': recipient.relationship,
            'birth_date': recipient.birth_date.isoformat() if recipient.birth_date else None,
            'notes': recipient.notes,
            'interests': list(recipient.interests.values('id', 'name'))
        })
    
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            
            recipient.name = data['name']
            recipient.relationship = data['relationship']
            recipient.birth_date = data.get('birth_date')
            recipient.notes = data.get('notes', '')
            recipient.save()
            
            # Handle interests
            if 'interests' in data:
                interest_names = [name.strip() for name in data['interests'].split(',') if name.strip()]
                interests = []
                for name in interest_names:
                    interest, _ = Tag.objects.get_or_create(name=name)
                    interests.append(interest)
                recipient.interests.set(interests)
            
            return JsonResponse({'message': 'Recipient updated successfully'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["DELETE"])
def recipient_detail(request, recipient_id):
    """Handle individual recipient operations."""
    recipient = get_object_or_404(Recipient, id=recipient_id, user=request.user)
    
    if request.method == "DELETE":
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
        
        # Start AI processing
        processor = AIProcessor(request.user)
        success, suggestions, error = processor.process_gift_idea(data)
        
        if success:
            # Update gift data with AI suggestions
            data['title'] = suggestions.get('title', data['title'])
            data['description'] = suggestions.get('description', data.get('description', ''))
            
            # Create the gift idea
            gift = GiftIdea.objects.create(
                user=request.user,
                title=data['title'],
                description=data['description'],
                price=data.get('price'),
                url=data.get('url', ''),
                image_url=data.get('image_url', ''),
                status='idea'
            )
            
            # Add suggested tags
            suggested_tags = suggestions.get('tags', [])
            if suggested_tags:
                tags = Tag.objects.filter(name__in=suggested_tags)
                gift.tags.set(tags)
            
            # Add suggested recipients
            suggested_recipients = suggestions.get('recipients', [])
            if suggested_recipients:
                recipients = Recipient.objects.filter(
                    id__in=suggested_recipients,
                    user=request.user
                )
                gift.recipients.set(recipients)
            
            messages.success(
                request, 
                f'Gift idea added successfully! {suggestions.get("reasoning", "")}'
            )
        else:
            # If AI processing failed, create gift without suggestions
            gift = GiftIdea.objects.create(
                user=request.user,
                title=data['title'],
                description=data.get('description', ''),
                price=data.get('price'),
                url=data.get('url', ''),
                image_url=data.get('image_url', ''),
                status='idea'
            )
            
            if error:
                messages.warning(
                    request, 
                    f'Gift idea added, but AI processing failed: {error}'
                )
            else:
                messages.success(request, 'Gift idea added successfully!')
        
        return JsonResponse({
            'message': 'Gift idea added successfully',
            'id': gift.id,
            'ai_processed': success
        })
        
    except Exception as e:
        messages.error(request, f'Failed to add gift idea: {str(e)}')
        return JsonResponse({'error': str(e)}, status=400)

class RecipientProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'recipient_profile.html'
    
    def post(self, request, *args, **kwargs):
        recipient_id = kwargs.get('recipient_id')
        recipient = get_object_or_404(Recipient, id=recipient_id, user=request.user)
        
        # Handle recipient update
        recipient.name = request.POST.get('name')
        recipient.relationship = request.POST.get('relationship')
        recipient.birth_date = request.POST.get('birth_date') or None
        recipient.notes = request.POST.get('notes', '')
        recipient.save()
        
        messages.success(request, f"{recipient.name}'s details have been updated successfully.")
        return redirect('recipient_profile', recipient_id=recipient_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipient_id = kwargs.get('recipient_id')
        recipient = get_object_or_404(Recipient, id=recipient_id, user=self.request.user)
        
        # Get all gifts for this recipient
        gifts = recipient.gift_ideas.all()
        
        # Apply search filter
        search_query = self.request.GET.get('search')
        if search_query:
            gifts = gifts.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()
        
        # Apply price range filter
        price_range = self.request.GET.get('price_range')
        if price_range:
            if price_range == 'under_25':
                gifts = gifts.filter(price__lt=25)
            elif price_range == '25_50':
                gifts = gifts.filter(price__gte=25, price__lt=50)
            elif price_range == '50_100':
                gifts = gifts.filter(price__gte=50, price__lt=100)
            elif price_range == 'over_100':
                gifts = gifts.filter(price__gte=100)
        
        # Apply status filter
        status = self.request.GET.get('status')
        if status:
            gifts = gifts.filter(status=status)
        
        # Apply sorting
        sort = self.request.GET.get('sort', 'recent')
        if sort == 'recent':
            gifts = gifts.order_by('-created_at')
        elif sort == 'price_low':
            gifts = gifts.order_by('price')
        elif sort == 'price_high':
            gifts = gifts.order_by('-price')
        
        # Pagination
        paginator = Paginator(gifts, 12)  # Show 12 gifts per page
        page = self.request.GET.get('page')
        try:
            gifts = paginator.page(page)
        except PageNotAnInteger:
            gifts = paginator.page(1)
        except EmptyPage:
            gifts = paginator.page(paginator.num_pages)
        
        # Current filters for form
        current_filters = {
            'search': search_query,
            'price_range': price_range,
            'status': status,
            'sort': sort
        }
        
        context.update({
            'recipient': recipient,
            'gifts': gifts,
            'tags': Tag.objects.all().order_by('name'),
            'relationship_choices': Recipient.RELATIONSHIP_CHOICES,
            'status_choices': GiftIdea.STATUS_CHOICES,
            'current_filters': current_filters,
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

@login_required
def gift_detail(request, gift_id):
    """View for displaying gift details."""
    gift = get_object_or_404(GiftIdea, id=gift_id, user=request.user)
    
    # Get similar gifts based on tags
    similar_gifts = GiftIdea.objects.filter(
        user=request.user,
        tags__in=gift.tags.all()
    ).exclude(id=gift.id).distinct()[:4]
    
    context = {
        'gift': gift,
        'similar_gifts': similar_gifts,
        'today': timezone.now().date(),
        'all_recipients': Recipient.objects.filter(user=request.user),
        'all_tags': Tag.objects.all(),
        'status_choices': GiftIdea.STATUS_CHOICES,
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
            
            if 'tags' in data:
                gift.tags.set(data['tags'])
            
            if 'recipients' in data:
                gift.recipients.set(data['recipients'])
            
            gift.save()
            
            return JsonResponse({'message': 'Gift updated successfully'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    elif request.method == "DELETE":
        try:
            gift.delete()
            return JsonResponse({'message': 'Gift deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

def get_or_create_tags(tag_names):
    """Convert tag names to tag IDs, creating tags if they don't exist."""
    tags = []
    for name in tag_names:
        tag, _ = Tag.objects.get_or_create(name=name)
        tags.append(tag.id)
    return tags

@require_http_methods(["POST"])
def process_gift_with_ai(request, gift_id):
    """Process a gift idea with AI to get tag and recipient suggestions."""
    try:
        gift = GiftIdea.objects.get(id=gift_id, user=request.user)
    except GiftIdea.DoesNotExist:
        return JsonResponse({'error': 'Gift not found'}, status=404)
    
    # Initialize AI processor
    processor = AIProcessor(request.user)
    
    # Process the gift
    success, suggestions, error = processor.process_gift_idea({
        'title': gift.title,
        'description': gift.description,
        'price': gift.price,
        'url': gift.url
    })
    
    if not success:
        return JsonResponse({'error': error or 'Failed to process with AI'}, status=400)
    
    try:
        # Update the gift with AI suggestions
        if 'tags' in suggestions:
            # Convert tag names to IDs
            tag_ids = get_or_create_tags(suggestions['tags'])
            gift.tags.set(tag_ids)
            
        if 'recipients' in suggestions:
            # Ensure all recipient IDs exist and belong to the user
            valid_recipient_ids = list(
                Recipient.objects.filter(
                    id__in=suggestions['recipients'], 
                    user=request.user
                ).values_list('id', flat=True)
            )
            gift.recipients.set(valid_recipient_ids)
            
        if 'title' in suggestions:
            gift.title = suggestions['title']
            
        if 'description' in suggestions:
            gift.description = suggestions['description']
            
        gift.save()
        
        return JsonResponse({
            'message': 'Successfully processed gift with AI',
            'suggestions': {
                'title': gift.title,
                'description': gift.description,
                'tags': list(gift.tags.values_list('name', flat=True)),
                'recipients': list(gift.recipients.values_list('id', flat=True)),
                'reasoning': suggestions.get('reasoning', '')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to update gift with AI suggestions: {str(e)}'
        }, status=400)

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
                context['openai_key_display'] = f"{preferences.openai_key[:8]}•••••{preferences.openai_key[-4:]}"
            if preferences.deepseek_key:
                context['deepseek_key_display'] = f"{preferences.deepseek_key[:8]}•••••{preferences.deepseek_key[-4:]}"
                
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

@login_required
def purchases(request):
    """View for listing all purchase records with search and pagination"""
    search_query = request.GET.get('search', '')
    
    # Base queryset
    purchases = PurchaseRecord.objects.filter(user=request.user)
    
    # Apply search if provided
    if search_query:
        purchases = purchases.filter(
            Q(gift__title__icontains=search_query) |
            Q(recipient__name__icontains=search_query) |
            Q(feedback__icontains=search_query)
        )
    
    # Order by most recent first
    purchases = purchases.order_by('-purchase_date')
    
    # Pagination
    paginator = Paginator(purchases, 10)  # Show 10 purchases per page
    page = request.GET.get('page')
    
    try:
        purchases = paginator.page(page)
    except PageNotAnInteger:
        purchases = paginator.page(1)
    except EmptyPage:
        purchases = paginator.page(paginator.num_pages)
    
    return render(request, 'purchases.html', {
        'purchases': purchases,
        'search_query': search_query
    })

@login_required
def record_purchase(request, gift_id):
    """View for recording a new purchase"""
    gift = get_object_or_404(GiftIdea, id=gift_id, user=request.user)
    
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        purchase_date = request.POST.get('purchase_date')
        feedback = request.POST.get('feedback')
        
        try:
            recipient = Recipient.objects.get(id=recipient_id, user=request.user)
            
            # Create purchase record
            PurchaseRecord.objects.create(
                gift=gift,
                recipient=recipient,
                user=request.user,
                purchase_date=purchase_date or timezone.now().date(),
                feedback=feedback
            )
            
            messages.success(request, 'Purchase recorded successfully!')
            return redirect('gift_detail', gift_id=gift_id)
            
        except Recipient.DoesNotExist:
            messages.error(request, 'Invalid recipient selected.')
            return redirect('gift_detail', gift_id=gift_id)
    
    return redirect('gift_detail', gift_id=gift_id)

@login_required
def update_purchase_feedback(request, purchase_id):
    """View for updating purchase details"""
    purchase = get_object_or_404(PurchaseRecord, id=purchase_id, user=request.user)
    
    if request.method == 'POST':
        feedback = request.POST.get('feedback')
        purchase_date = request.POST.get('purchase_date')
        
        purchase.feedback = feedback
        if purchase_date:
            purchase.purchase_date = purchase_date
        purchase.save()
        
        messages.success(request, 'Purchase details updated successfully!')
    
    return redirect('purchases')

@login_required
def delete_purchase(request, purchase_id):
    """View for deleting a purchase record"""
    purchase = get_object_or_404(PurchaseRecord, id=purchase_id, user=request.user)
    purchase.delete()
    messages.success(request, 'Purchase record deleted successfully!')
    return redirect('purchases')

@login_required
def delete_gift(request, gift_id):
    """View for deleting a gift idea"""
    gift = get_object_or_404(GiftIdea, id=gift_id, user=request.user)
    gift.delete()
    messages.success(request, 'Gift idea deleted successfully!')
    return redirect('index')

@login_required
def delete_recipient(request, recipient_id):
    """View for deleting a recipient"""
    recipient = get_object_or_404(Recipient, id=recipient_id, user=request.user)
    recipient.delete()
    messages.success(request, 'Recipient deleted successfully!')
    return redirect('recipients')

@login_required
def add_recipient_interest(request, recipient_id):
    """Add an interest to a recipient."""
    if request.method != 'POST':
        return redirect('recipient_profile', recipient_id=recipient_id)
        
    recipient = get_object_or_404(Recipient, id=recipient_id, user=request.user)
    interest_name = request.POST.get('interest', '').strip()
    
    if interest_name:
        # Get or create the interest tag
        interest, _ = Tag.objects.get_or_create(name=interest_name)
        recipient.interests.add(interest)
        messages.success(request, f'Added interest: {interest_name}')
    
    return redirect('recipient_profile', recipient_id=recipient_id)

@login_required
def remove_recipient_interest(request, recipient_id, interest_id):
    """Remove an interest from a recipient."""
    if request.method != 'POST':
        return redirect('recipient_profile', recipient_id=recipient_id)
        
    recipient = get_object_or_404(Recipient, id=recipient_id, user=request.user)
    interest = get_object_or_404(Tag, id=interest_id)
    
    recipient.interests.remove(interest)
    messages.success(request, f'Removed interest: {interest.name}')
    
    return redirect('recipient_profile', recipient_id=recipient_id)
