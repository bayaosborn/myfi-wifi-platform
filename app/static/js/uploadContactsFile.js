// =============================================
// VCF/CSV FILE UPLOAD
// Simple, efficient contact import
// =============================================

document.getElementById('uploadBtn').addEventListener('click', () => {
    document.getElementById('contactsFileInput').click();
});

document.getElementById('contactsFileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const status = document.getElementById('status');
    status.textContent = 'Reading file...';

    try {
        const fileContent = await file.text();
        const isVCF = file.name.toLowerCase().endsWith('.vcf');
        const isCSV = file.name.toLowerCase().endsWith('.csv');

        if (!isVCF && !isCSV) {
            status.textContent = '✗ Only .vcf or .csv files allowed';
            return;
        }

        const contacts = isVCF ? parseVCF(fileContent) : parseCSV(fileContent);

        if (contacts.length === 0) {
            status.textContent = '✗ No contacts found in file';
            return;
        }

        status.textContent = `Uploading ${contacts.length} contacts...`;

        // Send to backend
        const response = await fetch('/api/contacts/bulk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contacts })
        });

        const result = await response.json();

        if (result.success) {
            status.textContent = `✓ Uploaded ${result.count} contacts`;
            
            // Reload display
            if (typeof loadContactsFromDatabase === 'function') {
                setTimeout(() => loadContactsFromDatabase(), 800);
            }

            setTimeout(() => closeModals(), 1500);
        } else {
            status.textContent = `✗ ${result.error}`;
        }

    } catch (error) {
        console.error('Upload error:', error);
        status.textContent = '✗ Upload failed';
    }
});

// Parse VCF (simple & efficient)
function parseVCF(content) {
    const contacts = [];
    const vcards = content.split('BEGIN:VCARD');

    for (let card of vcards) {
        if (!card.includes('END:VCARD')) continue;

        const getName = (str) => {
            const fn = str.match(/FN:(.*)/i);
            const n = str.match(/N:(.*)/i);
            return fn?.[1]?.trim() || n?.[1]?.split(';')[1]?.trim() || '';
        };

        const getPhone = (str) => {
            const tel = str.match(/TEL[^:]*:(.*)/i);
            return tel?.[1]?.trim().replace(/[\s-()]/g, '') || '';
        };

        const getEmail = (str) => {
            const email = str.match(/EMAIL[^:]*:(.*)/i);
            return email?.[1]?.trim() || '';
        };

        const name = getName(card);
        if (!name) continue;

        contacts.push({
            name,
            phone: getPhone(card),
            email: getEmail(card),
            tag: 'General',
            notes: ''
        });
    }

    return contacts;
}

// Parse CSV
function parseCSV(content) {
    const lines = content.split('\n').filter(l => l.trim());
    if (lines.length < 2) return [];

    const headers = lines[0].toLowerCase().split(',');
    const contacts = [];

    for (let i = 1; i < lines.length; i++) {
        const vals = lines[i].split(',');
        const name = vals[headers.indexOf('name')] || vals[headers.indexOf('full name')] || '';
        
        if (name.trim()) {
            contacts.push({
                name: name.trim(),
                phone: (vals[headers.indexOf('phone')] || '').trim(),
                email: (vals[headers.indexOf('email')] || '').trim(),
                tag: (vals[headers.indexOf('tag')] || 'General').trim(),
                notes: (vals[headers.indexOf('notes')] || '').trim()
            });
        }
    }

    return contacts;
}