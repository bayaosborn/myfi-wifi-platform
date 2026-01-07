/**
 * PWA Registration and Install Prompt
 * Handles service worker registration and install prompts
 */

let deferredPrompt;
let isInstalled = false;

// Check if app is already installed
if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
  isInstalled = true;
  console.log('✅ PWA: Running as installed app');
}

// Register service worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    registerServiceWorker();
  });
}

async function registerServiceWorker() {
  try {
    const registration = await navigator.serviceWorker.register('/static/service-worker.js', {
      scope: '/'
    });
    
    console.log('✅ Service Worker registered:', registration.scope);
    
    // Check for updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      console.log('🔄 Service Worker: Update found');
      
      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // New service worker available
          showUpdateNotification();
        }
      });
    });
    
    // Check for updates every hour
    setInterval(() => {
      registration.update();
    }, 60 * 60 * 1000);
    
  } catch (error) {
    console.error('❌ Service Worker registration failed:', error);
  }
}

// Listen for install prompt
window.addEventListener('beforeinstallprompt', (e) => {
  console.log('💾 Install prompt available');
  
  // Prevent default browser install prompt
  e.preventDefault();
  
  // Store the event for later use
  deferredPrompt = e;
  
  // Show custom install button
  showInstallPrompt();
});

// Listen for successful install
window.addEventListener('appinstalled', () => {
  console.log('✅ PWA: Installed successfully');
  isInstalled = true;
  hideInstallPrompt();
  
  // Show success message
  showNotification('MyFi installed! Launch from home screen.', 'success');
  
  // Clear the deferred prompt
  deferredPrompt = null;
});

// Show custom install prompt
function showInstallPrompt() {
  // Create install banner
  const banner = document.createElement('div');
  banner.id = 'pwa-install-banner';
  banner.innerHTML = `
    <div style="
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: #0051fe;
      color: white;
      padding: 16px 24px;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      gap: 16px;
      z-index: 9999;
      max-width: 90%;
      animation: slideUp 0.3s ease-out;
    ">
      <div style="flex: 1;">
        <div style="font-weight: 600; margin-bottom: 4px;">📱 Install MyFi</div>
        <div style="font-size: 14px; opacity: 0.9;">Get quick access from your home screen</div>
      </div>
      <button id="pwa-install-btn" style="
        background: white;
        color: #667eea;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        white-space: nowrap;
      ">
        Install
      </button>
      <button id="pwa-dismiss-btn" style="
        background: transparent;
        color: white;
        border: none;
        padding: 10px;
        cursor: pointer;
        font-size: 20px;
      ">
        ✕
      </button>
    </div>
    
    <style>
      @keyframes slideUp {
        from {
          transform: translateX(-50%) translateY(100px);
          opacity: 0;
        }
        to {
          transform: translateX(-50%) translateY(0);
          opacity: 1;
        }
      }
    </style>
  `;
  
  document.body.appendChild(banner);
  
  // Install button click
  document.getElementById('pwa-install-btn').addEventListener('click', async () => {
    if (!deferredPrompt) return;
    
    // Show install prompt
    deferredPrompt.prompt();
    
    // Wait for user choice
    const { outcome } = await deferredPrompt.userChoice;
    console.log('User choice:', outcome);
    
    if (outcome === 'accepted') {
      console.log('✅ User accepted install');
    } else {
      console.log('❌ User dismissed install');
    }
    
    // Clear prompt
    deferredPrompt = null;
    hideInstallPrompt();
  });
  
  // Dismiss button click
  document.getElementById('pwa-dismiss-btn').addEventListener('click', () => {
    hideInstallPrompt();
    
    // Don't show again for 7 days
    localStorage.setItem('pwa-dismissed', Date.now() + (7 * 24 * 60 * 60 * 1000));
  });
  
  // Check if previously dismissed
  const dismissed = localStorage.getItem('pwa-dismissed');
  if (dismissed && Date.now() < parseInt(dismissed)) {
    hideInstallPrompt();
  }
}

function hideInstallPrompt() {
  const banner = document.getElementById('pwa-install-banner');
  if (banner) {
    banner.remove();
  }
}

// Show update notification
function showUpdateNotification() {
  const notification = document.createElement('div');
  notification.innerHTML = `
    <div style="
      position: fixed;
      top: 20px;
      right: 20px;
      background: white;
      color: #333;
      padding: 16px 24px;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.2);
      z-index: 9999;
      max-width: 300px;
    ">
      <div style="font-weight: 600; margin-bottom: 8px;">🔄 Update Available</div>
      <div style="font-size: 14px; margin-bottom: 12px;">A new version of MyFi is ready</div>
      <button id="pwa-reload-btn" style="
        background: #667eea;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
      ">
        Reload Now
      </button>
    </div>
  `;
  
  document.body.appendChild(notification);
  
  document.getElementById('pwa-reload-btn').addEventListener('click', () => {
    // Tell service worker to skip waiting
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
    }
    
    // Reload page
    window.location.reload();
  });
}

// Helper: Show notification
function showNotification(message, type = 'info') {
  console.log(`[${type.toUpperCase()}] ${message}`);
  
  // You can integrate with your existing notification system here
  // For now, just console log
}

// Expose PWA status
window.pwaStatus = {
  isInstalled: () => isInstalled,
  canInstall: () => !!deferredPrompt,
  triggerInstall: () => {
    if (deferredPrompt) {
      document.getElementById('pwa-install-btn')?.click();
    }
  }
};

console.log('📱 PWA: Initialized');