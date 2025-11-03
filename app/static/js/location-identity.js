document.addEventListener('DOMContentLoaded', function() {
    const enableBtn = document.getElementById('enable-location-btn');
    const statusMessage = document.getElementById('status-message');
    
    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
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
        // Simple fingerprint - you should improve this
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


    /*
    enableBtn.addEventListener('click', function() {
        if (!navigator.geolocation) {
            showStatus('Geolocation is not supported by your browser', 'error');
            return;
        }
        
        enableBtn.disabled = true;
        showStatus('Requesting location permission...', 'loading');
        
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const deviceInfo = getDeviceInfo();
                const deviceFingerprint = generateDeviceFingerprint();
                
                showStatus('Saving location...', 'loading');
                
                fetch('/api/location/capture', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        device_fingerprint: deviceFingerprint,
                        device_type: deviceInfo.deviceType,
                        os_type: deviceInfo.osType
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('Location enabled! Redirecting...', 'success');
                        setTimeout(() => {
                            window.location.href = '/my-account';
                        }, 1000);
                    } else {
                        showStatus(data.error || 'Failed to save location', 'error');
                        enableBtn.disabled = false;
                    }
                })
                .catch(error => {
                    showStatus('Error saving location. Please try again.', 'error');
                    enableBtn.disabled = false;
                });
            },
            function(error) {
                let errorMessage = '';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Location permission denied. Please enable location in your settings to use Myfi.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information unavailable. Please check your device settings.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Location request timed out. Please try again.';
                        break;
                    default:
                        errorMessage = 'An error occurred while getting your location.';
                }
                showStatus(errorMessage, 'error');
                enableBtn.disabled = false;
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    });
});
*/
    enableBtn.addEventListener('click', function() {
    if (!navigator.geolocation) {
        showStatus('Geolocation is not supported by your browser', 'error');
        return;
    }
    
    enableBtn.disabled = true;
    showStatus('Requesting location permission...', 'loading');
    
    console.log('Requesting geolocation...'); // ADD THIS
    
    navigator.geolocation.getCurrentPosition(
        function(position) {
            console.log('Location received:', position.coords); // ADD THIS
            
            const deviceInfo = getDeviceInfo();
            const deviceFingerprint = generateDeviceFingerprint();
            
            console.log('Device info:', deviceInfo); // ADD THIS
            console.log('Device fingerprint:', deviceFingerprint); // ADD THIS
            
            showStatus('Saving location...', 'loading');
            
            fetch('/api/location/capture', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    device_fingerprint: deviceFingerprint,
                    device_type: deviceInfo.deviceType,
                    os_type: deviceInfo.osType
                })
            })
            .then(response => {
                console.log('Response status:', response.status); // ADD THIS
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data); // ADD THIS
                
                if (data.success) {
                    showStatus('Location enabled! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.href = '/notifications-setup';
                    }, 1000);
                } else {
                    showStatus(data.error || 'Failed to save location', 'error');
                    enableBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Fetch error:', error); // ADD THIS
                showStatus('Error saving location. Please try again.', 'error');
                enableBtn.disabled = false;
            });
        },
        function(error) {
            console.error('Geolocation error:', error); // ADD THIS
            
            let errorMessage = '';
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage = 'Location permission denied. Please enable location in your settings to use Myfi.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage = 'Location information unavailable. Please check your device settings.';
                    break;
                case error.TIMEOUT:
                    errorMessage = 'Location request timed out. Please try again.';
                    break;
                default:
                    errorMessage = 'An error occurred while getting your location.';
            }
            showStatus(errorMessage, 'error');
            enableBtn.disabled = false;
        },
        {
            enableHighAccuracy: true,
            timeout: 30000,  // INCREASE from 10000 to 30000 (30 seconds)
            maximumAge: 0
        }
    );
});
});