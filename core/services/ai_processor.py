from openai import OpenAI
from django.conf import settings
from core.models import UserPreferences, Recipient, Tag
import json
from typing import Dict, Optional, Tuple

class AIProcessor:
    """Service for processing gift ideas using AI models."""
    
    def __init__(self, user):
        """Initialize with user to get their AI preferences."""
        self.user = user
        self._client = None
        self._preferences = None
        self._session_key = None
    
    @property
    def preferences(self) -> Optional[UserPreferences]:
        """Get user preferences, cached for the instance."""
        if self._preferences is None:
            self._preferences = UserPreferences.objects.filter(user=self.user).first()
        return self._preferences
    
    @property
    def client(self) -> Optional[OpenAI]:
        """Get OpenAI client based on user preferences."""
        if self._client is not None:
            return self._client
            
        if not self.preferences or self.preferences.current_ai_model == 'none':
            return None
            
        api_key = None
        base_url = None
        
        if self.preferences.current_ai_model == 'openai':
            api_key = self.preferences.openai_key
        elif self.preferences.current_ai_model == 'deepseek':
            api_key = self.preferences.deepseek_key
            base_url = "https://api.deepseek.com/v1"
        
        if not api_key:
            return None
            
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        return self._client
    
    def process_gift_idea(self, gift_data: Dict) -> Tuple[bool, Dict, str]:
        """
        Process a gift idea to suggest tags and recipients.
        Returns: (success, suggestions, error_message)
        """
        if not self.client or not self.preferences:
            return False, {}, "AI processing is not configured"
        
        try:
            # Get all recipients with their details
            recipients = Recipient.objects.filter(user=self.user).values(
                'id', 'name', 'relationship', 'birth_date', 'notes'
            )
            
            # Format dates and prepare recipient data
            formatted_recipients = []
            for recipient in recipients:
                recipient_data = dict(recipient)
                # Convert date to string format
                if recipient_data['birth_date']:
                    recipient_data['birth_date'] = recipient_data['birth_date'].strftime('%Y-%m-%d')
                # Get interests
                recipient_data['interests'] = list(
                    Recipient.objects.get(id=recipient_data['id'])
                    .interests.values_list('name', flat=True)
                )
                formatted_recipients.append(recipient_data)
            
            # Get all available tags
            available_tags = list(Tag.objects.values_list('name', flat=True))
            
            # Prepare the system message
            system_message = {
                "role": "system",
                "content": f"""You are a gift advisor AI. Analyze the gift and suggest appropriate tags and recipients.
                Rules:
                1. Suggest up to 10 most relevant tags from: {available_tags}
                2. Suggest up to 10 most suitable recipients based on their profiles
                3. Keep gift titles concise and clear
                4. Format descriptions to be clear and well-structured
                5. IMPORTANT: Return ONLY raw JSON without any markdown code blocks or backticks.
                
                Required JSON structure:
                {{
                    "title": "simplified title",
                    "description": "formatted description",
                    "tags": ["tag1", "tag2"],
                    "recipients": [recipient_id1, recipient_id2],
                    "reasoning": "brief explanation of choices"
                }}
                
                Available recipients:
                {json.dumps(formatted_recipients, indent=2)}"""
            }
            
            # Prepare the user message
            user_message = {
                "role": "user",
                "content": f"""Return raw JSON only, no code blocks. Analyze this gift:
                Title: {gift_data.get('title')}
                Description: {gift_data.get('description')}
                Price: ${gift_data.get('price')}
                URL: {gift_data.get('url')}"""
            }
            
            # Get model name based on provider
            model = None
            if self.preferences.current_ai_model == 'openai':
                model = self.preferences.openai_model
            else:
                model = self.preferences.deepseek_model
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=model,
                messages=[system_message, user_message],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            # Parse the response
            try:
                content = response.choices[0].message.content.strip()
                # Remove any potential markdown or code block indicators
                content = content.replace('```json', '').replace('```', '').strip()
                suggestions = json.loads(content)
                return True, suggestions, ""
            except json.JSONDecodeError as e:
                print("Failed to parse response:", content)  # Debug log
                return False, {}, f"Failed to parse AI response: {str(e)}"
                
        except Exception as e:
            return False, {}, f"AI processing failed: {str(e)}" 