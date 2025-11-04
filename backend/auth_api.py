"""
Simple session-based authentication (register/login/logout/me) + Google OAuth
"""
from flask import Blueprint, request, jsonify, session, redirect, url_for
from models import get_db, User, create_tables
from authlib.integrations.flask_client import OAuth
import requests
import os

auth_bp = Blueprint('auth', __name__)

create_tables()

oauth = OAuth()
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

print(f"🔍 DEBUG - GOOGLE_CLIENT_ID: {GOOGLE_CLIENT_ID[:30] if GOOGLE_CLIENT_ID else 'NOT SET'}...")
print(f"🔍 DEBUG - GOOGLE_CLIENT_SECRET: {'SET' if GOOGLE_CLIENT_SECRET else 'NOT SET'}")

def init_oauth(app):
    oauth.init_app(app)
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        oauth.register(
            name='google',
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        print(f"✅ Google OAuth configured with Client ID: {GOOGLE_CLIENT_ID[:20]}...")
    else:
        print("⚠️  Google OAuth NOT configured - missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET")

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    db = next(get_db())
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password')
        name = data.get('name')
        if not email or not password:
            return jsonify({"success": False, "message": "Email and password required"}), 400
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({"success": False, "message": "Email already registered"}), 400
        user = User(email=email, name=name)
        user.set_password(password)
        db.add(user)
        db.commit()
        session['user_id'] = user.id
        session['user_email'] = user.email
        return jsonify({"success": True, "message": "Registered", "user": {"id": user.id, "email": user.email}})
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 500
    finally:
        db.close()


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    db = next(get_db())
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"success": False, "message": "Email and password required"}), 400
        
        user = db.query(User).filter(User.email == email).first()
        
        # Check if user exists
        if not user:
            return jsonify({
                "success": False,
                "message": "No account found with this email. Please sign up first.",
                "error_type": "user_not_found",
                "redirect": "signup"
            }), 404
        
        # Check password
        if not user.check_password(password):
            return jsonify({
                "success": False, 
                "message": "Invalid password. Please try again.",
                "error_type": "wrong_password"
            }), 401
        
        # Login successful
        session['user_id'] = user.id
        session['user_email'] = user.email
        return jsonify({"success": True, "message": "Logged in", "user": {"id": user.id, "email": user.email}})
    finally:
        db.close()


@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out"})


@auth_bp.route('/auth/me', methods=['GET'])
def me():
    uid = session.get('user_id')
    if not uid:
        return jsonify({"authenticated": False}), 200
    return jsonify({"authenticated": True, "user": {"id": uid, "email": session.get('user_email')}})

@auth_bp.route('/auth/config', methods=['GET'])
def auth_config():
    """Check if Google OAuth is configured"""
    google_oauth_enabled = 'google' in oauth._clients if hasattr(oauth, '_clients') else False
    return jsonify({
        "google_oauth_enabled": google_oauth_enabled
    })


# Google OAuth: start login
@auth_bp.route('/auth/google', methods=['GET'])
def auth_google():
    print("🔥 auth_google() function called!")
    
    if 'google' not in oauth._clients:
        print("❌ Google OAuth not configured")
        from flask import render_template_string
        error_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Google OAuth Not Configured</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                h1 { color: #d32f2f; }
                code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
                pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
                a { color: #1976d2; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>⚠️ Google OAuth Not Configured</h1>
            <p>To enable Google OAuth login, you need to configure your Google OAuth credentials.</p>
            
            <h2>Quick Setup:</h2>
            <ol>
                <li>Create a <code>.env</code> file in the <code>backend</code> directory</li>
                <li>Add these lines:
                    <pre>GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here</pre>
                </li>
                <li>Restart your Flask server</li>
            </ol>
            
            <h2>Detailed Instructions:</h2>
            <p>See <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a> to create OAuth credentials.</p>
            <p>For step-by-step instructions, check <code>GOOGLE_OAUTH_SETUP.md</code> in your project root.</p>
            
            <hr>
            <p><a href="/login">← Back to Login</a> | <a href="/">Go to Home</a></p>
        </body>
        </html>
        """
        return render_template_string(error_html), 500
    
    # Detect if we're on localhost or production
    if request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
        scheme = 'http'
    else:
        scheme = 'https'
    
    redirect_uri = url_for('auth.auth_google_callback', _external=True, _scheme=scheme)
    
    print(f"🔐 Initiating Google OAuth login")
    print(f"📍 Redirect URI: {redirect_uri}")
    print(f"🌐 Request host: {request.host}")
    print(f"🔒 Scheme: {scheme}")
    
    # FORCE ACCOUNT SELECTION: Add prompt=select_account
    return oauth.google.authorize_redirect(
        redirect_uri,
        prompt='select_account'  # This forces Google to show account picker every time
    )


# Google OAuth: callback
@auth_bp.route('/auth/google/callback', methods=['GET'])
def auth_google_callback():
    print(f"🔄 Google OAuth callback received")
    print(f"📦 Request args: {request.args}")
    
    if 'google' not in oauth._clients:
        return jsonify({"success": False, "message": "Google OAuth not configured."}), 500
    
    try:
        token = oauth.google.authorize_access_token()
        print(f"✅ Token received successfully")
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return jsonify({"success": False, "message": f"OAuth error: {str(e)}"}), 400

    # Prefer Google's UserInfo endpoint; fallback to ID token parsing, then direct HTTP
    userinfo = None
    try:
        resp = oauth.google.get('userinfo')
        if resp and hasattr(resp, 'json'):
            userinfo = resp.json()
            print(f"👤 User info (userinfo endpoint): {userinfo.get('email')}")
    except Exception as e:
        print(f"⚠️  userinfo endpoint failed: {e}")

    if not userinfo:
        # Try direct HTTP call using access token
        try:
            access_token = (token or {}).get('access_token')
            if access_token:
                r = requests.get(
                    'https://openidconnect.googleapis.com/v1/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=6
                )
                if r.ok:
                    userinfo = r.json()
                    print(f"👤 User info (direct HTTP): {userinfo.get('email')}")
        except Exception as e:
            print(f"⚠️  direct userinfo HTTP failed: {e}")

    if not userinfo:
        try:
            userinfo = oauth.google.parse_id_token(token)
            print(f"👤 User info (id_token): {userinfo.get('email')}")
        except Exception as e:
            print(f"❌ Error parsing user info: {e}")
            return jsonify({"success": False, "message": "Failed to retrieve user info"}), 400
    
    if not userinfo:
        return jsonify({"success": False, "message": "Failed to retrieve user info"}), 400

    # Check if user exists and redirect accordingly
    db = next(get_db())
    try:
        email = (userinfo.get('email') or '').lower()
        name = userinfo.get('name')
        picture = userinfo.get('picture')

        # Check if user already exists
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # EXISTING USER: Log them in and redirect to wishlist
            print(f"✅ Existing user found: {email} - Logging in")
            session['user_id'] = user.id
            session['user_email'] = user.email
            print(f"🎉 Login successful, redirecting to wishlist")
            return redirect('/wishlist')
        else:
            # NEW USER: Create account and redirect to signup/login page with welcome message
            print(f"📝 New user detected: {email} - Creating account")
            user = User(email=email, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Set session
            session['user_id'] = user.id
            session['user_email'] = user.email
            
            print(f"🆕 New account created, redirecting to login page with welcome message")
            # Redirect to login page (which will show welcome message and redirect to wishlist)
            return redirect('/login?new_google_user=true')
            
    except Exception as e:
        db.rollback()
        import traceback
        print(f"❌ Error in OAuth callback: {traceback.format_exc()}")
        return jsonify({"success": False, "message": f"OAuth callback failed: {str(e)}"}), 500
    finally:
        db.close()


# Trailing-slash tolerant aliases (avoid 404 if provider appends a slash)
@auth_bp.route('/auth/google/', methods=['GET'])
def auth_google_slash():
    return auth_google()


@auth_bp.route('/auth/google/callback/', methods=['GET'])
def auth_google_callback_slash():
    return auth_google_callback()


# Test route (at module level, not inside any function!)
@auth_bp.route('/auth/test', methods=['GET'])
def test_route():
    print("🔥 TEST ROUTE HIT!")
    return "Test route works!"