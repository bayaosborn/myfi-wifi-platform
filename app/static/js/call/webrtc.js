/**
 * MyFi WebRTC - Clean Implementation with Echo Cancellation
 * Fixes the acoustic feedback (whistle) problem
 */

// WebRTC Configuration with STUN servers
const rtcConfig = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
        { urls: 'stun:stun2.l.google.com:19302' }
    ]
};

// Audio constraints with echo cancellation enabled
const audioConstraints = {
    audio: {
        echoCancellation: true,      // ⭐ Prevents feedback loop
        noiseSuppression: true,       // ⭐ Reduces background noise
        autoGainControl: true,        // ⭐ Normalizes volume
        sampleRate: 48000,           // High quality audio
        channelCount: 1              // Mono (saves bandwidth)
    },
    video: false
};

// Global state
let peerConnection = null;
let localStream = null;
let socket = null;
let currentCall = {
    userId: null,
    phone: null,
    name: null,
    callId: null,
    startTime: null,
    timerInterval: null,
    duration: 0
};

// ==================== INITIALIZATION ====================

function initSocket() {
    if (socket && socket.connected) {
        socket.disconnect();
    }
    
    socket = io({
        transports: ['websocket', 'polling'],
        upgrade: true,
        rememberUpgrade: true,
        forceNew: true
    });
    
    socket.on('connect', () => {
        console.log('✅ Socket connected:', socket.id);
    });
    
    socket.on('disconnect', () => {
        console.log('❌ Socket disconnected');
    });
    
    socket.on('incoming_call', handleIncomingCall);
    socket.on('call_answered', handleCallAnswered);
    socket.on('call_rejected', handleCallRejected);
    socket.on('ice_candidate', handleIceCandidate);
    socket.on('call_ended', handleCallEnded);
    socket.on('call_failed', handleCallFailed);
}

// ==================== PEER CONNECTION ====================

async function createPeerConnection() {
    try {
        peerConnection = new RTCPeerConnection(rtcConfig);
        
        // Get local audio with echo cancellation
        localStream = await navigator.mediaDevices.getUserMedia(audioConstraints);
        
        // Add local stream to peer connection
        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
            console.log('✅ Added local track:', track.kind);
        });
        
        // Handle remote stream
        peerConnection.ontrack = (event) => {
            console.log('✅ Received remote stream');
            const remoteAudio = document.getElementById('remoteAudio') || createRemoteAudio();
            remoteAudio.srcObject = event.streams[0];
            
            // Ensure remote audio plays
            remoteAudio.play().catch(e => {
                console.warn('⚠️ Auto-play blocked, user interaction needed');
            });
        };
        
        // Handle ICE candidates
        peerConnection.onicecandidate = (event) => {
            if (event.candidate && currentCall.userId) {
                socket.emit('ice_candidate', {
                    recipient_id: currentCall.userId,
                    candidate: event.candidate
                });
            }
        };
        
        // Monitor connection state
        peerConnection.oniceconnectionstatechange = () => {
            console.log('🔄 ICE state:', peerConnection.iceConnectionState);
            
            if (peerConnection.iceConnectionState === 'disconnected' ||
                peerConnection.iceConnectionState === 'failed') {
                console.warn('⚠️ Connection lost');
                endCall();
            }
        };
        
        console.log('✅ Peer connection created');
        return peerConnection;
        
    } catch (error) {
        console.error('❌ Error creating peer connection:', error);
        
        if (error.name === 'NotAllowedError') {
            showNotification('Microphone access denied. Please allow microphone permissions.', 'error');
        } else if (error.name === 'NotFoundError') {
            showNotification('No microphone found. Please connect a microphone.', 'error');
        } else {
            showNotification('Failed to access microphone: ' + error.message, 'error');
        }
        
        return null;
    }
}

function createRemoteAudio() {
    const audio = document.createElement('audio');
    audio.id = 'remoteAudio';
    audio.autoplay = true;
    audio.style.display = 'none';
    document.body.appendChild(audio);
    return audio;
}

// ==================== OUTGOING CALL ====================

async function initiateCall(userId, phone, name) {
    console.log('📞 Initiating call to:', name, phone);
    
    currentCall.userId = userId;
    currentCall.phone = phone;
    currentCall.name = name;
    
    const pc = await createPeerConnection();
    if (!pc) return;
    
    try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        
        socket.emit('call_user', {
            callee_id: userId,
            offer: offer
        });
        
        showCallScreen('Calling ' + (name || phone) + '...');
        
    } catch (error) {
        console.error('❌ Error creating offer:', error);
        showNotification('Failed to initiate call', 'error');
        endCall();
    }
}

// ==================== INCOMING CALL ====================

async function handleIncomingCall(data) {
    console.log('📞 Incoming call from:', data.caller_name || data.caller_phone);
    
    currentCall.userId = data.caller_id;
    currentCall.phone = data.caller_phone;
    currentCall.name = data.caller_name;
    currentCall.callId = data.call_id;
    
    // Store offer for later (when user accepts)
    window.pendingOffer = data.offer;
    
    // Show incoming call modal
    showIncomingCallModal(data);
}

async function acceptCall() {
    console.log('✅ Accepting call');
    hideIncomingCallModal();
    
    const pc = await createPeerConnection();
    if (!pc) return;
    
    try {
        await pc.setRemoteDescription(new RTCSessionDescription(window.pendingOffer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        
        socket.emit('answer_call', {
            caller_id: currentCall.userId,
            answer: answer,
            call_id: currentCall.callId
        });
        
        showCallScreen('Connected to ' + (currentCall.name || currentCall.phone));
        startCallTimer();
        
    } catch (error) {
        console.error('❌ Error accepting call:', error);
        showNotification('Failed to accept call', 'error');
        endCall();
    }
}

function rejectCall() {
    console.log('❌ Rejecting call');
    
    socket.emit('reject_call', {
        caller_id: currentCall.userId,
        call_id: currentCall.callId
    });
    
    hideIncomingCallModal();
    resetCallState();
}

// ==================== CALL ANSWERED ====================

async function handleCallAnswered(data) {
    console.log('✅ Call answered');
    
    currentCall.callId = data.call_id;
    
    try {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
        
        const statusEl = document.getElementById('callStatus');
        if (statusEl) statusEl.textContent = 'Connected';
        
        startCallTimer();
        
    } catch (error) {
        console.error('❌ Error handling answer:', error);
    }
}

// ==================== ICE CANDIDATES ====================

async function handleIceCandidate(data) {
    try {
        if (peerConnection && data.candidate) {
            await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
        }
    } catch (error) {
        console.error('❌ Error adding ICE candidate:', error);
    }
}

// ==================== CALL ENDED ====================

function handleCallEnded(data) {
    console.log('📴 Call ended by other user');
    showNotification('Call ended', 'info');
    endCall();
}

function handleCallRejected() {
    console.log('❌ Call rejected');
    showNotification('Call was rejected', 'info');
    endCall();
}

function handleCallFailed(data) {
    console.log('❌ Call failed:', data.reason);
    showNotification('Call failed: ' + data.reason, 'error');
    endCall();
}

function endCall() {
    console.log('📴 Ending call');
    
    // Calculate duration
    if (currentCall.startTime) {
        currentCall.duration = Math.floor((Date.now() - currentCall.startTime) / 1000);
    }
    
    // Notify server
    if (currentCall.userId && socket) {
        socket.emit('hang_up', {
            other_user_id: currentCall.userId,
            call_id: currentCall.callId,
            duration: currentCall.duration
        });
    }
    
    // Clean up WebRTC
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }
    
    if (localStream) {
        localStream.getTracks().forEach(track => {
            track.stop();
            console.log('🛑 Stopped track:', track.kind);
        });
        localStream = null;
    }
    
    // Clean up remote audio
    const remoteAudio = document.getElementById('remoteAudio');
    if (remoteAudio) {
        remoteAudio.srcObject = null;
        remoteAudio.remove();
    }
    
    // Stop timer
    if (currentCall.timerInterval) {
        clearInterval(currentCall.timerInterval);
    }
    
    // Reset UI
    hideCallScreen();
    
    // Reset state
    resetCallState();
    
    // Reload call history if available
    if (typeof loadCallHistory === 'function') {
        loadCallHistory();
    }
}

// ==================== CALL TIMER ====================

function startCallTimer() {
    currentCall.startTime = Date.now();
    currentCall.duration = 0;
    
    currentCall.timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - currentCall.startTime) / 1000);
        currentCall.duration = elapsed;
        
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        
        const timerEl = document.getElementById('callTimer');
        if (timerEl) {
            timerEl.textContent = `${minutes}:${seconds}`;
        }
    }, 1000);
}

// ==================== AUDIO CONTROLS ====================

function toggleMute() {
    if (!localStream) return;
    
    const audioTrack = localStream.getAudioTracks()[0];
    if (!audioTrack) return;
    
    audioTrack.enabled = !audioTrack.enabled;
    
    const muteBtn = document.getElementById('muteBtn');
    if (muteBtn) {
        muteBtn.textContent = audioTrack.enabled ? '🎤 Mute' : '🔇 Unmuted';
        muteBtn.classList.toggle('muted', !audioTrack.enabled);
    }
    
    console.log('🎤 Mute:', !audioTrack.enabled);
}

function toggleSpeaker() {
    // Speaker control is handled by device
    // On mobile, this would switch between earpiece and speaker
    showNotification('Speaker control: Use device volume buttons', 'info');
}

// ==================== UI HELPERS ====================

function showCallScreen(status) {
    const callScreen = document.getElementById('callScreen');
    if (!callScreen) return;
    
    const statusEl = document.getElementById('callStatus');
    const nameEl = document.getElementById('callUserName');
    
    if (statusEl) statusEl.textContent = status;
    if (nameEl) nameEl.textContent = currentCall.name || currentCall.phone;
    
    callScreen.style.display = 'flex';
    
    // Hide other sections
    const searchSection = document.querySelector('.search-section');
    if (searchSection) searchSection.style.display = 'none';
}

function hideCallScreen() {
    const callScreen = document.getElementById('callScreen');
    if (callScreen) callScreen.style.display = 'none';
    
    const searchSection = document.querySelector('.search-section');
    if (searchSection) searchSection.style.display = 'block';
    
    const timerEl = document.getElementById('callTimer');
    if (timerEl) timerEl.textContent = '00:00';
}

function showIncomingCallModal(data) {
    const modal = document.getElementById('incomingCallModal');
    if (!modal) return;
    
    const nameEl = document.getElementById('incomingCallerName');
    if (nameEl) {
        nameEl.textContent = data.caller_name || data.caller_phone || 'Unknown';
    }
    
    modal.style.display = 'flex';
    
    // Play ringtone if available
    playRingtone();
}

function hideIncomingCallModal() {
    const modal = document.getElementById('incomingCallModal');
    if (modal) modal.style.display = 'none';
    
    stopRingtone();
}

function playRingtone() {
    // TODO: Implement ringtone sound
    console.log('🔔 Playing ringtone');
}

function stopRingtone() {
    // TODO: Stop ringtone sound
    console.log('🔕 Stopping ringtone');
}

function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // TODO: Implement toast notifications
    alert(message);
}

function resetCallState() {
    currentCall = {
        userId: null,
        phone: null,
        name: null,
        callId: null,
        startTime: null,
        timerInterval: null,
        duration: 0
    };
}

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 WebRTC initialized');
    initSocket();
    
    // Attach event listeners
    const hangUpBtn = document.getElementById('hangUpBtn');
    if (hangUpBtn) {
        hangUpBtn.addEventListener('click', endCall);
    }
    
    const muteBtn = document.getElementById('muteBtn');
    if (muteBtn) {
        muteBtn.addEventListener('click', toggleMute);
    }
    
    const speakerBtn = document.getElementById('speakerBtn');
    if (speakerBtn) {
        speakerBtn.addEventListener('click', toggleSpeaker);
    }
    
    const acceptBtn = document.getElementById('acceptCallBtn');
    if (acceptBtn) {
        acceptBtn.addEventListener('click', acceptCall);
    }
    
    const rejectBtn = document.getElementById('rejectCallBtn');
    if (rejectBtn) {
        rejectBtn.addEventListener('click', rejectCall);
    }
});

// Export for use in other scripts
window.MyFiCall = {
    initiateCall,
    endCall,
    toggleMute,
    toggleSpeaker
};