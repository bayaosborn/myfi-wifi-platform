// =============================================
// TAG COLORS
// Manages tag-based card background colors
// =============================================

// Tag color mapping (background and text colors)
const TAG_COLORS = {
    'family': {
        bg: '#FFE5E5',      // Soft pink
        text: '#8B0000'     // Dark red
    },
    'work': {
        bg: '#E8F4FD',      // Light blue
        text: '#004085'     // Dark blue
    },
    'friends': {
        bg: '#FFF4E6',      // Warm cream
        text: '#8B4513'     // Saddle brown
    },
    'relationship': {
        bg: '#FFE6F0',      // Light rose
        text: '#C71585'     // Medium violet red
    },
    'riders': {
        bg: '#E8F5E9',      // Light green
        text: '#1B5E20'     // Dark green
    },
    'favorite': {
        bg: '#FFF9C4',      // Light yellow
        text: '#F57F17'     // Dark yellow/gold
    },
    'general': {
        bg: '#F5F5F5',      // Light gray (default)
        text: '#111111'     // Almost black
    }
};

// Apply tag color to the main contact card
function applyTagColor(tag) {
    console.log('applyTagColor called with tag:', tag);
    
    // Normalize tag to lowercase and trim whitespace
    const normalizedTag = (tag || 'general').toLowerCase().trim();
    console.log('Normalized tag:', normalizedTag);
    
    // Get colors for this tag (fallback to general if tag not found)
    const colors = TAG_COLORS[normalizedTag] || TAG_COLORS['general'];
    console.log('Using colors:', colors);
    
    // Find the main card element
    const mainCard = document.querySelector('.main-card');
    console.log('Main card element found:', mainCard);
    
    if (mainCard) {
        // Apply background color
        mainCard.style.backgroundColor = colors.bg;
        console.log('Applied background color:', colors.bg);
        
        // Apply text color to main elements
        const contactName = mainCard.querySelector('.contact-name');
        if (contactName) {
            contactName.style.color = colors.text;
            console.log('Applied text color to name:', colors.text);
        }
        
        // Keep contact details in a neutral dark color for readability
        const contactDetails = mainCard.querySelectorAll('.contact-detail');
        contactDetails.forEach(detail => {
            detail.style.color = '#333333';
        });
        
        console.log(`✓ Applied ${normalizedTag} color scheme successfully`);
    } else {
        console.error('❌ Main card element not found!');
    }
}

// Reset to default card styling
function resetCardColor() {
    const mainCard = document.querySelector('.main-card');
    
    if (mainCard) {
        mainCard.style.backgroundColor = '#FFFFFF';
        
        const contactName = mainCard.querySelector('.contact-name');
        if (contactName) {
            contactName.style.color = '#111111';
        }
        
        const contactDetails = mainCard.querySelectorAll('.contact-detail');
        contactDetails.forEach(detail => {
            detail.style.color = '#111111';
        });
    }
}

// Get all available tag colors (useful for UI display)
function getAvailableTagColors() {
    return TAG_COLORS;
}

console.log('✓ tagColors.js loaded');

















/*



// =============================================
// TAG COLORS
// Manages tag-based card background colors
// =============================================

// Tag color mapping (background and text colors)
const TAG_COLORS = {
    'family': {
        bg: '#FFE5E5',      // Soft pink
        text: '#8B0000'     // Dark red
    },
    'work': {
        bg: '#E8F4FD',      // Light blue
        text: '#004085'     // Dark blue
    },
    'friends': {
        bg: '#FFF4E6',      // Warm cream
        text: '#8B4513'     // Saddle brown
    },
    'relationship': {
        bg: '#FFE6F0',      // Light rose
        text: '#C71585'     // Medium violet red
    },
    'riders': {
        bg: '#E8F5E9',      // Light green
        text: '#1B5E20'     // Dark green
    },
    'favorite': {
        bg: '#FFF9C4',      // Light yellow
        text: '#F57F17'     // Dark yellow/gold
    },
    'general': {
        bg: '#F5F5F5',      // Light gray (default)
        text: '#111111'     // Almost black
    }
};

// Apply tag color to the main contact card
function applyTagColor(tag) {
    // Normalize tag to lowercase and trim whitespace
    const normalizedTag = (tag || 'general').toLowerCase().trim();
    
    // Get colors for this tag (fallback to general if tag not found)
    const colors = TAG_COLORS[normalizedTag] || TAG_COLORS['general'];
    
    // Find the main card element
    const mainCard = document.querySelector('.main-card');
    
    if (mainCard) {
        // Apply background color
        mainCard.style.backgroundColor = colors.bg;
        
        // Apply text color to main elements
        const contactName = mainCard.querySelector('.contact-name');
        if (contactName) {
            contactName.style.color = colors.text;
        }
        
        // Keep contact details in a neutral dark color for readability
        const contactDetails = mainCard.querySelectorAll('.contact-detail');
        contactDetails.forEach(detail => {
            detail.style.color = '#333333';
        });
        
        console.log(`Applied ${normalizedTag} color scheme:`, colors);
    }
}

// Reset to default card styling
function resetCardColor() {
    const mainCard = document.querySelector('.main-card');
    
    if (mainCard) {
        mainCard.style.backgroundColor = '#FFFFFF';
        
        const contactName = mainCard.querySelector('.contact-name');
        if (contactName) {
            contactName.style.color = '#111111';
        }
        
        const contactDetails = mainCard.querySelectorAll('.contact-detail');
        contactDetails.forEach(detail => {
            detail.style.color = '#111111';
        });
    }
}

// Get all available tag colors (useful for UI display)
function getAvailableTagColors() {
    return TAG_COLORS;
}