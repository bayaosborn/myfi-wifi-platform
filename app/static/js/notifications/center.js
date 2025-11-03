document.addEventListener('DOMContentLoaded', function() {
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    const notificationList = document.getElementById('notification-list');
    
    let lastNotificationId = 0;
    let pollingInterval = null;
    let notificationSound = null;
    
    // Initialize sound
    try {
        notificationSound = new Audio('/static/audio/notification_sound.mp3');
        notificationSound.volume = 0.7;
    } catch (e) {
        console.log('Sound init failed');
    }
    
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        
        return date.toLocaleDateString();
    }
    
    function getCategoryIcon(category) {
        const icons = {
            'weather': '☁️',
            'service': '📡',
            'promo': '🎁',
            'social': '👥',
            'system': '⚙️'
        };
        return icons[category] || '🔔';
    }
    
    function createNotificationElement(notification) {
        const div = document.createElement('div');
        div.className = `notification-item ${notification.is_read ? 'read' : 'unread'}`;
        div.dataset.id = notification.id;
        
        const icon = getCategoryIcon(notification.category);
        
        div.innerHTML = `
            <div class="notification-header">
                <span class="notification-icon">${icon}</span>
                <span class="notification-category ${notification.category}">${notification.category}</span>
            </div>
            <div class="notification-title">${notification.title}</div>
            <div class="notification-message">${notification.message}</div>
            <div class="notification-footer">
                <span class="notification-time">${formatTimestamp(notification.created_at)}</span>
                <div class="notification-actions">
                    ${!notification.is_read ? '<button class="notification-action-btn mark-read">Mark as read</button>' : ''}
                </div>
            </div>
            ${notification.priority === 'high' || notification.priority === 'urgent' ? 
                `<div class="priority-indicator ${notification.priority}"></div>` : ''}
        `;
        
        div.addEventListener('click', function(e) {
            if (!e.target.classList.contains('notification-action-btn')) {
                if (!notification.is_read) {
                    markAsRead(notification.id);
                }
                if (notification.action_url) {
                    window.location.href = notification.action_url;
                }
            }
        });
        
        const markReadBtn = div.querySelector('.mark-read');
        if (markReadBtn) {
            markReadBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                markAsRead(notification.id);
                div.classList.remove('unread');
                div.classList.add('read');
                markReadBtn.remove();
            });
        }
        
        return div;
    }
    
    function markAsRead(notificationId) {
        fetch(`/api/notifications/${notificationId}/read`, {
            method: 'PATCH'
        }).catch(err => {});
    }
    
    function loadNotifications() {
        fetch('/api/notifications')
            .then(response => response.json())
            .then(data => {
                loadingState.style.display = 'none';
                
                if (!data.notifications || data.notifications.length === 0) {
                    emptyState.style.display = 'block';
                    notificationList.style.display = 'none';
                } else {
                    emptyState.style.display = 'none';
                    notificationList.style.display = 'flex';
                    
                    const newNotifications = data.notifications.filter(
                        n => n.id > lastNotificationId
                    );
                    
                    if (newNotifications.length > 0) {
                        // PLAY SOUND
                        if (notificationSound) {
                            notificationSound.currentTime = 0;
                            notificationSound.play().catch(e => {});
                        }
                        
                        newNotifications.reverse().forEach(notification => {
                            const element = createNotificationElement(notification);
                            notificationList.insertBefore(element, notificationList.firstChild);
                        });
                        
                        lastNotificationId = data.notifications[0].id;
                    } else if (lastNotificationId === 0) {
                        notificationList.innerHTML = '';
                        data.notifications.forEach(notification => {
                            const element = createNotificationElement(notification);
                            notificationList.appendChild(element);
                        });
                        
                        if (data.notifications.length > 0) {
                            lastNotificationId = data.notifications[0].id;
                        }
                    }
                }
            })
            .catch(error => {
                loadingState.innerHTML = '<p style="color: #dc2626;">Failed to load notifications</p>';
            });
    }
    
    loadNotifications();
    
    pollingInterval = setInterval(() => {
        loadNotifications();
    }, 5000);
    
    window.addEventListener('beforeunload', () => {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
    });
});
