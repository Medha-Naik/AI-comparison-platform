document.addEventListener('DOMContentLoaded', () => {
  const emailEl = document.getElementById('loginEmail');
  const passEl = document.getElementById('loginPassword');
  const loginBtn = document.getElementById('loginBtn');
  const registerBtn = document.getElementById('registerBtn');

  // Get the next URL parameter for redirect after login
  const urlParams = new URLSearchParams(window.location.search);
  const nextUrl = urlParams.get('next') || '/wishlist';

  async function doAuth(path) {
    const email = (emailEl.value || '').trim();
    const password = passEl.value || '';
    if (!email || !password) { alert('Enter email and password'); return; }
    const res = await fetch(`/auth/${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.success) {
      // Redirect to next URL or wishlist
      window.location.href = nextUrl;
    } else {
      alert(data.message || 'Authentication failed');
    }
  }

  loginBtn.addEventListener('click', () => doAuth('login'));
  registerBtn.addEventListener('click', () => doAuth('register'));
});



