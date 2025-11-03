document.addEventListener('DOMContentLoaded', function() {
    const enableBtn = document.getElementById('enable-notifications-btn');
    const statusMessage = document.getElementById('status-message');
    
    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
    }
    
    function urlBase64ToUint8Array(base64String) {
        // Add padding if needed
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }
    
    function getDeviceInfo() {
        const userAgent = navigator.userAgent;
        let deviceType = 'unknown';
        let osType = 'unknown';
        
        if (/mobile/i.test(userAgent)) {
            deviceType = 'phone';
        } else if (/tablet|ipad/i.test(userAgent)) {
            deviceType = 'tablet';
        } else {
            deviceType = 'desktop';
        }
        
        if (/android/i.test(userAgent)) {
            osType = 'android';
        } else if (/iphone|ipad|ipod/i.test(userAgent)) {
            osType = 'ios';
        } else if (/windows/i.test(userAgent)) {
            osType = 'windows';
        } else if (/mac/i.test(userAgent)) {
            osType = 'macos';
        } else if (/linux/i.test(userAgent)) {
            osType = 'linux';
        }
        
        return { deviceType, osType };
    }
    
    function generateDeviceFingerprint() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('myfi', 2, 2);
        const canvasData = canvas.toDataURL();
        
        const fingerprint = {
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            screenResolution: `${screen.width}x${screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            canvas: canvasData.substring(0, 50)
        };
        
        return btoa(JSON.stringify(fingerprint)).substring(0, 64);
    }
    
    async function subscribeUserToPush() {
        try {
            // Check browser support
            if (!('serviceWorker' in navigator)) {
                throw new Error('Service Workers not supported in this browser');
            }
            
            if (!('PushManager' in window)) {
                throw new Error('Push notifications not supported in this browser');
            }
            
            showStatus('Registering service worker...', 'loading');
            console.log('Registering service worker...');
            
            // Register service worker
            const registration = await navigator.serviceWorker.register('/serviceworker.js', {
                scope: '/'
            });
            
            console.log('Service worker registered:', registration);
            
            // Wait for service worker to be ready
            await navigator.serviceWorker.ready;
            
            showStatus('Requesting notification permission...', 'loading');
            console.log('Requesting notification permission...');
            
            // Request notification permission
            const permission = await Notification.requestPermission();
            console.log('Notification permission:', permission);
            
            if (permission !== 'granted') {
                throw new Error('Notification permission denied');
            }
            
            showStatus('Creating push subscription...', 'loading');
            console.log('Creating push subscription...');
            console.log('VAPID Public Key:', VAPID_PUBLIC_KEY);
            
            // Convert VAPID key to Uint8Array
            const applicationServerKey = urlBase64ToUint8Array(VAPID_PUBLIC_KEY);
            console.log('Converted VAPID key:', applicationServerKey);
            
            // Subscribe to push
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: applicationServerKey
            });
            
            console.log('Push subscription created:', subscription);
            
            showStatus('Saving subscription...', 'loading');
            
            const deviceInfo = getDeviceInfo();
            const deviceFingerprint = generateDeviceFingerprint();
            
            // Send subscription to backend
            const response = await fetch('/api/notifications/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...subscription.toJSON(),
                    device_fingerprint: deviceFingerprint,
                    device_info: deviceInfo
                })
            });
            
            const data = await response.json();
            console.log('Server response:', data);
            
            if (data.success) {
                showStatus('Notifications enabled! Redirecting...', 'success');
                setTimeout(() => {
                    window.location.href = '/my-account';
                }, 1500);
            } else {
                throw new Error(data.error || 'Failed to save subscription');
            }
            
        } catch (error) {
            console.error('Error enabling notifications:', error);
            showStatus(error.message || 'Failed to enable notifications', 'error');
            enableBtn.disabled = false;
        }
    }
    
    enableBtn.addEventListener('click', function() {
        enableBtn.disabled = true;
        subscribeUserToPush();
    });
});