// Global state variables for Library Explorer
let currentLibraryPage = 1;
let currentLibraryBook = 'All';
let librarySearchTimeout = null;

// On Page Load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Library Collections list and load initial hadiths
    initLibraryBooks();
    loadLibraryData();
});

// Tab Switcher
function switchTab(tabName) {
    // Toggle active classes on buttons
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`nav-${tabName}`).classList.add('active');
    
    // Toggle active classes on content sections
    document.querySelectorAll('.tab-content').forEach(section => section.classList.remove('active'));
    document.getElementById(`${tabName}-section`).classList.add('active');
}

// Suggested Query Click Handler
function useQuery(text) {
    const input = document.getElementById('chat-input');
    input.value = text;
    // Switch to chat tab if not active
    switchTab('chat');
    // Submit form
    document.getElementById('chat-form').requestSubmit();
}

// ==========================================================================
// CHAT BOT MODULE
// ==========================================================================

async function handleChatSubmit(event) {
    event.preventDefault();
    
    const inputEl = document.getElementById('chat-input');
    const submitBtn = document.getElementById('chat-submit-btn');
    const messagesEl = document.getElementById('chat-messages');
    const loaderEl = document.getElementById('chat-loading');
    
    const query = inputEl.value.trim();
    if (!query) return;
    
    // Add user message to UI
    appendUserMessage(query);
    inputEl.value = '';
    
    // Disable inputs
    inputEl.disabled = true;
    submitBtn.disabled = true;
    loaderEl.classList.remove('hidden');
    messagesEl.scrollTop = messagesEl.scrollHeight;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: query, count: 5 })
        });
        
        if (!response.ok) {
            throw new Error(`Server returned error status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove loading state
        loaderEl.classList.add('hidden');
        inputEl.disabled = false;
        submitBtn.disabled = false;
        inputEl.focus();
        
        // Append Bot Response
        appendBotResponse(data.results);
        
    } catch (error) {
        console.error("Chat API error:", error);
        loaderEl.classList.add('hidden');
        inputEl.disabled = false;
        submitBtn.disabled = false;
        
        appendSystemError("Apologies, I encountered an issue retrieving similar Hadiths from the database. Please verify the backend server is running and try again.");
    }
    
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function appendUserMessage(text) {
    const messagesEl = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user-message';
    msgDiv.innerHTML = `
        <div class="message-avatar"><i class="fa-solid fa-user"></i></div>
        <div class="message-content">
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    messagesEl.appendChild(msgDiv);
}

function appendSystemError(text) {
    const messagesEl = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message system-message';
    msgDiv.innerHTML = `
        <div class="message-avatar" style="background-color: #8b0000;"><i class="fa-solid fa-circle-exclamation"></i></div>
        <div class="message-content" style="background-color: #fce8e6; border-left: 3px solid #8b0000; color: #8b0000;">
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    messagesEl.appendChild(msgDiv);
}

function appendBotResponse(results) {
    const messagesEl = document.getElementById('chat-messages');
    const botMsgDiv = document.createElement('div');
    botMsgDiv.className = 'message bot-message';
    
    let hadithCardsHtml = '';
    
    if (!results || results.length === 0) {
        hadithCardsHtml = '<p>No similar Hadiths were found matching your query in the corpus.</p>';
    } else {
        hadithCardsHtml = `<p>I have scanned the corpus and found <strong>${results.length}</strong> highly relevant matches using semantic matching:</p>`;
        
        results.forEach((h, index) => {
            const gradeText = h.english_grade ? `Grade: ${h.english_grade}` : 'Grade info unavailable';
            const distancePercent = Math.max(0, Math.min(100, Math.round((1 - h.distance) * 100)));
            const matchTag = `Semantic Similarity: ${distancePercent}%`;
            
            // Build unique IDs for collapse panels
            const toggleId = `toggle-chat-${h.id}-${index}`;
            const panelId = `panel-chat-${h.id}-${index}`;
            
            hadithCardsHtml += `
                <div class="hadith-result-card">
                    <div class="hadith-result-header">
                        <span>#${h.id + 1} (${h.book} - Hadith No. ${h.hadith_number})</span>
                        <span class="match-badge" style="color: var(--color-gold-deep);">${matchTag}</span>
                    </div>
                    <div class="hadith-result-body">
                        <div class="hadith-arabic">${h.arabic_hadith}</div>
                        <div class="hadith-english"><strong>English:</strong> ${h.english_hadith}</div>
                        <div class="hadith-urdu" lang="ur"><strong>اردو:</strong> ${h.urdu_hadith}</div>
                        
                        <div class="hadith-meta-footer">
                            <span>Chapter: ${h.chapter_english} | Section: ${h.section_english}</span>
                            <span class="hadith-grade">${gradeText}</span>
                        </div>
                    </div>
                    
                    <!-- Scholarly Commentary Section -->
                    <button class="explanation-toggle-btn" id="${toggleId}" onclick="toggleChatExplanation('${panelId}', '${toggleId}')">
                        <i class="fa-solid fa-angle-down"></i> View Scholarly Commentary & Explanation
                    </button>
                    <div class="explanation-content-panel" id="${panelId}">
                        <div class="explanation-title">${escapeHtml(h.explanation.title)}</div>
                        <div class="explanation-intro">${escapeHtml(h.explanation.introduction)}</div>
                        <ul class="explanation-lessons">
                            ${h.explanation.lessons.map(lesson => `<li>${escapeHtml(lesson)}</li>`).join('')}
                        </ul>
                        <div class="explanation-scholarly">
                            <strong>Scholarly Note:</strong> ${escapeHtml(h.explanation.scholarly_commentary)}
                        </div>
                    </div>
                </div>
            `;
        });
    }
    
    botMsgDiv.innerHTML = `
        <div class="message-avatar"><i class="fa-solid fa-dharmachakra"></i></div>
        <div class="message-content" style="width: 100%;">
            ${hadithCardsHtml}
        </div>
    `;
    
    messagesEl.appendChild(botMsgDiv);
}

function toggleChatExplanation(panelId, buttonId) {
    const panel = document.getElementById(panelId);
    const btn = document.getElementById(buttonId);
    
    if (panel.style.display === 'block') {
        panel.style.display = 'none';
        btn.innerHTML = `<i class="fa-solid fa-angle-down"></i> View Scholarly Commentary & Explanation`;
    } else {
        panel.style.display = 'block';
        btn.innerHTML = `<i class="fa-solid fa-angle-up"></i> Hide Commentary & Explanation`;
    }
}

// ==========================================================================
// CORPUS EXPLORER MODULE
// ==========================================================================

async function initLibraryBooks() {
    const listEl = document.getElementById('library-book-tabs');
    try {
        const response = await fetch('/api/books');
        const books = await response.json();
        
        listEl.innerHTML = '';
        books.forEach(b => {
            const btn = document.createElement('button');
            btn.className = `book-tab-btn ${b.id === currentLibraryBook ? 'active' : ''}`;
            btn.id = `book-tab-${b.id}`;
            btn.onclick = () => selectLibraryBook(b.id);
            btn.innerHTML = `
                <span>${escapeHtml(b.name)}</span>
                <span class="book-badge">${b.count.toLocaleString()}</span>
            `;
            listEl.appendChild(btn);
        });
    } catch (error) {
        console.error("Error loading books list:", error);
        listEl.innerHTML = '<div style="color: var(--color-gold-deep); font-size:12px;">Failed to load book filters.</div>';
    }
}

function selectLibraryBook(bookId) {
    currentLibraryBook = bookId;
    
    // Toggle active class in UI
    document.querySelectorAll('.book-tab-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById(`book-tab-${bookId}`);
    if (activeBtn) activeBtn.classList.add('active');
    
    // Reset page and reload
    currentLibraryPage = 1;
    loadLibraryData();
}

function handleLibrarySearch() {
    // Debounce search input
    clearTimeout(librarySearchTimeout);
    librarySearchTimeout = setTimeout(() => {
        currentLibraryPage = 1;
        loadLibraryData();
    }, 400);
}

async function loadLibraryData() {
    const gridEl = document.getElementById('library-results');
    const loadingEl = document.getElementById('library-loading');
    const countEl = document.getElementById('library-count-text');
    const paginationEl = document.getElementById('library-pagination');
    
    const searchVal = document.getElementById('library-search').value.trim();
    
    loadingEl.classList.remove('hidden');
    
    try {
        const url = `/api/explore?page=${currentLibraryPage}&book=${currentLibraryBook}&search=${encodeURIComponent(searchVal)}&per_page=10`;
        const response = await fetch(url);
        const data = await response.json();
        
        loadingEl.classList.add('hidden');
        
        // Update count
        countEl.textContent = `Found: ${data.total.toLocaleString()} Hadiths`;
        
        // Populate Grid
        gridEl.innerHTML = '';
        if (!data.hadiths || data.hadiths.length === 0) {
            gridEl.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-face-frown"></i>
                    <p>No Hadiths matching the criteria were found. Try modifying your search term.</p>
                </div>
            `;
            paginationEl.innerHTML = '';
            return;
        }
        
        data.hadiths.forEach(h => {
            const card = document.createElement('div');
            card.className = 'library-card';
            card.innerHTML = `
                <div class="library-card-header">
                    <span class="hadith-source">${escapeHtml(h.book)}</span>
                    <span class="hadith-ref-badge">Hadith #${h.hadith_number}</span>
                </div>
                <div class="library-card-body">
                    <div class="library-arabic">${h.arabic_hadith}</div>
                    <div class="library-english"><strong>English:</strong> ${h.english_hadith}</div>
                    
                    <!-- Hidden Translation/Commentary Panel (loaded dynamically) -->
                    <div class="library-expansion-panel" id="library-panel-${h.id}">
                        <div class="hadith-urdu" id="library-urdu-${h.id}" lang="ur">Translating text into Urdu...</div>
                        <div class="explanation-content-panel" id="library-exp-content-${h.id}" style="display: block; border-top: none; padding: 10px 0 0 0;">
                            <div class="explanation-title" id="library-exp-title-${h.id}">Generating insights...</div>
                            <div class="explanation-intro" id="library-exp-intro-${h.id}"></div>
                            <ul class="explanation-lessons" id="library-exp-lessons-${h.id}"></ul>
                            <div class="explanation-scholarly" id="library-exp-scholarly-${h.id}"></div>
                        </div>
                    </div>
                </div>
                <div class="library-card-footer">
                    <span class="hadith-grade">${h.english_grade ? `Grade: ${h.english_grade}` : 'Grade info unavailable'}</span>
                    <button class="toggle-details-btn" id="library-toggle-btn-${h.id}" onclick="toggleLibraryDetails(${h.id})">
                        <i class="fa-solid fa-language"></i> View Urdu & Explanation <i class="fa-solid fa-angle-down"></i>
                    </button>
                </div>
            `;
            gridEl.appendChild(card);
        });
        
        // Build Pagination
        buildLibraryPagination(data.page, data.pages);
        
    } catch (error) {
        console.error("Explore API error:", error);
        loadingEl.classList.add('hidden');
        gridEl.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <p>Failed to query the database. Check console for details.</p>
            </div>
        `;
        paginationEl.innerHTML = '';
    }
}

// Dynamically fetch translation and scholarly explanation for Library Cards
const loadedDetails = new Set();
async function toggleLibraryDetails(hadithId) {
    const panel = document.getElementById(`library-panel-${hadithId}`);
    const btn = document.getElementById(`library-toggle-btn-${hadithId}`);
    
    if (panel.classList.contains('active')) {
        panel.classList.remove('active');
        btn.innerHTML = `<i class="fa-solid fa-language"></i> View Urdu & Explanation <i class="fa-solid fa-angle-down"></i>`;
    } else {
        panel.classList.add('active');
        btn.innerHTML = `<i class="fa-solid fa-language"></i> Hide Urdu & Explanation <i class="fa-solid fa-angle-up"></i>`;
        
        // Fetch on demand if not already loaded
        if (!loadedDetails.has(hadithId)) {
            try {
                const response = await fetch(`/api/translate/${hadithId}`);
                const data = await response.json();
                
                // Display Urdu
                document.getElementById(`library-urdu-${hadithId}`).innerHTML = `<strong>اردو:</strong> ${data.urdu_hadith}`;
                
                // Display Commentary
                document.getElementById(`library-exp-title-${hadithId}`).innerText = data.explanation.title;
                document.getElementById(`library-exp-intro-${hadithId}`).innerText = data.explanation.introduction;
                
                const lessonsUl = document.getElementById(`library-exp-lessons-${hadithId}`);
                lessonsUl.innerHTML = data.explanation.lessons.map(l => `<li>${escapeHtml(l)}</li>`).join('');
                
                document.getElementById(`library-exp-scholarly-${hadithId}`).innerHTML = `<strong>Scholarly Note:</strong> ${escapeHtml(data.explanation.scholarly_commentary)}`;
                
                loadedDetails.add(hadithId);
            } catch (error) {
                console.error(`Error loading details for Hadith ${hadithId}:`, error);
                document.getElementById(`library-urdu-${hadithId}`).innerText = "Failure to retrieve Urdu translation.";
                document.getElementById(`library-exp-title-${hadithId}`).innerText = "Commentary Unavailable";
            }
        }
    }
}

// Build Pagination buttons with a slider window
function buildLibraryPagination(currentPage, totalPages) {
    const paginationEl = document.getElementById('library-pagination');
    paginationEl.innerHTML = '';
    
    if (totalPages <= 1) return;
    
    // Previous Button
    const prevBtn = document.createElement('button');
    prevBtn.className = 'page-btn nav-arrows';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => changeLibraryPage(currentPage - 1);
    prevBtn.innerHTML = '<i class="fa-solid fa-chevron-left"></i> Previous';
    paginationEl.appendChild(prevBtn);
    
    // Page index tags
    const maxButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);
    
    if (endPage - startPage + 1 < maxButtons) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }
    
    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = `page-btn`;
        firstBtn.innerText = '1';
        firstBtn.onclick = () => changeLibraryPage(1);
        paginationEl.appendChild(firstBtn);
        
        if (startPage > 2) {
            const ellipsis = document.createElement('span');
            ellipsis.innerText = '...';
            ellipsis.style.margin = '0 5px';
            paginationEl.appendChild(ellipsis);
        }
    }
    
    for (let p = startPage; p <= endPage; p++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `page-btn ${p === currentPage ? 'active' : ''}`;
        pageBtn.innerText = p.toString();
        pageBtn.onclick = () => changeLibraryPage(p);
        paginationEl.appendChild(pageBtn);
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const ellipsis = document.createElement('span');
            ellipsis.innerText = '...';
            ellipsis.style.margin = '0 5px';
            paginationEl.appendChild(ellipsis);
        }
        
        const lastBtn = document.createElement('button');
        lastBtn.className = `page-btn`;
        lastBtn.innerText = totalPages.toString();
        lastBtn.onclick = () => changeLibraryPage(totalPages);
        paginationEl.appendChild(lastBtn);
    }
    
    // Next Button
    const nextBtn = document.createElement('button');
    nextBtn.className = 'page-btn nav-arrows';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => changeLibraryPage(currentPage + 1);
    nextBtn.innerHTML = 'Next <i class="fa-solid fa-chevron-right"></i>';
    paginationEl.appendChild(nextBtn);
}

function changeLibraryPage(pageNumber) {
    currentLibraryPage = pageNumber;
    loadLibraryData();
    // Scroll explorer top to view
    document.querySelector('.library-controls').scrollIntoView({ behavior: 'smooth' });
}

// ==========================================================================
// UTILITIES
// ==========================================================================

function escapeHtml(text) {
    if (!text) return '';
    return text
        .toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
