// API base URL
const API_URL = 'http://127.0.0.1:8000';

// DOM Elements
const authContainer = document.getElementById('authContainer');
const appContainer = document.getElementById('appContainer');
const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const logoutBtn = document.getElementById('logoutBtn');
const noteInput = document.getElementById('noteInput');
const addNoteBtn = document.getElementById('addNoteBtn');
const notesGrid = document.getElementById('notesGrid');
const emptyState = document.getElementById('emptyState');
const modal = document.getElementById('editModal');
const editTextarea = document.getElementById('editNoteTextarea');
const saveNoteBtn = document.getElementById('saveNoteBtn');
const modalClose = document.querySelector('.modal-close');

let currentToken = null;
let editingNoteId = null;

// ===== AUTHENTICATION =====

// Check if user is already logged in
window.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('authToken');
    if (token) {
        currentToken = token;
        showAppScreen();
        loadNotes();
    } else {
        showLoginScreen();
    }
});

// Toggle between login and signup forms
function toggleAuthForm(e) {
    e.preventDefault();
    loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
    signupForm.style.display = signupForm.style.display === 'none' ? 'block' : 'none';
}

// Login form submission
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorMsg = document.getElementById('loginError');
    const loading = document.getElementById('loginLoading');

    errorMsg.textContent = '';
    loading.style.display = 'block';

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            currentToken = data.token;
            localStorage.setItem('authToken', data.token);
            loginForm.reset();
            showAppScreen();
            loadNotes();
        } else {
            errorMsg.textContent = data.message || 'Login failed';
        }
    } catch (error) {
        errorMsg.textContent = 'Network error. Please try again.';
    } finally {
        loading.style.display = 'none';
    }
});

// Signup form submission
signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('signupConfirmPassword').value;
    const errorMsg = document.getElementById('signupError');
    const loading = document.getElementById('signupLoading');

    if (password !== confirmPassword) {
        errorMsg.textContent = 'Passwords do not match';
        return;
    }

    errorMsg.textContent = '';
    loading.style.display = 'block';

    try {
        const response = await fetch(`${API_URL}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            currentToken = data.token;
            localStorage.setItem('authToken', data.token);
            signupForm.reset();
            showAppScreen();
            loadNotes();
        } else {
            errorMsg.textContent = data.message || 'Signup failed';
        }
    } catch (error) {
        errorMsg.textContent = 'Network error. Please try again.';
    } finally {
        loading.style.display = 'none';
    }
});

// Logout
logoutBtn.addEventListener('click', () => {
    currentToken = null;
    localStorage.removeItem('authToken');
    showLoginScreen();
    loginForm.reset();
    signupForm.reset();
});

// ===== NOTES MANAGEMENT =====

// Load notes from API
async function loadNotes() {
    try {
        const response = await fetch(`${API_URL}/notes`, {
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        if (response.ok) {
            const notes = await response.json();
            console.log('Is array?:', Array.isArray(notes));  // ADD THIS LINE
            renderNotes(notes);
        } else {
            console.error('Failed to load notes');
        }
    } catch (error) {
        console.error('Error loading notes:', error);
    }
}


// Render notes to the grid
function renderNotes(notes) {
    notesGrid.innerHTML = '';

    if (notes.length === 0) {
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';

    notes.forEach(note => {
        const noteEl = document.createElement('div');
        noteEl.className = 'note';
        noteEl.innerHTML = `
    <div class="note-date">${formatDate(note.createdAt)}</div>
    <div class="note-content">${escapeHtml(note.content)}</div>
    <div class="note-actions">
        <button class="edit-btn" onclick="openEditModal('${note.id}', '${escapeAttribute(note.content)}')">Edit</button>
        <button class="delete-btn" onclick="deleteNote('${note.id}')">Delete</button>
    </div>
`;
        notesGrid.appendChild(noteEl);
    });
}

// Add a new note
addNoteBtn.addEventListener('click', addNote);
noteInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        addNote();
    }
});

async function addNote() {
    const content = noteInput.value.trim();

    if (!content) return;

    try {
        const response = await fetch(`${API_URL}/notes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({ content })
        });

        if (response.ok) {
            noteInput.value = '';
            noteInput.focus();
            loadNotes();
        } else {
            console.error('Failed to add note');
        }
    } catch (error) {
        console.error('Error adding note:', error);
    }
}

// Open edit modal
function openEditModal(noteId, content) {
    editingNoteId = noteId;
    editTextarea.value = content;
    modal.style.display = 'block';
    editTextarea.focus();
}

// Close modal
function closeEditModal() {
    modal.style.display = 'none';
    editingNoteId = null;
}

// Save edited note
saveNoteBtn.addEventListener('click', async () => {
    const content = editTextarea.value.trim();

    if (!content || !editingNoteId) return;

    try {
        const response = await fetch(`${API_URL}/notes/${editingNoteId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify({ content })
        });

        if (response.ok) {
            closeEditModal();
            loadNotes();
        } else {
            console.error('Failed to update note');
        }
    } catch (error) {
        console.error('Error updating note:', error);
    }
});

// Close modal on outside click
modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        closeEditModal();
    }
});

// Delete note
async function deleteNote(noteId) {
    if (!confirm('Are you sure you want to delete this note?')) return;

    try {
        const response = await fetch(`${API_URL}/notes/${noteId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });

        if (response.ok) {
            loadNotes();
        } else {
            console.error('Failed to delete note');
        }
    } catch (error) {
        console.error('Error deleting note:', error);
    }
}

// ===== UTILITY FUNCTIONS =====

function showLoginScreen() {
    authContainer.style.display = 'block';
    appContainer.style.display = 'none';
}

function showAppScreen() {
    authContainer.style.display = 'none';
    appContainer.style.display = 'block';
    noteInput.focus();
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttribute(text) {
    return text.replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}
