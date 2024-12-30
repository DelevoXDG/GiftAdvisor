from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Tag, Occasion, Recipient, GiftIdea
from faker import Faker
from decimal import Decimal
import random
from datetime import date, timedelta

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Generates fake data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--gifts', type=int, default=10, help='Number of gift ideas to generate')

    def handle(self, *args, **options):
        num_gifts = options['gifts']
        
        # Create a test user if none exists
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'password': 'admin'}
        )
        if created:
            user.set_password('admin')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created test user: {user.email}'))
        
        # Create tags
        tags = []
        tag_names = ['Birthday', 'Christmas', 'Anniversary', 'Wedding', 'Graduation', 
                    'Housewarming', 'Baby Shower', 'Valentine\'s Day', 'Tech', 'Books', 
                    'Fashion', 'Home & Garden', 'Sports', 'Music', 'Art']
        
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tags.append(tag)
            if created:
                self.stdout.write(f'Created tag: {tag.name}')
        
        # Create recipients
        recipients = []
        relationships = ['family', 'friend', 'colleague', 'other']
        
        for _ in range(5):
            recipient = Recipient.objects.create(
                user=user,
                name=fake.name(),
                relationship=random.choice(relationships),
                birth_date=fake.date_of_birth(minimum_age=18, maximum_age=80),
                notes=fake.text(max_nb_chars=200)
            )
            recipient.interests.set(random.sample(tags, k=random.randint(1, 3)))
            recipients.append(recipient)
            self.stdout.write(f'Created recipient: {recipient.name}')
        
        # Create occasions
        occasions = []
        for _ in range(3):
            occasion = Occasion.objects.create(
                user=user,
                name=random.choice(['Birthday Party', 'Christmas Gathering', 'Wedding Anniversary']),
                date=date.today() + timedelta(days=random.randint(1, 365)),
                description=fake.text(max_nb_chars=200)
            )
            occasions.append(occasion)
            self.stdout.write(f'Created occasion: {occasion.name}')
        
        # Create gift ideas
        for i in range(num_gifts):
            gift = GiftIdea.objects.create(
                user=user,
                title=fake.catch_phrase(),
                description=fake.text(max_nb_chars=200),
                price=Decimal(random.uniform(10, 500)).quantize(Decimal('0.01')),
                url=fake.url(),
                status=random.choice(['idea', 'gifted'])
            )
            
            # Add random relationships
            gift.recipients.set(random.sample(recipients, k=random.randint(1, 3)))
            gift.occasions.set(random.sample(occasions, k=random.randint(0, 2)))
            gift.tags.set(random.sample(tags, k=random.randint(1, 4)))
            
            self.stdout.write(f'Created gift idea {i+1}/{num_gifts}: {gift.title}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully generated {num_gifts} gift ideas!')) 