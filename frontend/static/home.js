document.addEventListener("DOMContentLoaded", () => {
  const searchBtn = document.getElementById("searchBtn");
  const searchInput = document.getElementById("searchInput");
  const wishlistLink = document.getElementById("wishlistLink");
  const profileIcon = document.getElementById("profileIcon");
  
  // Handle search button click
  searchBtn.addEventListener("click", performSearch);
  
  // Handle Enter key press
  searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      performSearch();
    }
  });
  
  // Handle wishlist icon click with authentication check
  wishlistLink.addEventListener("click", async (e) => {
    e.preventDefault();
    
    try {
      const meRes = await fetch('/auth/me');
      const me = await meRes.json();
      
      if (me.authenticated) {
        // User is logged in, go to wishlist
        window.location.href = '/wishlist';
      } else {
        // User is not logged in, go to login page with next parameter
        window.location.href = '/login?next=' + encodeURIComponent('/wishlist');
      }
    } catch (error) {
      console.error('Error checking authentication:', error);
      // On error, redirect to login
      window.location.href = '/login';
    }
  });
  
  // Handle profile icon click - go to profile page
  profileIcon.addEventListener("click", async (e) => {
    e.preventDefault();
    
    try {
      const meRes = await fetch('/auth/me');
      const me = await meRes.json();
      
      if (me.authenticated) {
        // User is logged in, go to profile page
        window.location.href = '/profile';
      } else {
        // User is not logged in, go to login page with next parameter
        window.location.href = '/login?next=' + encodeURIComponent('/profile');
      }
    } catch (error) {
      console.error('Error checking authentication:', error);
      // On error, redirect to login
      window.location.href = '/login';
    }
  });
  
  function performSearch() {
    const query = searchInput.value.trim();
    
    if (!query) {
      alert("Please enter a search query");
      return;
    }
    
    // Navigate to results page
    window.location.href = `/results?q=${encodeURIComponent(query)}`;
  }
});