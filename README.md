# GiftAdvisor 🎁

A smart gift recommendation system that helps you manage and track gift ideas for your loved ones. Never struggle with finding the perfect gift again!

## Features ✨

- Smart gift recommendations based on recipient interests
- Price tracking and budgeting
- Gift purchase history and feedback
- Multiple currency support
- Social login with Google
- AI-powered gift suggestions

## Prerequisites 📋

- Python 3.12+
- Poetry for dependency management
- Google Cloud Platform

## Setup 🚀

1. Install dependencies with Poetry:
```bash
poetry install
```

2. Set up Google OAuth:
   - Go to the [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Enable the Google+ API
   - Go to Credentials > Create Credentials > OAuth Client ID
   - Set up the OAuth consent screen:
     - Add your app name and contact email
     - Add the following scopes: email, profile
   - Create OAuth Client ID:
     - Application type: Web application
     - Name: GiftAdvisor (or your preferred name)
     - Authorized JavaScript origins: `http://127.0.0.1:8000` (for development)
     - Authorized redirect URIs: `http://127.0.0.1:8000/accounts/google/login/callback/`
   - Note down your Client ID and Client Secret

3. Set up environment variables:
Create a `.env` file in the root directory based on the example [`.env.example`](.env.example) file:
```env
DJANGO_SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

4. Run migrations:
```bash
poetry run ./manage.py migrate
```

5. Create a superuser (optional):
```bash
poetry run ./manage.py createsuperuser
```

6. Run the development server:
```bash
poetry run ./manage.py runserver
```


## Usage Guide 🌟

### Managing Recipients 👥
1. Go to [Recipients](http://127.0.0.1:8000/recipients/) and add your loved ones to recipients list
2. Tag their interests (e.g., "TV", "Fishing", "Books")
3. Add personal notes to remember their preferences

### Set up AI Processing 🤖
1. Go to [Preferences](http://127.0.0.1:8000/preferences/) and set up your AI processing preferences
2. Choose your preferred AI provider and model
3. Set up API keys for your AI provider of choice

### Add gift ideas from your favorite stores 🛒
1. Go to [Gift Ideas](http://127.0.0.1:8000/) and add gift ideas from your favorite stores via "Quick Add" feature, by pasting product URL
2. All the info like title, description, price, images will be automatically extracted from the product page
3. Then, your gift ideas will be automatically processed by AI and added to your dashboard! The AI will determine tags and great potential recipients for each gift idea!

### Finding the Perfect Gift 🎯
1. Browse [Recipients](http://127.0.0.1:8000/recipients/) that will already have a list of gift ideas personalized for them!
2. You can also find the perfect gift for your recipient by browsing [Gift Ideas](http://127.0.0.1:8000/), based on price, relationsip
3. When you found a gift idea, you can mark it as "Gifted", and keep track of feedback for every gift you make!
