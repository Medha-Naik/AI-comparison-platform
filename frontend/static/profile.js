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
    
    // Set edit modal values
    document.getElementById('editName').value = me.name || '';
    document.getElementById('editEmail').value = me.email || '';
    
    // Load wishlist count
    await loadWishlistCount();
    
    // Calculate member since (mock data - you can enhance this with actual registration date)
    const memberDate = new Date();
    memberDate.setMonth(memberDate.getMonth() - 3); // Mock: 3 months ago
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    document.getElementById('memberSince').textContent = `${monthNames[memberDate.getMonth()]} ${memberDate.getFullYear()}`;
    
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
    const res = await fetch('/api/wishlist');
    const data = await res.json();
    
    if (data.success) {
      document.getElementById('wishlistCount').textContent = data.items.length;
    }
  } catch (error) {
    console.error('Error loading wishlist count:', error);
    document.getElementById('wishlistCount').textContent = '0';
  }
}

function showEditProfile() {
  const modal = document.getElementById('editModal');
  modal.classList.add('show');
}

function closeEditProfile() {
  const modal = document.getElementById('editModal');
  modal.classList.remove('show');
}

async function saveProfile() {
  const name = document.getElementById('editName').value.trim();
  
  if (!name) {
    showNotification('Please enter a name', 'error');
    return;
  }
  
  try {
    // Note: You'll need to create an endpoint in your Flask app to update user profile
    // For now, this is a placeholder that shows the expected behavior
    const res = await fetch('/auth/update-profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    
    const data = await res.json();
    
    if (data.success) {
      showNotification('Profile updated successfully', 'success');
      document.getElementById('profileName').textContent = name;
      closeEditProfile();
    } else {
      showNotification(data.message || 'Failed to update profile', 'error');
    }
  } catch (error) {
    console.error('Error updating profile:', error);
    showNotification('Network error. Please try again.', 'error');
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

// Close modal when clicking outside
document.getElementById('editModal').addEventListener('click', (e) => {
  if (e.target.id === 'editModal') {
    closeEditProfile();
  }
});