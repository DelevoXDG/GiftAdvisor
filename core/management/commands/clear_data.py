from django.core.management.base import BaseCommand
from core.models import Tag, Occasion, Recipient, GiftIdea

class Command(BaseCommand):
    help = 'Clears all gift-related data while preserving user accounts'

    def handle(self, *args, **options):
        # Delete all gift ideas first (to handle foreign key relationships)
        gift_count = GiftIdea.objects.count()
        GiftIdea.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {gift_count} gift ideas'))
        
        # Delete all recipients
        recipient_count = Recipient.objects.count()
        Recipient.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {recipient_count} recipients'))
        
        # Delete all occasions
        occasion_count = Occasion.objects.count()
        Occasion.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {occasion_count} occasions'))
        
        # Delete all tags
        tag_count = Tag.objects.count()
        Tag.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {tag_count} tags'))
        
        self.stdout.write(self.style.SUCCESS('Successfully cleared all gift-related data')) 