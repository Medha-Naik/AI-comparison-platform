document.addEventListener('DOMContentLoaded', async () => {
  const searchBtn = document.getElementById('searchBtn');
  const searchInput = document.getElementById('searchInput');
  
  // Check authentication
  await checkAuthAndLoadProfile();
  
  // Search functionality
  searchBtn.addEventListener('click', performSearch);
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      performSearch();
    }
  });
  
  function performSearch() {
    const query = searchInput.value.trim();
    if (!query) {
      alert('Please enter a search query');
      return;
    }
    window.location.href = `/results?q=${encodeURIComponent(query)}`;
  }
});

async function checkAuthAndLoadProfile() {
  try {
    const meRes = await fetch('/auth/me');
    const me = await meRes.json();
    
    if (!me.authenticated) {
      // Not logged in, redirect to login
      window.location.href = '/login?next=' + encodeURIComponent('/profile');
      return;
    }
    
    // Load profile data
    document.getElementById('profileName').textContent = me.name || 'User';
    document.getElementById('profileEmail').textContent = me.email || '';
    
    // Load wishlist count
    await loadWishlistCount();
    
  } catch (error) {
    console.error('Error loading profile:', error);
    showNotification('Error loading profile', 'error');
    setTimeout(() => {
      window.location.href = '/login';
    }, 2000);
  }
}

async function loadWishlistCount() {
  try {
    const res = await fetch('/api/wishlist/me');
    const data = await res.json();
    
    if (data.success && data.wishlist) {
      document.getElementById('wishlistCount').textContent = data.wishlist.length;
    } else {
      document.getElementById('wishlistCount').textContent = '0';
    }
  } catch (error) {
    console.error('Error loading wishlist count:', error);
    document.getElementById('wishlistCount').textContent = '0';
  }
}

async function handleLogout() {
  try {
    const res = await fetch('/auth/logout', { method: 'POST' });
    const data = await res.json();
    
    if (data.success) {
      showNotification('Logged out successfully', 'success');
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
    } else {
      showNotification('Logout failed', 'error');
    }
  } catch (error) {
    console.error('Logout error:', error);
    showNotification('Network error', 'error');
  }
}

function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
    color: white;
    padding: 15px 20px;
    border-radius: 8px;
    z-index: 10001;
    font-weight: 500;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    animation: slideIn 0.3s ease;
  `;
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => {
      if (document.body.contains(notification)) {
        document.body.removeChild(notification);
      }
    }, 300);
  }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);
