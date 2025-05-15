
// Initialize AOS animations
document.addEventListener('DOMContentLoaded', function() {
  // Initialize AOS library if it exists
  if (typeof AOS !== 'undefined') {
    AOS.init({ 
      once: true,
      duration: 800,
      offset: 100
    });
  }

  // Toggle collapsible sections
  const collapsibles = document.querySelectorAll('.collapsible');
  
  collapsibles.forEach(function(collapsible) {
    collapsible.addEventListener('click', function() {
      const content = this.nextElementSibling;
      if (content.style.display === 'block' || content.style.display === '') {
        content.style.display = 'none';
      } else {
        content.style.display = 'block';
      }
    });
  });

  // MFA sections toggle
  const showOTPBtn = document.getElementById('show-otp-btn');
  const showQRBtn = document.getElementById('show-qr-btn');
  const mfaSection = document.getElementById('mfa-section');
  const qrSection = document.getElementById('qr-section');

  if (showOTPBtn && mfaSection) {
    showOTPBtn.addEventListener('click', function() {
      mfaSection.style.display = 'block';
      if (qrSection) qrSection.style.display = 'none';
    });
  }

  if (showQRBtn && qrSection) {
    showQRBtn.addEventListener('click', function() {
      qrSection.style.display = 'block';
      if (mfaSection) mfaSection.style.display = 'none';
    });
  }

  // Show care plan history
  const historyDropdowns = document.querySelectorAll('.history-dropdown');
  
  historyDropdowns.forEach(function(dropdown) {
    dropdown.addEventListener('change', function() {
      const residentId = this.getAttribute('data-resident-id');
      const selectedIndex = this.value;
      
      const allEntries = document.querySelectorAll(`[id^='plan-${residentId}-']`);
      allEntries.forEach(entry => entry.style.display = 'none');
      
      const selected = document.getElementById(`plan-${residentId}-${selectedIndex}`);
      if (selected) selected.style.display = 'block';
    });
  });

  // Auto-initialize the first option for care plan history dropdowns
  historyDropdowns.forEach(function(dropdown) {
    if (dropdown.options.length > 0) {
      const event = new Event('change');
      dropdown.dispatchEvent(event);
    }
  });

  // Handle form errors
  const errorMessage = document.getElementById('error-message');
  const formWithErrors = document.querySelector('form[data-has-error="true"]');
  
  if (errorMessage && formWithErrors) {
    errorMessage.style.display = 'block';
  }

  // Copy invite link to clipboard functionality
  const copyButtons = document.querySelectorAll('.copy-invite-btn');
  
  copyButtons.forEach(function(button) {
    button.addEventListener('click', function() {
      const linkElement = document.querySelector(this.getAttribute('data-target'));
      
      if (linkElement) {
        const textArea = document.createElement('textarea');
        textArea.value = linkElement.textContent || linkElement.value;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        // Show copied message
        const originalText = this.textContent;
        this.textContent = 'Copied!';
        setTimeout(() => {
          this.textContent = originalText;
        }, 2000);
      }
    });
  });
});

// Function to toggle login sections
function toggleLogins() {
  const section = document.getElementById("loginsSection");
  section.style.display = (section.style.display === "none" || section.style.display === "") ? "block" : "none";
}

// Function to toggle JWT logs
function toggleJwtLogs() {
  const section = document.getElementById("jwtSection");
  section.style.display = (section.style.display === "none" || section.style.display === "") ? "block" : "none";
}

// Function to toggle honeypot logs
function toggleHoneypot() {
  const section = document.getElementById("honeypotSection");
  section.style.display = (section.style.display === "none" || section.style.display === "") ? "block" : "none";
}

// Function to show OTP section in MFA
function showOTP() {
  const mfaSection = document.getElementById("mfa-section");
  const qrSection = document.getElementById("qr-section");
  
  if (mfaSection) mfaSection.style.display = "block";
  if (qrSection) qrSection.style.display = "none";
}

// Function to show QR section in MFA
function showQR() {
  const mfaSection = document.getElementById("mfa-section");
  const qrSection = document.getElementById("qr-section");
  
  if (qrSection) qrSection.style.display = "block";
  if (mfaSection) mfaSection.style.display = "none";
}

// Function to show selected care plan
function showSelectedCarePlan(selectElem, residentId) {
  const selectedIndex = selectElem.value;
  const allEntries = document.querySelectorAll(`[id^='plan-${residentId}-']`);
  allEntries.forEach(entry => entry.style.display = 'none');

  const selected = document.getElementById(`plan-${residentId}-${selectedIndex}`);
  if (selected) selected.style.display = 'block';
}
