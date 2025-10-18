// static/js/main.js - Main JavaScript for MYFI

// ==================== AUTH MODAL ====================
let isLoginMode = false;

function openAuthModal() {
  document.getElementById('authModal').style.display = 'flex';
  updateAuthForm();
}

function closeAuthModal() {
  document.getElementById('authModal').style.display = 'none';
}

function updateAuthForm() {
  const title = document.getElementById('authTitle');
  const submitBtn = document.getElementById('authSubmit');
  const mpesaInput = document.getElementById('mpesaInput');
  const toggleText = document.getElementById('toggleText');
  
  if (isLoginMode) {
    title.textContent = 'Login';
    submitBtn.textContent = 'Login';
    mpesaInput.style.display = 'none';
    mpesaInput.required = false;
    toggleText.innerHTML = 'Don\'t have an account? <a onclick="toggleAuthMode()">Sign Up</a>';
  } else {
    title.textContent = 'Sign Up';
    submitBtn.textContent = 'Sign Up';
    mpesaInput.style.display = 'block';
    mpesaInput.required = true;
    toggleText.innerHTML = 'Already have an account? <a onclick="toggleAuthMode()">Login</a>';
  }
}

function toggleAuthMode() {
  isLoginMode = !isLoginMode;
  updateAuthForm();
}

// Handle auth form submission
document.addEventListener('DOMContentLoaded', function() {
  const authForm = document.getElementById('authForm');
  if (authForm) {
    authForm.onsubmit = async (e) => {
      e.preventDefault();
      const form = e.target;
      const endpoint = isLoginMode ? '/api/login' : '/api/signup';

      const body = {
        username: form.username.value.toLowerCase().replace(/\s/g, ''),
        password: form.password.value
      };
      
      if (!isLoginMode) {
        body.mpesa_phone = form.mpesa_phone.value;
      }
      
      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(body)
        });
        
        const data = await res.json();
        
        if (res.ok) {
          window.location.href = '/my-account';
        } else {
          const msgDiv = document.getElementById('authMessage');
          msgDiv.className = 'message error';
          msgDiv.textContent = data.message;
        }
      } catch (error) {
        console.error('Auth error:', error);
        alert('Network error. Please try again.');
      }
    };
  }
});

// ==================== PAYMENT MODAL ====================
function openPaymentModal() {
  document.getElementById('paymentModal').style.display = 'flex';
}

function closePaymentModal() {
  document.getElementById('paymentModal').style.display = 'none';
}

function copyMpesa() {
  const number = document.getElementById('mpesaNumber').textContent;
  navigator.clipboard.writeText(number).then(() => {
    alert('Number copied: ' + number);
  });
}

async function confirmPaymentSent() {
  try {
    const res = await fetch('/api/mark-payment-sent', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'}
    });
    
    const data = await res.json();
    
    if (res.ok) {
      closePaymentModal();
      showPendingNotice();
      alert('✓ Payment marked as sent. Admin will verify soon.');
    } else {
      alert('Error: ' + data.message);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Network error');
  }
}

function showPendingNotice() {
  document.getElementById('pendingNotice').style.display = 'block';
}

function dismissPending() {
  document.getElementById('pendingNotice').style.display = 'none';
}

// ==================== ADMIN DASHBOARD ====================
async function loadDashboard() {
  try {
    const res = await fetch('/admin/api/dashboard');
    const data = await res.json();
    
    // Update stats
    document.getElementById('totalGroups').textContent = data.total_groups || 0;
    document.getElementById('pendingPayments').textContent = data.pending_payments || 0;
    document.getElementById('totalRevenue').textContent = (data.total_revenue || 0).toFixed(2);
    
    // Load pending payments
    loadPendingPayments(data.payments || []);
    
    // Load groups
    loadGroups(data.groups || []);
  } catch (error) {
    console.error('Dashboard load error:', error);
  }
}

function loadPendingPayments(payments) {
  const container = document.getElementById('pendingPaymentsList');
  
  if (!payments || payments.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">✅</div><p>No pending payments</p></div>';
    return;
  }
  
  container.innerHTML = payments.map(p => `
    <div class="payment-item">
      <div class="payment-info">
        <strong>${p.member_name || 'Unknown'}</strong> - ${p.amount} KSH
        <br><small>Group: ${p.group_name || 'N/A'} | Code: ${p.mpesa_code || 'N/A'}</small>
      </div>
      <div class="payment-actions">
        <button class="approve-btn" onclick="verifyPayment(${p.id}, true)">Approve</button>
        <button class="reject-btn" onclick="verifyPayment(${p.id}, false)">Reject</button>
      </div>
    </div>
  `).join('');
}

function loadGroups(groups) {
  const container = document.getElementById('groupsList');
  
  if (!groups || groups.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📦</div><p>No groups yet</p></div>';
    return;
  }
  
  container.innerHTML = groups.map(g => `
    <div class="group-item">
      <div class="group-name">${g.name || 'Unnamed'}
        <span class="badge badge-${g.status || 'pending'}">${(g.status || 'pending').toUpperCase()}</span>
      </div>
      <div class="group-details">
        Code: <strong>${g.group_code || 'N/A'}</strong> | 
        Members: ${g.member_count || 0}/4 | 
        Balance: ${g.current_balance || 0} / ${g.target_amount || 0} KSH
      </div>
    </div>
  `).join('');
}

async function verifyPayment(paymentId, approve) {
  try {
    const res = await fetch('/admin/api/verify-payment', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({payment_id: paymentId, approve: approve})
    });
    
    const data = await res.json();
    alert(data.message);
    
    if (res.ok) {
      loadDashboard(); // Reload
    }
  } catch (error) {
    console.error('Verify payment error:', error);
    alert('Error verifying payment');
  }
}

async function runExpiry() {
  if (!confirm('Check and expire old groups?')) return;
  
  try {
    const res = await fetch('/admin/api/expire-groups', {method: 'POST'});
    const data = await res.json();
    alert(data.message);
    loadDashboard(); // Reload
  } catch (error) {
    console.error('Expiry error:', error);
    alert('Error running expiry check');
  }
}

async function logout() {
  try {
    const res = await fetch('/admin/api/logout', {method: 'POST'});
    if (res.ok) {
      window.location.href = '/admin';
    }
  } catch (error) {
    console.error('Logout error:', error);
    window.location.href = '/admin';
  }
}

// Load dashboard if on admin page
if (window.location.pathname.includes('/admin/dashboard')) {
  document.addEventListener('DOMContentLoaded', loadDashboard);
}

// Close modals when clicking outside
window.onclick = function(event) {
  const authModal = document.getElementById('authModal');
  const paymentModal = document.getElementById('paymentModal');
  
  if (event.target == authModal) {
    closeAuthModal();
  }
  if (event.target == paymentModal) {
    closePaymentModal();
  }
}
