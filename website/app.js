// Global state
let allStartups = [];
let filteredStartups = [];
let categories = new Set();
let halls = new Set();

// Initialize app
function initializeApp() {
    allStartups = startupsData;
    filteredStartups = [...allStartups];

    // Extract unique categories and halls
    allStartups.forEach(startup => {
        if (startup.category && startup.category !== 'Error' && startup.category !== 'No Data') {
            categories.add(startup.category);
        }
        if (startup.hall) {
            halls.add(startup.hall);
        }
    });

    // Populate filters
    populateFilters();

    // Render initial startups
    renderStartups();

    // Setup event listeners
    setupEventListeners();

    // Update stats
    updateStats();
}

// Populate filter dropdowns
function populateFilters() {
    const categoryFilter = document.getElementById('categoryFilter');
    const hallFilter = document.getElementById('hallFilter');

    // Sort and add categories
    Array.from(categories).sort().forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categoryFilter.appendChild(option);
    });

    // Sort and add halls
    Array.from(halls).sort((a, b) => {
        const numA = parseInt(a);
        const numB = parseInt(b);
        return numA - numB;
    }).forEach(hall => {
        const option = document.createElement('option');
        option.value = hall;
        option.textContent = `Hall ${hall}`;
        hallFilter.appendChild(option);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Search
    document.getElementById('searchInput').addEventListener('input', handleSearch);

    // Filters
    document.getElementById('categoryFilter').addEventListener('change', applyFilters);
    document.getElementById('hallFilter').addEventListener('change', applyFilters);
    document.getElementById('resetFilters').addEventListener('click', resetFilters);

    // Modal
    const modal = document.getElementById('modal');
    const closeBtn = document.querySelector('.close-btn');

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Handle search
function handleSearch(e) {
    const query = e.target.value.toLowerCase();

    if (query.trim() === '') {
        applyFilters();
        return;
    }

    filteredStartups = allStartups.filter(startup => {
        const searchText = [
            startup.name,
            startup.category,
            startup.summary,
            ...(startup.tags || []),
            ...(startup.key_offerings || [])
        ].join(' ').toLowerCase();

        return searchText.includes(query);
    });

    renderStartups();
}

// Apply filters
function applyFilters() {
    const searchQuery = document.getElementById('searchInput').value.toLowerCase();
    const categoryValue = document.getElementById('categoryFilter').value;
    const hallValue = document.getElementById('hallFilter').value;

    filteredStartups = allStartups.filter(startup => {
        // Search filter
        if (searchQuery) {
            const searchText = [
                startup.name,
                startup.category,
                startup.summary,
                ...(startup.tags || []),
                ...(startup.key_offerings || [])
            ].join(' ').toLowerCase();

            if (!searchText.includes(searchQuery)) return false;
        }

        // Category filter
        if (categoryValue && startup.category !== categoryValue) {
            return false;
        }

        // Hall filter
        if (hallValue && startup.hall !== hallValue) {
            return false;
        }

        return true;
    });

    renderStartups();
}

// Reset filters
function resetFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('categoryFilter').value = '';
    document.getElementById('hallFilter').value = '';

    filteredStartups = [...allStartups];
    renderStartups();
}

// Render startups
function renderStartups() {
    const grid = document.getElementById('startupsGrid');
    const noResults = document.getElementById('noResults');
    const resultsCount = document.getElementById('resultsCount');

    // Update count
    resultsCount.textContent = `${filteredStartups.length} startup${filteredStartups.length !== 1 ? 's' : ''} found`;

    // Clear grid
    grid.innerHTML = '';

    if (filteredStartups.length === 0) {
        grid.style.display = 'none';
        noResults.style.display = 'block';
        return;
    }

    grid.style.display = 'grid';
    noResults.style.display = 'none';

    // Render each startup
    filteredStartups.forEach((startup, index) => {
        const card = createStartupCard(startup, index);
        grid.appendChild(card);
    });
}

// Create startup card
function createStartupCard(startup, index) {
    const card = document.createElement('div');
    card.className = 'startup-card';
    card.style.animationDelay = `${index * 0.05}s`;

    // Determine category badge color
    let categoryClass = 'category-badge';

    const logoHtml = startup.logo_url ?
        `<img src="${startup.logo_url}" alt="${startup.name}" class="startup-logo" onerror="this.style.display='none'">` :
        '';

    const summaryText = startup.summary && startup.summary !== 'No information available' && startup.summary !== 'Failed to process with AI'
        ? startup.summary
        : 'No summary available for this startup.';

    const tagsHtml = startup.tags && startup.tags.length > 0
        ? `<div class="startup-tags">
            ${startup.tags.slice(0, 5).map(tag => `<span class="tag">${tag}</span>`).join('')}
           </div>`
        : '';

    const websiteHtml = startup.website
        ? `<a href="${startup.website}" target="_blank" class="startup-link" onclick="event.stopPropagation()">
            Visit Website →
           </a>`
        : '';

    card.innerHTML = `
        <div class="startup-header">
            ${logoHtml}
            <span class="hall-badge">Hall ${startup.hall || 'TBD'}</span>
        </div>
        <h3 class="startup-name">${startup.name}</h3>
        <span class="${categoryClass}">${startup.category || 'Uncategorized'}</span>
        <p class="startup-summary">${summaryText}</p>
        ${tagsHtml}
        ${websiteHtml}
    `;

    card.addEventListener('click', () => showStartupDetails(startup));

    return card;
}

// Show startup details in modal
function showStartupDetails(startup) {
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modalBody');

    const keyOfferingsHtml = startup.key_offerings && startup.key_offerings.length > 0
        ? `<div style="margin-top: 24px;">
            <h3 style="color: var(--primary); margin-bottom: 12px;">Key Offerings</h3>
            <ul style="list-style: none; padding: 0;">
                ${startup.key_offerings.map(offering => `
                    <li style="padding: 8px 0; padding-left: 24px; position: relative;">
                        <span style="position: absolute; left: 0; color: var(--primary);">✓</span>
                        ${offering}
                    </li>
                `).join('')}
            </ul>
           </div>`
        : '';

    const tagsHtml = startup.tags && startup.tags.length > 0
        ? `<div style="margin-top: 24px;">
            <h3 style="color: var(--primary); margin-bottom: 12px;">Technologies</h3>
            <div class="startup-tags">
                ${startup.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
            </div>
           </div>`
        : '';

    const websiteHtml = startup.website
        ? `<a href="${startup.website}" target="_blank" style="color: var(--primary); text-decoration: none; margin-top: 16px; display: inline-block;">
            🌐 Visit Website
           </a>`
        : '';

    const aboutPageHtml = startup.about_page_url && startup.about_page_url !== startup.website
        ? `<a href="${startup.about_page_url}" target="_blank" style="color: var(--secondary); text-decoration: none; margin-left: 16px; display: inline-block;">
            ℹ️ About Page
           </a>`
        : '';

    const linkedinHtml = startup.linkedin_url
        ? `<a href="${startup.linkedin_url}" target="_blank" style="color: #0077b5; text-decoration: none; margin-left: 16px; display: inline-block;">
            💼 LinkedIn
           </a>`
        : '';

    const summaryText = startup.summary && startup.summary !== 'No information available' && startup.summary !== 'Failed to process with AI'
        ? startup.summary
        : 'No detailed information available for this startup.';

    modalBody.innerHTML = `
        <div style="text-align: center; margin-bottom: 32px;">
            ${startup.logo_url ? `<img src="${startup.logo_url}" alt="${startup.name}" style="width: 100px; height: 100px; object-fit: contain; background: white; padding: 12px; border-radius: 16px; margin-bottom: 16px;">` : ''}
            <h2 style="font-size: 2rem; margin-bottom: 8px;">${startup.name}</h2>
            <span class="hall-badge" style="font-size: 1rem; padding: 8px 16px;">Hall ${startup.hall || 'TBD'} ${startup.space_sqm ? `• ${startup.space_sqm} sqm` : ''}</span>
        </div>
        
        <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 24px;">
            <span class="category-badge" style="font-size: 0.95rem; padding: 6px 16px;">${startup.category || 'Uncategorized'}</span>
            ${startup.confidence ? `<span style="margin-left: 12px; color: var(--gray-light); font-size: 0.85rem;">Confidence: ${startup.confidence}</span>` : ''}
        </div>
        
        <div style="margin-bottom: 24px;">
            <h3 style="color: var(--primary); margin-bottom: 12px;">About</h3>
            <p style="color: var(--gray-light); line-height: 1.8;">${summaryText}</p>
        </div>
        
        ${keyOfferingsHtml}
        ${tagsHtml}
        
        <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid rgba(255,255,255,0.1);">
            ${websiteHtml}
            ${aboutPageHtml}
            ${linkedinHtml}
        </div>
        
        <div style="margin-top: 24px; padding: 16px; background: rgba(99,102,241,0.1); border-left: 4px solid var(--primary); border-radius: 8px;">
            <p style="font-size: 0.9rem; color: var(--gray-light); margin: 0;">
                <strong>Note:</strong> Key person/presenter information is being collected and will be added soon.
            </p>
        </div>
    `;

    modal.style.display = 'block';
}

// Update stats
function updateStats() {
    document.getElementById('totalStartups').textContent = allStartups.length;
    document.getElementById('totalCategories').textContent = categories.size;
    document.getElementById('totalHalls').textContent = halls.size;
}

// Export for use in HTML
window.addEventListener('DOMContentLoaded', () => {
    // App will be initialized when data is loaded via fetch in HTML
});
