// Load users and recent notifications on page load
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    loadRecentNotifications();
    setupCharCounters();
    setupTargetToggle();
});

function setupCharCounters() {
    const titleInput = document.getElementById('title');
    const messageInput = document.getElementById('message');
    
    titleInput.addEventListener('input', () => {
        document.getElementById('titleCount').textContent = `${titleInput.value.length}/100`;
    });
    
    messageInput.addEventListener('input', () => {
        document.getElementById('messageCount').textContent = `${messageInput.value.length}/500`;
    });
}

function setupTargetToggle() {
    document.getElementById('target').addEventListener('change', (e) => {
        const userGroup = document.getElementById('userSelectGroup');
        userGroup.style.display = e.target.value === 'single' ? 'block' : 'none';
    });
}

async function loadUsers() {
    try {
        const response = await fetch('/admin/api/users');
        const data = await response.json();
        
        if (data.users) {
            const select = document.getElementById('userId');
            select.innerHTML = '<option value="">Select a user</option>';
            
            data.users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = `${user.username} (ID: ${user.id})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function loadRecentNotifications() {
    try {
        const response = await fetch('/admin/api/notifications/all');
        const data = await response.json();
        
        const container = document.getElementById('recentNotifications');
        
        if (data.notifications && data.notifications.length > 0) {
            container.innerHTML = '';
            data.notifications.slice(0, 20).forEach(notif => {
                const div = document.createElement('div');
                div.className = 'notification-item';
                div.innerHTML = `
                    <div class="notification-header">
                        <span class="notification-meta">
                            <span>${getCategoryIcon(notif.category)} ${notif.category}</span>
                            <span>•</span>
                            <span>${formatTime(notif.created_at)}</span>
                        </span>
                    </div>
                    <div class="notification-title">${notif.title}</div>
                    <div class="notification-message">${notif.message}</div>
                `;
                container.appendChild(div);
            });
        } else {
            container.innerHTML = '<div class="loading">No notifications sent yet</div>';
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
        document.getElementById('recentNotifications').innerHTML = '<div class="loading">Error loading notifications</div>';
    }
}

function getCategoryIcon(category) {
    const icons = {
        'system': '🔧',
        'service': '📡',
        'promo': '🎁',
        'weather': '☁️',
        'social': '👥'
    };
    return icons[category] || '🔔';
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 60000);
    
    if (diff < 1) return 'Just now';
    if (diff < 60) return `${diff} min ago`;
    if (diff < 1440) return `${Math.floor(diff / 60)} hours ago`;
    return date.toLocaleDateString();
}

// Preview notification
document.getElementById('previewBtn').addEventListener('click', () => {
    const title = document.getElementById('title').value.trim();
    const message = document.getElementById('message').value.trim();
    const category = document.getElementById('category').value;
    
    if (!title || !message) {
        alert('Please fill in title and message');
        return;
    }
    
    const preview = document.getElementById('preview');
    document.getElementById('previewIcon').textContent = getCategoryIcon(category);
    document.getElementById('previewTitle').textContent = title;
    document.getElementById('previewMessage').textContent = message;
    preview.style.display = 'block';
});

// Send notification
document.getElementById('sendBtn').addEventListener('click', async () => {
    const target = document.getElementById('target').value;
    const userId = document.getElementById('userId').value;
    const category = document.getElementById('category').value;
    const priority = document.getElementById('priority').value;
    const title = document.getElementById('title').value.trim();
    const message = document.getElementById('message').value.trim();
    
    if (!title || !message) {
        showStatus('Please fill in title and message', 'error');
        return;
    }
    
    if (target === 'single' && !userId) {
        showStatus('Please select a user', 'error');
        return;
    }
    
    const payload = {
        target,
        category,
        priority,
        title,
        message
    };
    
    if (target === 'single') {
        payload.user_id = parseInt(userId);
    }
    
    try {
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = true;
        sendBtn.textContent = 'Sending...';
        
        const response = await fetch('/admin/api/notifications/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus(data.message, 'success');
            // Clear form
            document.getElementById('title').value = '';
            document.getElementById('message').value = '';
            document.getElementById('preview').style.display = 'none';
            document.getElementById('titleCount').textContent = '0/100';
            document.getElementById('messageCount').textContent = '0/500';
            // Reload recent notifications
            loadRecentNotifications();
        } else {
            showStatus(data.message || 'Failed to send notification', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showStatus('Error sending notification', 'error');
    } finally {
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send Notification';
    }
});

function showStatus(message, type) {
    const statusMsg = document.getElementById('statusMessage');
    statusMsg.textContent = message;
    statusMsg.className = `status-message ${type}`;
    statusMsg.style.display = 'block';
    
    setTimeout(() => {
        statusMsg.style.display = 'none';
    }, 5000);
}

// Quick templates
function useTemplate(type) {
    const templates = {
        welcome: {
            title: '🎉 Welcome to MyFi!',
            message: 'Thanks for joining MyFi! Get started by connecting to our WiFi network. Enjoy fast, reliable internet.',
            category: 'system',
            priority: 'low'
        },
        maintenance: {
            title: '🔧 Scheduled Maintenance',
            message: 'Our network will undergo maintenance from 2 AM to 4 AM tonight. We apologize for any inconvenience.',
            category: 'service',
            priority: 'high'
        },
        promo: {
            title: '🎁 Special Offer - 50% Off!',
            message: 'Get 50% off on your next top-up! Use code MYFI50 at checkout. Offer valid until end of month.',
            category: 'promo',
            priority: 'medium'
        },
        weather: {
            title: '☁️ Weather Alert',
            message: 'Heavy rain expected in your area. Network performance may be affected. Stay safe!',
            category: 'weather',
            priority: 'medium'
        }
    };
    
    const template = templates[type];
    if (template) {
        document.getElementById('title').value = template.title;
        document.getElementById('message').value = template.message;
        document.getElementById('category').value = template.category;
        document.getElementById('priority').value = template.priority;
        document.getElementById('titleCount').textContent = `${template.title.length}/100`;
        document.getElementById('messageCount').textContent = `${template.message.length}/500`;
    }
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        fetch('/admin/api/logout', { method: 'POST' })
            .then(() => window.location.href = '/admin');
    }
}