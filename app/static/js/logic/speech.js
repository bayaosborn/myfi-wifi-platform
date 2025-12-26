/**
 * Speech-to-Text for Logic
 * 
 * Strategy:
 * 1. Use browser's Web Speech API (fast, free)
 * 2. If not supported, record and send to backend
 * 3. Auto-activate Logic when mic tapped
 * 4. Normalize text before sending to Logic
 */

class SpeechLogic {
    constructor(logicSearchInstance) {
        this.logicSearch = logicSearchInstance;
        this.searchInput = document.getElementById('contactSearchInput');
        
        // Check browser support
        this.webSpeechSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
        
        // State
        this.isListening = false;
        this.recognition = null;
        
        // For fallback recording
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        this.init();
    }
    
    init() {
        this.createMicButton();
        
        if (this.webSpeechSupported) {
            this.initWebSpeech();
            console.log('✓ Using browser Web Speech API');
        } else {
            console.log('⚠️ Web Speech not supported, will use recording fallback');
        }
    }
    
    /**
     * Create microphone button
     */
    createMicButton() {
        const micBtn = document.createElement('button');
        micBtn.id = 'micBtn';
        micBtn.className = 'mic-btn';
        micBtn.innerHTML = '🎤';
        micBtn.title = 'Voice input';
        
        // Insert after search input
        this.searchInput.parentNode.appendChild(micBtn);
        
        // Add click handler
        micBtn.addEventListener('click', () => this.toggleListening());
        
        this.micBtn = micBtn;
    }
    
    /**
     * Initialize Web Speech API (Chrome, Edge, Safari)
     */
    initWebSpeech() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configuration
        this.recognition.continuous = false;  // Stop after one result
        this.recognition.interimResults = false;  // Only final results
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;
        
        // Event handlers
        this.recognition.onstart = () => {
            this.isListening = true;
            this.micBtn.innerHTML = '🔴';
            this.micBtn.classList.add('listening');
            this.searchInput.placeholder = '🎤 Listening...';
        };
        
        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('🎤 Heard:', transcript);
            this.handleTranscript(transcript);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.stopListening();
            
            // Fallback to recording if error
            if (event.error === 'not-allowed') {
                alert('Microphone access denied. Please allow microphone access.');
            } else {
                // Try recording fallback
                this.startRecording();
            }
        };
        
        this.recognition.onend = () => {
            this.stopListening();
        };
    }
    
    /**
     * Toggle listening state
     */
    toggleListening() {
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }
    
    /**
     * Start listening via Web Speech or Recording
     */
    startListening() {
        if (this.webSpeechSupported && this.recognition) {
            try {
                this.recognition.start();
            } catch (error) {
                console.error('Failed to start recognition:', error);
                this.startRecording();
            }
        } else {
            this.startRecording();
        }
    }
    
    /**
     * Stop listening
     */
    stopListening() {
        this.isListening = false;
        this.micBtn.innerHTML = '🎤';
        this.micBtn.classList.remove('listening');
        this.searchInput.placeholder = 'Search contacts...';
        
        if (this.recognition) {
            try {
                this.recognition.stop();
            } catch (e) {
                // Already stopped
            }
        }
        
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
    }
    
    /**
     * Handle recognized text
     */
    handleTranscript(rawText) {
        console.log('Raw transcript:', rawText);
        
        // Normalize text
        const normalized = this.normalizeText(rawText);
        console.log('Normalized:', normalized);
        
        // Auto-activate Logic and inject command
        this.logicSearch.activateLogicMode();
        this.searchInput.value = normalized;
        
        // Auto-submit after short delay (let user see what was heard)
        setTimeout(() => {
            if (this.logicSearch.isLogicMode && normalized) {
                this.logicSearch.sendToLogic(normalized);
                this.searchInput.value = '';
            }
        }, 500);
    }
    
    /**
     * Normalize recognized text
     * 
     * Removes filler words, fixes common errors
     */
    normalizeText(text) {
        let normalized = text.toLowerCase().trim();
        
        // Remove filler words
        const fillers = [
            'please', 'uh', 'um', 'hey', 'okay', 'kindly',
            'can you', 'could you', 'would you'
        ];
        
        fillers.forEach(filler => {
            const regex = new RegExp(`\\b${filler}\\b`, 'gi');
            normalized = normalized.replace(regex, '');
        });
        
        // Fix common speech-to-text errors
        const corrections = {
            'logical': 'Logic',
            'call her': 'call',
            'message her': 'message',
            'email her': 'email',
            'text her': 'message',
            'phone': 'call'
        };
        
        Object.keys(corrections).forEach(wrong => {
            const regex = new RegExp(`\\b${wrong}\\b`, 'gi');
            normalized = normalized.replace(regex, corrections[wrong]);
        });
        
        // Remove "Logic" prefix if user said it
        normalized = normalized.replace(/^logic\s+/i, '');
        
        // Clean up extra spaces
        normalized = normalized.replace(/\s+/g, ' ').trim();
        
        // Capitalize first letter of names (simple heuristic)
        normalized = normalized.replace(/\b(call|message|email)\s+([a-z])/gi, 
            (match, action, firstLetter) => `${action} ${firstLetter.toUpperCase()}`
        );
        
        return normalized;
    }
    
    /**
     * Fallback: Record audio and send to backend
     */
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (e) => {
                this.audioChunks.push(e.data);
            };
            
            this.mediaRecorder.onstop = async () => {
                await this.sendAudioToBackend();
            };
            
            this.mediaRecorder.start();
            
            this.isListening = true;
            this.micBtn.innerHTML = '🔴';
            this.micBtn.classList.add('listening');
            this.searchInput.placeholder = '🎤 Recording...';
            
            console.log('Recording started (fallback mode)');
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            alert('Could not access microphone');
        }
    }
    
    /**
     * Send recorded audio to backend for transcription
     */
    async sendAudioToBackend() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'speech.webm');
        
        this.micBtn.innerHTML = '⏳';
        this.searchInput.placeholder = 'Processing...';
        
        try {
            const response = await fetch('/api/logic/speech', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.handleTranscript(data.text);
            } else {
                console.error('Transcription failed:', data.error);
                alert('Could not understand audio');
            }
            
        } catch (error) {
            console.error('Failed to send audio:', error);
            alert('Failed to process speech');
        } finally {
            this.stopListening();
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Wait for logicSearch to be initialized
    setTimeout(() => {
        if (typeof logicSearch !== 'undefined') {
            window.speechLogic = new SpeechLogic(logicSearch);
        }
    }, 100);
});