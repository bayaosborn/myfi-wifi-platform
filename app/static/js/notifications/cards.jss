// Notification Cards - In-app sliding notifications (WITH DEBUG)

class NotificationCard {
    constructor() {
        console.log('🔧 [NotificationCards] Initializing...');
        this.container = document.getElementById('notificationCardsContainer');
        
        if (!this.container) {
            console.error('❌ [NotificationCards] Container not found! Check if user is logged in.');
            return;
        }
        
        console.log('✅ [NotificationCards] Container found:', this.container);
        
        this.activeCards = new Set();
        this.maxCards = 3;
        this.socket = null;
        this.init();
    }
    
    init() {
        console.log('🔧 [NotificationCards] Connecting to socket...');
        
        this.socket = io({
            transports: ['websocket', 'polling']
        });
        
        this.socket.on('connect', () => {
            console.log('✅ [NotificationCards] Socket connected! Socket ID:', this.socket.id);
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('❌ [NotificationCards] Socket connection error:', error);
        });
        
        this.socket.on('disconnect', (reason) => {
            console.warn('⚠️ [NotificationCards] Socket disconnected:', reason);
        });
        
        this.socket.on('new_notification', (data) => {
            console.log('🔔 [NotificationCards] New notification received:', data);
            this.show(data);
        });
        
        // Test notification on load (for debugging)
        console.log('🔧 [NotificationCards] Sending test notification in 3 seconds...');
        setTimeout(() => {
            console.log('🧪 [NotificationCards] Triggering test notification');
            this.show({
                title: 'Test Notification',
                message: 'If you see this, the notification system is working!',
                category: 'system',
                priority: 'low'
            });
        }, 3000);
    }
    
    show(notificationData) {
        console.log('📥 [NotificationCards] show() called with:', notificationData);
        
        if (this.activeCards.size >= this.maxCards) {
            console.warn('⚠️ [NotificationCards] Max cards reached, skipping...');
            return;
        }
        
        try {
            const card = this.createCard(notificationData);
            console.log('✅ [NotificationCards] Card created:', card);
            
            this.container.appendChild(card);
            this.activeCards.add(card);
            console.log('✅ [NotificationCards] Card added to DOM. Active cards:', this.activeCards.size);
            
            setTimeout(() => {
                card.classList.add('show');
                console.log('✅ [NotificationCards] Card animated in');
            }, 10);
            
            const autoDismissTimer = setTimeout(() => {
                console.log('⏰ [NotificationCards] Auto-dismissing card');
                this.dismiss(card);
            }, 15000);
            
            card.dataset.timer = autoDismissTimer;
        } catch (error) {
            console.error('❌ [NotificationCards] Error showing card:', error);
        }
    }
    
    createCard(data) {
        console.log('🏗️ [NotificationCards] Creating card element...');
        
        const card = document.createElement('div');
        card.className = `notification-card ${data.priority || 'medium'}`;
        
        const icon = this.getCategoryIcon(data.category);
        const color = this.getCategoryColor(data.category);
        
        card.innerHTML = `
            <div class="notification-card-header" style="background: ${color}">
                <span class="notification-card-icon">${icon}</span>
                <span class="notification-card-category">${data.category || 'notification'}</span>
                <button class="notification-card-close">×</button>
            </div>
            <div class="notification-card-body">
                <div class="notification-card-title">${this.escapeHtml(data.title)}</div>
                <div class="notification-card-message">${this.escapeHtml(data.message)}</div>
                ${data.action_url ? `<a href="${data.action_url}" class="notification-card-action">View Details →</a>` : ''}
            </div>
            <div class="notification-card-progress">
                <div class="notification-card-progress-bar"></div>
            </div>
        `;
        
        // Close button
        const closeBtn = card.querySelector('.notification-card-close');
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            console.log('🗙 [NotificationCards] Close button clicked');
            this.dismiss(card);
        });
        
        this.addSwipeGesture(card);
        
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('notification-card-action')) {
                console.log('👆 [NotificationCards] Card clicked, dismissing');
                this.dismiss(card);
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
            console.log('👆 [NotificationCards] Touch start');
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
            console.log('👆 [NotificationCards] Touch end, diff:', diff);
            
            if (diff > 100) {
                console.log('💨 [NotificationCards] Swiped away');
                card.style.transform = 'translateX(400px)';
                card.style.opacity = '0';
                setTimeout(() => this.dismiss(card), 300);
            } else {
                card.style.transform = 'translateX(0)';
                card.style.opacity = '1';
            }
        });
    }
    
    dismiss(card) {
        console.log('🗑️ [NotificationCards] Dismissing card');
        
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
            console.log('✅ [NotificationCards] Card removed. Active cards:', this.activeCards.size);
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
    
    getCategoryColor(category) {
        const colors = {
            'system': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'service': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'promo': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            'weather': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            'social': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
        };
        return colors[category] || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize
console.log('🚀 [NotificationCards] Script loaded');
if (document.readyState === 'loading') {
    console.log('⏳ [NotificationCards] Waiting for DOM...');
    document.addEventListener('DOMContentLoaded', () => {
        console.log('✅ [NotificationCards] DOM ready, initializing...');
        window.notificationCards = new NotificationCard();
    });
} else {
    console.log('✅ [NotificationCards] DOM already ready, initializing...');
    window.notificationCards = new NotificationCard();
}