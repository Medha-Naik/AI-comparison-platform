# Google OAuth Setup Instructions

This guide will help you set up Google OAuth for the AI Shopping Assistant.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "AI Shopping Assistant")
5. Click "Create"

## Step 2: Enable Google+ API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google+ API" (or use "Google Identity Services")
3. Click on it and click "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" (unless you have a Google Workspace)
   - Fill in the required fields:
     - App name: "AI Shopping Assistant"
     - User support email: Your email
     - Developer contact: Your email
   - Click "Save and Continue"
   - Add scopes: `email`, `profile`, `openid`
   - Add test users (your email) if app is in testing mode
   - Click "Save and Continue"
4. Configure the OAuth consent screen (if needed)
5. Create OAuth client ID:
   - Application type: "Web application"
   - Name: "AI Shopping Assistant Web Client"
   - Authorized JavaScript origins:
     - Add: `http://127.0.0.1:5000`
     - Add: `http://localhost:5000`
   - Authorized redirect URIs:
     - Add: `http://127.0.0.1:5000/auth/google/callback`
     - Add: `http://localhost:5000/auth/google/callback`
   - Click "Create"
6. Copy your **Client ID** and **Client Secret**

## Step 4: Configure Environment Variables

### Option A: Using .env file (Recommended)

1. Create a `.env` file in the `backend` directory:

```bash
cd backend
touch .env  # On Windows: type nul > .env
```

2. Add these lines to `.env`:

```
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
```

3. Replace `your-client-id-here` and `your-client-secret-here` with the actual values from Step 3.

### Option B: Using Environment Variables (Windows PowerShell)

```powershell
$env:GOOGLE_CLIENT_ID="your-client-id-here.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET="your-client-secret-here"
```

### Option C: Using Environment Variables (Windows CMD)

```cmd
set GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
set GOOGLE_CLIENT_SECRET=your-client-secret-here
```

### Option D: Using Environment Variables (Linux/Mac)

```bash
export GOOGLE_CLIENT_ID="your-client-id-here.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret-here"
```

## Step 5: Restart the Flask Server

After setting the environment variables, restart your Flask server:

```bash
# Stop the current server (Ctrl+C)
# Then start it again
python app.py
```

## Step 6: Test Google OAuth

1. Go to `http://127.0.0.1:5000/login`
2. Click "Continue with Google"
3. You should be redirected to Google's login page
4. After logging in, you'll be redirected back to your app

## Troubleshooting

### Error: "Google OAuth not configured"

- Make sure you've set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- Make sure you restarted the Flask server after setting the variables
- Check the console output when starting the server - it should show:
  - `✅ Google OAuth configured with Client ID: ...`

### Error: "redirect_uri_mismatch"

- Make sure the redirect URI in Google Console exactly matches: `http://127.0.0.1:5000/auth/google/callback`
- Make sure you're accessing the app via `http://127.0.0.1:5000` (not `localhost` or `http://localhost:5000`)

### Error: "Access blocked: This app's request is invalid"

- Make sure you've added yourself as a test user in the OAuth consent screen (if app is in testing mode)
- Make sure you've enabled the Google+ API or Google Identity Services

## Important Notes

- **Security**: Never commit your `.env` file or credentials to version control
- **Production**: For production, use HTTPS and update the redirect URIs accordingly
- **Testing Mode**: Google OAuth apps start in "Testing" mode. Only users you add as test users can log in. To make it public, you need to submit your app for verification (only if you're using sensitive scopes).

