// UI event handlers

document.getElementById('searchBtn').addEventListener('click', searchUser);
document.getElementById('searchInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchUser();
});

document.getElementById('callBtn').addEventListener('click', () => {
    const userId = document.getElementById('callBtn').dataset.userId;
    const username = document.getElementById('foundUsername').textContent;
    initiateCall(userId, username);
});

document.getElementById('hangUpBtn').addEventListener('click', endCall);

document.getElementById('acceptCallBtn').addEventListener('click', acceptCall);
document.getElementById('rejectCallBtn').addEventListener('click', rejectCall);

document.getElementById('muteBtn').addEventListener('click', () => {
    if (localStream) {
        const audioTrack = localStream.getAudioTracks()[0];
        audioTrack.enabled = !audioTrack.enabled;
        document.getElementById('muteBtn').textContent = audioTrack.enabled ? 'Mute' : 'Unmute';
    }
});

document.getElementById('speakerBtn').addEventListener('click', () => {
    // Speaker toggle - this is tricky on mobile, placeholder for now
    alert('Speaker control - implement based on device');
});



/*
async function searchUser() {
    const username = document.getElementById('searchInput').value.trim();
    
    if (!username) {
        alert('Enter a username');
        return;
    }
    
    try {
        const response = await fetch('/api/search-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        
        const data = await response.json();
        
        if (data.found) {
            document.getElementById('foundUsername').textContent = data.user.username;
            document.getElementById('onlineStatus').textContent = data.user.online ? '🟢 Online' : '⚪ Offline';
            document.getElementById('callBtn').dataset.userId = data.user.id;
            document.getElementById('searchResults').style.display = 'block';
        } else {
            alert(data.message || 'User not found');
            document.getElementById('searchResults').style.display = 'none';
        }
    } catch (error) {
        console.error('Search error:', error);
        alert('Error searching user');
    }
}

*/

async function searchUser() {
    const username = document.getElementById('searchInput').value.trim();
    
    if (!username) {
        alert('Enter a username');
        return;
    }
    
    try {
        const response = await fetch('/api/search-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        
        const data = await response.json();
        
        if (data.found) {
            document.getElementById('foundUsername').textContent = data.user.username;
            document.getElementById('onlineStatus').textContent = data.user.online ? '🟢 Online' : '⚪ Offline';
            
            // MAKE SURE IT'S AN INTEGER
            document.getElementById('callBtn').dataset.userId = data.user.id;
            
            console.log('✅ Found user:', data.user.username, 'ID:', data.user.id, 'Type:', typeof data.user.id);
            
            document.getElementById('searchResults').style.display = 'block';
        } else {
            alert(data.message || 'User not found');
            document.getElementById('searchResults').style.display = 'none';
        }
    } catch (error) {
        console.error('Search error:', error);
        alert('Error searching user');
    }
}



// Update the searchUser function to set current user
async function searchUser() {
    const username = document.getElementById('searchInput').value.trim();
    
    if (!username) {
        alert('Enter a username');
        return;
    }
    
    try {
        const response = await fetch('/api/search-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        
        const data = await response.json();
        
        if (data.found) {
            document.getElementById('foundUsername').textContent = data.user.username;
            document.getElementById('onlineStatus').textContent = data.user.online ? '🟢 Online' : '⚪ Offline';
            document.getElementById('callBtn').dataset.userId = data.user.id;
            document.getElementById('searchResults').style.display = 'block';
            
            // Set current user for contacts.js
            if (typeof window.setCurrentSearchedUser === 'function') {
                window.setCurrentSearchedUser(data.user);
            }
        } else {
            alert(data.message || 'User not found');
            document.getElementById('searchResults').style.display = 'none';
        }
    } catch (error) {
        console.error('Search error:', error);
        alert('Error searching user');
    }
}