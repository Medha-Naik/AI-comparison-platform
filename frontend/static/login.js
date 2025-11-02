document.addEventListener('DOMContentLoaded', () => {
  const emailEl = document.getElementById('loginEmail');
  const passEl = document.getElementById('loginPassword');
  const nameEl = document.getElementById('registerName');
  const loginBtn = document.getElementById('loginBtn');
  const registerBtn = document.getElementById('registerBtn');
  const pageTitle = document.getElementById('pageTitle');
  const pageSubtitle = document.getElementById('pageSubtitle');
  const nameGroup = document.getElementById('nameGroup');
  const googleOAuthDiv = document.getElementById('googleOAuthDiv');
  const googleOAuthBtn = document.getElementById('googleOAuthBtn');
  
  // Handle Google OAuth button click with error handling
  if (googleOAuthBtn) {
    googleOAuthBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      
      try {
        // Check if OAuth is configured before redirecting
        const res = await fetch('/auth/config');
        const data = await res.json();
        
        if (!data.google_oauth_enabled) {
          showError('Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables. See GOOGLE_OAUTH_SETUP.md for instructions.');
          return;
        }
        
        // OAuth is configured, proceed with redirect
        window.location.href = '/auth/google';
      } catch (error) {
        // If config endpoint fails, try anyway - backend will handle error
        window.location.href = '/auth/google';
      }
    });
  }

  // Get the next URL parameter for redirect after login
  const urlParams = new URLSearchParams(window.location.search);
  const nextUrl = urlParams.get('next') || '/wishlist';
  const prefilledEmail = urlParams.get('email');
  const mode = urlParams.get('mode'); // 'signup' or 'login'

  // Pre-fill email if provided in URL
  if (prefilledEmail) {
    emailEl.value = decodeURIComponent(prefilledEmail);
  }

  // Switch to signup mode if specified
  if (mode === 'signup') {
    switchToSignupMode();
  }

  // Login function
  async function doLogin() {
    const email = (emailEl.value || '').trim();
    const password = passEl.value || '';
    
    if (!email || !password) { 
      showError('Please enter email and password'); 
      return; 
    }
    
    loginBtn.disabled = true;
    loginBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Logging in...';
    
    try {
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await res.json();
      
      if (data.success) {
        showSuccess('Login successful! Redirecting...');
        setTimeout(() => {
          window.location.href = nextUrl;
        }, 500);
      } else {
        // Check if user doesn't exist
        if (data.error_type === 'user_not_found') {
          showError(data.message);
          setTimeout(() => {
            // Switch to signup mode with email pre-filled
            switchToSignupMode(email);
          }, 2000);
        } else if (data.error_type === 'wrong_password') {
          showError(data.message);
        } else {
          showError(data.message || 'Login failed');
        }
      }
    } catch (error) {
      showError('Network error. Please try again.');
    } finally {
      loginBtn.disabled = false;
      loginBtn.innerHTML = 'Login';
    }
  }

  // Register function
  async function doRegister() {
    const email = (emailEl.value || '').trim();
    const password = passEl.value || '';
    const name = (nameEl.value || '').trim();
    
    if (!email || !password) { 
      showError('Please enter email and password'); 
      return; 
    }
    
    if (password.length < 6) {
      showError('Password must be at least 6 characters');
      return;
    }
    
    registerBtn.disabled = true;
    registerBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating account...';
    
    try {
      const res = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name })
      });
      
      const data = await res.json();
      
      if (data.success) {
        showSuccess('Account created! Redirecting...');
        setTimeout(() => {
          window.location.href = nextUrl;
        }, 500);
      } else {
        if (data.message.includes('already registered')) {
          showError(data.message + ' Please login instead.');
          setTimeout(() => {
            switchToLoginMode(email);
          }, 2000);
        } else {
          showError(data.message || 'Registration failed');
        }
      }
    } catch (error) {
      showError('Network error. Please try again.');
    } finally {
      registerBtn.disabled = false;
      registerBtn.innerHTML = 'Create account';
    }
  }

  // Switch to signup mode
  function switchToSignupMode(email) {
    pageTitle.textContent = 'Create Account';
    pageSubtitle.textContent = 'No account found. Please create one to continue.';
    pageSubtitle.style.display = 'block';
    nameGroup.style.display = 'block';
    loginBtn.style.display = 'none';
    registerBtn.textContent = 'Create Account';
    registerBtn.classList.remove('btn-secondary');
    registerBtn.classList.add('btn-primary');
    
    if (email) {
      emailEl.value = email;
    }
    
    // Update URL
    const newUrl = new URL(window.location);
    newUrl.searchParams.set('mode', 'signup');
    if (email) {
      newUrl.searchParams.set('email', email);
    }
    window.history.pushState({}, '', newUrl);
  }

  // Switch to login mode
  function switchToLoginMode(email) {
    pageTitle.textContent = 'Sign in';
    pageSubtitle.style.display = 'none';
    nameGroup.style.display = 'none';
    loginBtn.style.display = 'inline-block';
    registerBtn.textContent = 'Create account';
    registerBtn.classList.remove('btn-primary');
    registerBtn.classList.add('btn-secondary');
    
    if (email) {
      emailEl.value = email;
    }
    
    // Update URL
    const newUrl = new URL(window.location);
    newUrl.searchParams.delete('mode');
    if (email) {
      newUrl.searchParams.set('email', email);
    }
    window.history.pushState({}, '', newUrl);
  }

  // Show error message
  function showError(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #f44336;
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      z-index: 1001;
      font-weight: 500;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 4000);
  }

  // Show success message
  function showSuccess(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #4caf50;
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      z-index: 1001;
      font-weight: 500;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 3000);
  }

  // Event listeners
  loginBtn.addEventListener('click', doLogin);
  registerBtn.addEventListener('click', () => {
    if (nameGroup.style.display === 'none') {
      // Switch to signup mode
      switchToSignupMode(emailEl.value);
    } else {
      // Already in signup mode, do register
      doRegister();
    }
  });

  // Enter key handling
  emailEl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') passEl.focus();
  });
  
  passEl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      if (nameGroup.style.display !== 'none') {
        nameEl.focus();
      } else {
        doLogin();
      }
    }
  });
  
  nameEl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') doRegister();
  });
});