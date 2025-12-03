let currentEditingContactId = null;



document.getElementById('editContactBtn').addEventListener('click', () => {
    if (contactsArray.length === 0) return;

    const contact = contactsArray[currentIndex];
    currentEditingContactId = contact.id;

    alert("Name:", contact.name)

});

