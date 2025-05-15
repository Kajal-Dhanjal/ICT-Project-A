/**
 * Admin Dashboard JavaScript
 * Handles interactive elements and log display functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Toggle log sections functionality
    setupCollapsibleSections();
    
    // Copy invite link functionality
    setupCopyButtons();
    
    // Add special styling to rows
    highlightTableRows();
});

/**
 * Sets up collapsible section functionality
 */
function setupCollapsibleSections() {
    const collapsibles = document.querySelectorAll('.collapsible');
    
    collapsibles.forEach(function(collapsible) {
        collapsible.addEventListener('click', function() {
            const content = this.nextElementSibling;
            const toggleIcon = this.querySelector('.toggle-icon');
            
            // Toggle display
            if (content.style.display === 'block') {
                content.style.display = 'none';
                if (toggleIcon) toggleIcon.textContent = '▼';
            } else {
                content.style.display = 'block';
                if (toggleIcon) toggleIcon.textContent = '▲';
            }
        });
    });
}

/**
 * Sets up the copy button functionality
 */
function setupCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-invite-btn');
    
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const targetSelector = this.getAttribute('data-target');
            const targetElement = document.querySelector(targetSelector);
            
            if (targetElement) {
                // Select the text in the target element
                targetElement.select();
                
                try {
                    // Execute copy command
                    document.execCommand('copy');
                    
                    // Visual feedback
                    const originalText = this.textContent;
                    this.textContent = 'Copied!';
                    setTimeout(() => {
                        this.textContent = originalText;
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy: ', err);
                }
            }
        });
    });
}

/**
 * Adds hover effects to table rows
 */
function highlightTableRows() {
    const tableRows = document.querySelectorAll('tbody tr');
    
    tableRows.forEach(function(row) {
        row.addEventListener('mouseenter', function() {
            if (this.classList.contains('error-row')) {
                this.style.backgroundColor = 'rgba(231, 76, 60, 0.15)';
            } else if (this.classList.contains('success-row')) {
                this.style.backgroundColor = 'rgba(40, 167, 69, 0.15)';
            } else if (this.classList.contains('honeypot-row')) {
                this.style.backgroundColor = 'rgba(243, 156, 18, 0.15)';
            } else {
                this.style.backgroundColor = 'rgba(0, 78, 124, 0.05)';
            }
        });
        
        row.addEventListener('mouseleave', function() {
            if (this.classList.contains('error-row')) {
                this.style.backgroundColor = 'rgba(231, 76, 60, 0.05)';
            } else if (this.classList.contains('success-row')) {
                this.style.backgroundColor = 'rgba(40, 167, 69, 0.05)';
            } else if (this.classList.contains('honeypot-row')) {
                this.style.backgroundColor = 'rgba(243, 156, 18, 0.05)';
            } else {
                this.style.backgroundColor = '';
            }
        });
    });
}

// Global functions for collapsible sections
function toggleLogins() {
    toggleSection('loginsSection');
}

function toggleJwtLogs() {
    toggleSection('jwtSection');
}

function toggleHoneypot() {
    toggleSection('honeypotSection');
}

function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const header = section.previousElementSibling;
    const toggleIcon = header.querySelector('.toggle-icon');
    
    if (section.style.display === 'block') {
        section.style.display = 'none';
        if (toggleIcon) toggleIcon.textContent = '▼';
    } else {
        section.style.display = 'block';
        if (toggleIcon) toggleIcon.textContent = '▲';
    }
}