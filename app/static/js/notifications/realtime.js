// Notification Cards with Polling + DEBUG

console.log('🚀 [Cards] Script loaded at', new Date().toISOString());

class NotificationCards {
    constructor() {
        console.log('🔧 [Cards] Constructor called');
        
        this.container = document.getElementById('notificationCardsContainer');
        console.log('🔧 [Cards] Looking for container...');
        console.log('🔧 [Cards] Container element:', this.container);
        
        if (!this.container) {
            console.error('❌ [Cards] Container not found! Check if element exists in HTML');
            console.error('❌ [Cards] Available elements:', document.body.innerHTML.substring(0, 500));
            return;
        }
        
        console.log('✅ [Cards] Container found:', this.container);
        console.log('✅ [Cards] Container position:', this.container.getBoundingClientRect());
        
        this.activeCards = new Set();
        this.maxCards = 3;
        this.lastNotificationId = 0;
        this.pollingInterval = null;
        
        console.log('🔧 [Cards] Calling init()...');
        this.init();
    }
    
    async init() {
        console.log('🔧 [Cards] Init started');
        
        try {
            // Get current user
            console.log('🔧 [Cards] Fetching /api/whoami...');
            const response = await fetch('/api/whoami');
            console.log('🔧 [Cards] Response status:', response.status);
            
            if (!response.ok) {
                console.error('❌ [Cards] /api/whoami failed with status:', response.status);
                console.error('❌ [Cards] Did you add the /api/whoami endpoint to Flask?');
                return;
            }
            
            const data = await response.json();
            console.log('🔧 [Cards] User data:', data);
            
            if (!data.user_id) {
                console.warn('⚠️ [Cards] No user_id in response');
                return;
            }
            
            this.userId = data.user_id;
            console.log('✅ [Cards] User ID:', this.userId);
            
            // Get latest notification ID
            console.log('🔧 [Cards] Getting last notification ID...');
            await this.getLastNotificationId();
            
            // Start polling immediately
            console.log('🔧 [Cards] Starting polling...');
            this.startPolling();
            
        } catch (error) {
            console.error('❌ [Cards] Init error:', error);
            console.error('❌ [Cards] Error stack:', error.stack);
        }
    }
    
    async getLastNotificationId() {
        try {
            console.log('🔧 [Cards] Fetching /api/notifications...');
            const response = await fetch('/api/notifications');
            const data = await response.json();
            
            console.log('🔧 [Cards] Notifications response:', data);
            
            if (data.success && data.notifications && data.notifications.length > 0) {
                this.lastNotificationId = data.notifications[0].id;
                console.log('📌 [Cards] Last notification ID set to:', this.lastNotificationId);
            } else {
                console.log('📌 [Cards] No existing notifications, starting from 0');
            }
        } catch (error) {
            console.error('❌ [Cards] Failed to get last ID:', error);
        }
    }
    
    startPolling() {
        console.log('🔄 [Cards] Starting polling (5 seconds)');
        console.log('🔄 [Cards] Polling will check every 5 seconds for notifications with ID >', this.lastNotificationId);
        
        // Check immediately
        console.log('🔍 [Cards] First poll (immediate)...');
        this.checkForNewNotifications();
        
        // Then check every 5 seconds
        this.pollingInterval = setInterval(() => {
            console.log('🔍 [Cards] Polling check at', new Date().toISOString());
            this.checkForNewNotifications();
        }, 5000);
    }
    
    async checkForNewNotifications() {
        try {
            const response = await fetch('/api/notifications');
            const data = await response.json();
            
            console.log('🔍 [Cards] Poll result:', {
                success: data.success,
                count: data.notifications ? data.notifications.length : 0,
                lastSeenId: this.lastNotificationId
            });
            
            if (!data.success || !data.notifications) {
                console.log('⚠️ [Cards] No notifications in response');
                return;
            }
            
            // Find new notifications
            const newNotifications = data.notifications.filter(
                n => n.id > this.lastNotificationId
            );
            
            console.log('🔍 [Cards] New notifications:', newNotifications);
            
            if (newNotifications.length > 0) {
                console.log(`🔔 [Cards] Found ${newNotifications.length} new notifications!`);
                console.log('🔔 [Cards] New notification IDs:', newNotifications.map(n => n.id));
                
                // Show cards for new notifications
                newNotifications.reverse().forEach((notification, index) => {
                    console.log(`🔥 [Cards] Processing notification ${index + 1}/${newNotifications.length}`);
                    this.showCard(notification);
                });
                
                // Update last seen ID
                this.lastNotificationId = data.notifications[0].id;
                console.log('📌 [Cards] Updated last seen ID to:', this.lastNotificationId);
            } else {
                console.log('ℹ️ [Cards] No new notifications (all IDs <= ' + this.lastNotificationId + ')');
            }
            
        } catch (error) {
            console.error('❌ [Cards] Polling error:', error);
        }
    }
    
    showCard(data) {
        console.log('🔥 [Cards] showCard() called');
        console.log('🔥 [Cards] Data:', data);
        console.log('🔥 [Cards] Active cards:', this.activeCards.size, '/', this.maxCards);
        
        if (this.activeCards.size >= this.maxCards) {
            console.warn('⚠️ [Cards] Max cards reached, skipping');
            return;
        }
        
        console.log('🔧 [Cards] Creating card element...');
        const card = this.createCard(data);
        console.log('✅ [Cards] Card created:', card);
        
        console.log('🔧 [Cards] Appending card to container...');
        this.container.appendChild(card);
        this.activeCards.add(card);
        console.log('✅ [Cards] Card appended. Container children:', this.container.children.length);
        
        // Animate in
        setTimeout(() => {
            console.log('🎬 [Cards] Adding show class to card');
            card.classList.add('show');
        }, 100);
        
        // Auto-dismiss after 15 seconds
        const timer = setTimeout(() => {
            console.log('⏰ [Cards] Auto-dismissing card after 15s');
            this.dismissCard(card);
        }, 15000);
        
        card.dataset.timer = timer;
        console.log('✅ [Cards] Card fully initialized');
    }
    
    createCard(data) {
        console.log('🛠️ [Cards] Creating card HTML...');
        
        const card = document.createElement('div');
        card.className = `notification-card ${data.priority || 'medium'}`;

        // ADD THIS INLINE STYLE FOR TESTING
    card.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        width: 360px;
        background: #3B82F6;
        border-radius: 16px;
        padding: 20px;
        color: white;
        z-index: 99999;
        box-shadow: 0 10px 40px rgba(59, 130, 246, 0.5);
    `;
        
        const icon = this.getCategoryIcon(data.category);
        console.log('🛠️ [Cards] Icon:', icon, 'Category:', data.category);
        
        card.innerHTML = `
            <div class="notification-card-header">
                <span class="notification-card-icon">${icon}</span>
                <span class="notification-card-category">${data.category || 'notification'}</span>
                <button class="notification-card-close">×</button>
            </div>
            <div class="notification-card-body">
                <div class="notification-card-title">${this.escapeHtml(data.title)}</div>
                <div class="notification-card-message">${this.escapeHtml(data.message)}</div>
                ${data.action_url ? `<a href="${data.action_url}" class="notification-card-action">View →</a>` : ''}
            </div>
        `;
        
        console.log('✅ [Cards] Card HTML created');
        
        // Close button
        card.querySelector('.notification-card-close').addEventListener('click', (e) => {
            e.stopPropagation();
            console.log('🗙 [Cards] Close button clicked');
            this.dismissCard(card);
        });
        
        // Swipe gesture
        this.addSwipeGesture(card);
        
        // Click to dismiss
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('notification-card-action')) {
                console.log('👆 [Cards] Card clicked, dismissing');
                this.dismissCard(card);
            }
        });
        
        return card;
    }
    
    addSwipeGesture(card) {
        let startX = 0;
        let currentX = 0;
        let isDragging = false;
        
        card.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
            console.log('👆 [Cards] Touch start at', startX);
        });
        
        card.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            currentX = e.touches[0].clientX;
            const diff = currentX - startX;
            
            if (diff > 0) {
                card.style.transform = `translateX(${diff}px)`;
                card.style.opacity = 1 - (diff / 300);
            }
        });
        
        card.addEventListener('touchend', () => {
            if (!isDragging) return;
            isDragging = false;
            
            const diff = currentX - startX;
            console.log('👆 [Cards] Touch end, swipe distance:', diff);
            
            if (diff > 100) {
                console.log('💨 [Cards] Swipe threshold reached, dismissing');
                card.style.transform = 'translateX(400px)';
                card.style.opacity = '0';
                setTimeout(() => this.dismissCard(card), 300);
            } else {
                console.log('↩️ [Cards] Swipe too short, snapping back');
                card.style.transform = 'translateX(0)';
                card.style.opacity = '1';
            }
        });
    }
    
    dismissCard(card) {
        console.log('🗑️ [Cards] Dismissing card');
        
        if (card.dataset.timer) {
            clearTimeout(parseInt(card.dataset.timer));
        }
        
        card.classList.remove('show');
        card.classList.add('hide');
        
        setTimeout(() => {
            if (card.parentNode) {
                card.parentNode.removeChild(card);
            }
            this.activeCards.delete(card);
            console.log('✅ [Cards] Card removed. Active cards:', this.activeCards.size);
        }, 300);
    }
    
    getCategoryIcon(category) {
        const icons = {
            'system': '⚙️',
            'service': '📡',
            'promo': '🎁',
            'weather': '☁️',
            'social': '👥'
        };
        return icons[category] || '🔔';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    destroy() {
        console.log('🛑 [Cards] Destroying polling');
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
    }
}

// Initialize
console.log('🔧 [Cards] Checking DOM ready state:', document.readyState);

if (document.readyState === 'loading') {
    console.log('⏳ [Cards] DOM not ready, waiting...');
    document.addEventListener('DOMContentLoaded', () => {
        console.log('✅ [Cards] DOM ready, initializing...');
        window.notificationCards = new NotificationCards();
    });
} else {
    console.log('✅ [Cards] DOM already ready, initializing immediately...');
    window.notificationCards = new NotificationCards();
}

window.addEventListener('beforeunload', () => {
    console.log('👋 [Cards] Page unloading, cleanup...');
    if (window.notificationCards) {
        window.notificationCards.destroy();
    }
});

console.log('✅ [Cards] Script initialization complete');