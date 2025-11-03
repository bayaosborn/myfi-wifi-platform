// WebRTC configuration




const rtcConfig = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ]
};

let peerConnection = null;
let localStream = null;
let socket = null;
let currentCallUserId = null;
let currentCallUsername = null;
let callStartTime = null;
let callTimerInterval = null;
let currentCallId = null;
let callDuration = 0;

// Initialize socket connection
function initSocket() {
    // Disconnect existing socket if any
    if (socket && socket.connected) {
        socket.disconnect();
    }
    
    socket = io({
        transports: ['websocket', 'polling'],
        forceNew: true  // Force new connection
    });
    
    socket.on('connect', () => {
        console.log('✅ Socket connected:', socket.id);
    });
    
    socket.on('disconnect', () => {
        console.log('❌ Socket disconnected');
    });
    
    socket.on('incoming_call', handleIncomingCall);
    socket.on('call_answered', handleCallAnswered);
    socket.on('ice_candidate', handleIceCandidate);
    socket.on('call_ended', handleCallEnded);
    socket.on('call_failed', (data) => {
        console.log('❌ Call failed:', data.reason);
        alert('Call failed: ' + data.reason); 
        endCall();
    });
}

// Create peer connection
async function createPeerConnection(isInitiator) {
    peerConnection = new RTCPeerConnection(rtcConfig);
    
    // Get local audio stream
    try {
        localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
        });
        console.log('✅ Microphone access granted');
    } catch (error) {
        console.error('❌ Error accessing microphone:', error);
        alert('Could not access microphone. Please check permissions.');
        return null;
    }
    
    // Handle remote stream
    peerConnection.ontrack = (event) => {
        console.log('✅ Received remote audio stream');
        const remoteAudio = new Audio();
        remoteAudio.srcObject = event.streams[0];
        remoteAudio.play();
    };
    
    // Handle ICE candidates
    peerConnection.onicecandidate = (event) => {
        if (event.candidate && currentCallUserId) {
            console.log('🧊 Sending ICE candidate');
            socket.emit('ice_candidate', {
                recipient_id: currentCallUserId,
                candidate: event.candidate
            });
        }
    };
    
    peerConnection.oniceconnectionstatechange = () => {
        console.log('🔄 ICE connection state:', peerConnection.iceConnectionState);
    };
    
    return peerConnection;
}

// Initiate call
async function initiateCall(userId, username) {
    console.log('📞 Initiating call to:', username, 'ID:', userId);
    
    currentCallUserId = userId;
    currentCallUsername = username;
    
    const pc = await createPeerConnection(true);
    if (!pc) return;
    
    try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        
        console.log('📤 Sending call offer');
        socket.emit('call_user', {
            callee_id: userId,
            offer: offer
        });
        
        showCallScreen('Calling ' + username + '...');
    } catch (error) {
        console.error('❌ Error creating offer:', error);
        alert('Failed to initiate call');
    }
}



//New code added from here to save Contacts 


async function handleIncomingCall(data) {
    console.log('📞 Incoming call from:', data.caller_username);
    
    currentCallUserId = data.caller_id;
    currentCallUsername = data.caller_username;
    currentCallId = data.call_id;  // Store call ID
    
    document.getElementById('incomingCallerName').textContent = data.caller_username;
    document.getElementById('incomingCallModal').style.display = 'flex';
    
    window.incomingOffer = data.offer;
}


//Accept Call function 

async function acceptCall() {
    console.log('✅ Accepting call');
    document.getElementById('incomingCallModal').style.display = 'none';
    
    const pc = await createPeerConnection(false);
    if (!pc) return;
    
    try {
        await pc.setRemoteDescription(new RTCSessionDescription(window.incomingOffer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        
        console.log('📤 Sending answer');
        socket.emit('answer_call', {
            caller_id: currentCallUserId,
            answer: answer,
            call_id: currentCallId
        });
        
        showCallScreen('Connected to ' + currentCallUsername);
        startCallTimer();
    } catch (error) {
        console.error('❌ Error accepting call:', error);
    }
}




/*
// Handle incoming call
async function handleIncomingCall(data) {
    console.log('📞 Incoming call from:', data.caller_username);
    
    currentCallUserId = data.caller_id;
    currentCallUsername = data.caller_username;
    
    document.getElementById('incomingCallerName').textContent = data.caller_username;
    document.getElementById('incomingCallModal').style.display = 'flex';
    
    // Store the offer for when user accepts
    window.incomingOffer = data.offer;
}



// Accept incoming call
async function acceptCall() {
    console.log('✅ Accepting call');
    document.getElementById('incomingCallModal').style.display = 'none';
    
    const pc = await createPeerConnection(false);
    if (!pc) return;
    
    try {
        await pc.setRemoteDescription(new RTCSessionDescription(window.incomingOffer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        
        console.log('📤 Sending answer');
        socket.emit('answer_call', {
            caller_id: currentCallUserId,
            answer: answer
        });
        
        showCallScreen('Connected to ' + currentCallUsername);
        startCallTimer();
    } catch (error) {
        console.error('❌ Error accepting call:', error);
    }
}

*/




// Reject call
function rejectCall() {
    console.log('❌ Rejecting call');
    document.getElementById('incomingCallModal').style.display = 'none';
    socket.emit('hang_up', { other_user_id: currentCallUserId });
    currentCallUserId = null;
    currentCallUsername = null;
}



async function handleCallAnswered(data) {
    console.log('✅ Call answered');
    currentCallId = data.call_id;  // Store call ID
    
    try {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
        document.getElementById('callStatus').textContent = 'Connected';
        startCallTimer();
    } catch (error) {
        console.error('❌ Error handling answer:', error);
    }
}




/*
// Handle call answered
async function handleCallAnswered(data) {
    console.log('✅ Call answered');
    try {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
        document.getElementById('callStatus').textContent = 'Connected';
        startCallTimer();
    } catch (error) {
        console.error('❌ Error handling answer:', error);
    }
}
*/




// Handle ICE candidate
async function handleIceCandidate(data) {
    console.log('🧊 Received ICE candidate');
    try {
        if (peerConnection) {
            await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
        }
    } catch (error) {
        console.error('❌ Error adding ICE candidate:', error);
    }
}

// Handle call ended
function handleCallEnded() {
    console.log('📴 Call ended by other user');
    endCall();
    alert('Call ended');
}



function endCall() {
    console.log('📴 Ending call');
    
    // Calculate duration
    if (callStartTime) {
        callDuration = Math.floor((Date.now() - callStartTime) / 1000);
    }
    
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }
    
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null;
    }
    
    if (callTimerInterval) {
        clearInterval(callTimerInterval);
        callTimerInterval = null;
    }
    
    if (currentCallUserId) {
        socket.emit('hang_up', {
            other_user_id: currentCallUserId,
            call_id: currentCallId,
            duration: callDuration
        });
    }
    
    currentCallUserId = null;
    currentCallUsername = null;
    currentCallId = null;
    callDuration = 0;
    
    hideCallScreen();
    
    // Reload call history
    // Reload call history
    if (typeof loadCallHistory === 'function') {
        loadCallHistory();
    }
}



/*
// End call
function endCall() {
    console.log('📴 Ending call');
    
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }
    
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null;
    }
    
    if (callTimerInterval) {
        clearInterval(callTimerInterval);
        callTimerInterval = null;
    }
    
    if (currentCallUserId) {
        socket.emit('hang_up', { other_user_id: currentCallUserId });
    }
    
    currentCallUserId = null;
    currentCallUsername = null;
    
    hideCallScreen();
}
*/







// Show call screen
function showCallScreen(status) {
    document.getElementById('callStatus').textContent = status;
    document.getElementById('callUsername').textContent = currentCallUsername;
    document.getElementById('callScreen').style.display = 'block';
    document.querySelector('.search-section').style.display = 'none';
    document.getElementById('searchResults').style.display = 'none';
}

// Hide call screen
function hideCallScreen() {
    document.getElementById('callScreen').style.display = 'none';
    document.querySelector('.search-section').style.display = 'block';
    document.getElementById('callTimer').textContent = '00:00';
}


function startCallTimer() {
    callStartTime = Date.now();
    callDuration = 0;
    
    callTimerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
        callDuration = elapsed;
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        document.getElementById('callTimer').textContent = `${minutes}:${seconds}`;
    }, 1000);
}




/*
// Call timer
function startCallTimer() {
    callStartTime = Date.now();
    callTimerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        document.getElementById('callTimer').textContent = `${minutes}:${seconds}`;
    }, 1000);
}

*/




// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing search page');
    initSocket();
});