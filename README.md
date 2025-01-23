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
- A Google Cloud Platform account for OAuth

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
