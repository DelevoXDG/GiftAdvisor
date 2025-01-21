from django.contrib import admin
from .models import Tag, Occasion, Recipient, GiftIdea, UserPreferences

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'user', 'created_at')
    list_filter = ('date', 'user')
    search_fields = ('name', 'description')

@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('name', 'relationship', 'user', 'birth_date', 'created_at')
    list_filter = ('relationship', 'user')
    search_fields = ('name', 'notes')
    filter_horizontal = ('interests',)

@admin.register(GiftIdea)
class GiftIdeaAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'price', 'status', 'created_at')
    list_filter = ('status', 'user', 'tags')
    search_fields = ('title', 'description')
    filter_horizontal = ('recipients', 'occasions', 'tags')

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_openai_key', 'created_at', 'updated_at')
    list_filter = ('user',)
    search_fields = ('user__email', 'user__username')
    
    def has_openai_key(self, obj):
        return bool(obj.openai_key)
    has_openai_key.boolean = True
    has_openai_key.short_description = 'Has OpenAI Key'
