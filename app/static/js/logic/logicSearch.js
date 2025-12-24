/**
 * Logic Search - Ultra Simplified
 * Only does: Detect Logic, send message, execute hidden commands
 */

class LogicSearch {
    constructor() {
        // Get search input
        this.searchInput = document.getElementById('contactSearchInput');
        
        // State
        this.isLogicMode = false;
        this.originalPlaceholder = 'Search contacts...';
        
        this.init();
    }
    
    init() {
        if (!this.searchInput) {
            console.error('❌ Search input not found');
            return;
        }
        
        // Listen for typing
        this.searchInput.addEventListener('input', (e) => {
            this.handleInput(e);
        });
        
        // Listen for Enter key
        this.searchInput.addEventListener('keydown', (e) => {
            this.handleKeydown(e);
        });
        
        console.log('✓ Logic search initialized');
    }
    
    handleInput(e) {
        const value = e.target.value.trim();
        
        // Changed to "Logic" instead of "/logic"
        if (value === 'Logic') {
            this.activateLogicMode();
            e.target.value = '';
        }
    }
    
    handleKeydown(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            
            const message = this.searchInput.value.trim();
            
            if (this.isLogicMode && message) {
                this.sendToLogic(message);
            }
        }
        
        // ESC key exits Logic mode
        if (e.key === 'Escape' && this.isLogicMode) {
            this.deactivateLogicMode();
        }
    }
    
    activateLogicMode() {
        this.isLogicMode = true;
        this.searchInput.placeholder = '💡 Ask Logic... (e.g., "Call Sarah")';
        this.searchInput.classList.add('logic-active');
        
        console.log('✓ Logic mode activated');
    }
    
    deactivateLogicMode() {
        this.isLogicMode = false;
        this.searchInput.placeholder = this.originalPlaceholder;
        this.searchInput.classList.remove('logic-active');
        
        console.log('✓ Logic mode deactivated');
    }
    
    async sendToLogic(message) {
        // Clear input
        this.searchInput.value = '';
        this.searchInput.placeholder = '💡 Logic is thinking...';
        this.searchInput.disabled = true;
        
        try {
            // Call API
            const response = await fetch('/api/logic/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Show response briefly
                this.showResponse(data.message);
                
                // Execute hidden commands SILENTLY
                if (data.hidden_commands && data.hidden_commands.length > 0) {
                    this.executeCommands(data.hidden_commands);
                }
            } else {
                this.showError('Logic error: ' + data.error);
            }
            
        } catch (error) {
            console.error('❌ API error:', error);
            this.showError('Connection error');
        } finally {
            // Re-enable input
            this.searchInput.disabled = false;
            this.searchInput.placeholder = '💡 Ask Logic...';
        }
    }
    
    showResponse(message) {
        this.searchInput.placeholder = `💡 ${message}`;
        
        setTimeout(() => {
            this.searchInput.placeholder = '💡 Ask Logic...';
        }, 2000);
    }
    
    showError(message) {
        this.searchInput.placeholder = `❌ ${message}`;
        
        setTimeout(() => {
            this.searchInput.placeholder = '💡 Ask Logic...';
        }, 3000);
    }
    
    executeCommands(commands) {
        console.log('🎯 Executing commands:', commands);
        
        commands.forEach(cmd => {
            if (cmd.action === 'call') {
                this.executeCall(cmd);
            } else if (cmd.action === 'message') {
                this.executeMessage(cmd);
            } else if (cmd.action === 'email') {
            this.executeEmail(cmd);
        }
        });
    }
    
    executeCall(command) {
        const phone = command.phone;
        const name = command.contact_name || 'contact';
        
        if (!phone) {
            console.error('❌ No phone number in command');
            return;
        }
        
        // Clean phone number
        const cleanPhone = phone.replace(/\s+/g, '');
        
        console.log(`📞 Calling ${name} at ${cleanPhone}`);
        
        // Trigger phone app
        window.location.href = `tel:${cleanPhone}`;
    }
    
    executeMessage(command) {
        const phone = command.phone;
        const name = command.contact_name || 'contact';
        
        if (!phone) {
            console.error('❌ No phone number in message command');
            return;
        }
        
        // Clean phone number
        const cleanPhone = phone.replace(/[^\d+]/g, '');
        
        // Default message body
        const messageBody = 'MyFi:';
        const encodedMessage = encodeURIComponent(messageBody);
        
        console.log(`💬 Messaging ${name} at ${cleanPhone}`);
        
        // Trigger SMS app
        window.location.href = `sms:${cleanPhone}?body=${encodedMessage}`;
        
        
    }


    executeEmail(command) {
    /**
     * Execute email command
     * 
     * Two modes:
     * 1. Simple (no draft): Just opens email client
     * 2. Draft mode: Shows draft, user can edit/send
     * 
     * Args:
     *   command: {
     *     action: "email",
     *     email: "person@email.com",
     *     contact_name: "Sarah",
     *     subject: "Subject line",
     *     body: "Email body text"
     *   }
     */
    const email = command.email;
    const name = command.contact_name || 'contact';
    const subject = command.subject || '';
    const body = command.body || '';
    
    if (!email) {
        console.error('❌ No email address in command');
        this.showError(`${name} has no email address`);
        return;
    }
    
    // Build mailto link
    const subjectEncoded = encodeURIComponent(subject);
    const bodyEncoded = encodeURIComponent(body);
    
    let mailtoLink = `mailto:${email}`;
    
    // Add subject and body if they exist
    const params = [];
    if (subject) params.push(`subject=${subjectEncoded}`);
    if (body) params.push(`body=${bodyEncoded}`);
    
    if (params.length > 0) {
        mailtoLink += '?' + params.join('&');
    }
    
    console.log(`📧 Emailing ${name} at ${email}`);
    
    // Show what's being drafted (if there's content)
    if (subject || body) {
        console.log(`📝 Subject: ${subject}`);
        console.log(`📝 Body preview: ${body.substring(0, 100)}...`);
    }
    
    // Trigger email client
    // This opens the default email app with pre-filled content
    // User can review/edit before sending
    window.location.href = mailtoLink;
}



    
    
}  // ← CLASS ENDS HERE (all methods inside)


// Initialize on page load
let logicSearch;
document.addEventListener('DOMContentLoaded', () => {
    logicSearch = new LogicSearch();
});