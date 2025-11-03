document.getElementById('saveBtn').addEventListener('click', async () => {
    const preferences = {
        weather_enabled: document.getElementById('weather_enabled').checked,
        service_enabled: document.getElementById('service_enabled').checked,
        promo_enabled: document.getElementById('promo_enabled').checked,
        system_enabled: document.getElementById('system_enabled').checked
    };
    
    try {
        const response = await fetch('/api/notifications/preferences', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(preferences)
        });
        
        const data = await response.json();
        
        const statusMsg = document.getElementById('statusMessage');
        statusMsg.style.display = 'block';
        
        if (data.success) {
            statusMsg.textContent = '✅ Settings saved!';
            statusMsg.className = 'status-message success';
        } else {
            statusMsg.textContent = '❌ Failed to save';
            statusMsg.className = 'status-message error';
        }
        
        setTimeout(() => {
            statusMsg.style.display = 'none';
        }, 3000);
    } catch (error) {
        console.error('Error:', error);
    }
});