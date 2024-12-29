from django.contrib import admin
from .models import Tag, Occasion, Recipient, GiftIdea

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
