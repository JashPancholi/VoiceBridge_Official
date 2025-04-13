let activeOuterButton = null;

// Function to switch between tabs (transcript and translation)
function showTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
}

// Function to close the language selection modal
function closeModal() {
    document.getElementById('popupModal').style.display = "none";
}

// Handle form submission for transcription/translation
document.getElementById('actionForm').onsubmit = async function(e) {
    e.preventDefault();
    closeModal();
    startLoadingBar();

    const formData = new FormData(this);
    const actionType = formData.get('actionType');

    if (actionType === 'transcribe') {
        formData.set('actionType', 'transcribe');
    }
    
    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Update UI with results
        document.getElementById('transcriptOutput').textContent = data.transcript || "";
        document.getElementById('translationOutput').textContent = data.translation || "";
        
        completeLoadingBar();
        
        // Update UI elements based on results
        if (data.transcript) {
            showSuccess("📝 Transcription completed successfully!");
            updateButtonStatus('transcriptBtn', true);
        }
        
        if (data.translation) {
            showSuccess("🌐 Translation completed successfully!");
            updateButtonStatus('translateBtn', true);
        }
    } catch (err) {
        completeLoadingBar();
        console.error("Error:", err);
        showError("Something went wrong. Please check your input.");
    }finally {
        completeLoadingBar();
        if (activeOuterButton) {
            activeOuterButton.disabled = false;
            activeOuterButton = null;
        }
    }
};

// Update button status (visual feedback)
function updateButtonStatus(buttonId, isComplete) {
    const button = document.getElementById(buttonId);
    if (isComplete) {
        button.classList.remove(buttonId === 'transcriptBtn' ? 'transcript-pending' : 'translate-pending');
        button.classList.add(buttonId === 'transcriptBtn' ? 'transcript-done' : 'translate-done');
        button.title = buttonId === 'transcriptBtn' ? 'Transcript ready' : 'Translation ready';
    } else {
        button.classList.add(buttonId === 'transcriptBtn' ? 'transcript-pending' : 'translate-pending');
        button.classList.remove(buttonId === 'transcriptBtn' ? 'transcript-done' : 'translate-done');
        button.title = buttonId === 'transcriptBtn' ? 'Transcription in progress...' : 'Translation in progress...';
    }
}

// Show success messages
function showSuccess(message) {
    const successContainer = document.getElementById('successContainer');
    const successBox = document.createElement('div');
    successBox.classList.add('successBox');
    successBox.textContent = message;
    successContainer.appendChild(successBox);
    setTimeout(() => successBox.remove(), 5000);
}

// Show error messages
function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    if (!errorContainer) return;
    const errorBox = document.createElement('div');
    errorBox.classList.add('errorBox');
    errorBox.textContent = message;
    errorContainer.appendChild(errorBox);
    setTimeout(() => errorBox.remove(), 5000);
}

// Show info messages
function showInfo(message) {
    const infoContainer = document.getElementById('successContainer');
    const infoBox = document.createElement('div');
    infoBox.classList.add('infoBox');
    infoBox.textContent = message;
    infoContainer.appendChild(infoBox);
    setTimeout(() => infoBox.remove(), 5000);
}

// Open the language selection modal
function openModal(action) {
    const modal = document.getElementById('popupModal');
    modal.style.display = "flex";
    modal.style.alignItems = "center";
    modal.style.justifyContent = "center";

    // grab and disable the clicked outer button
    const clickedButton = event?.target;
    if (clickedButton && clickedButton.tagName === 'BUTTON') {
        clickedButton.disabled = true;
        activeOuterButton = clickedButton;
    }

    document.getElementById('actionType').value = action;

    const voiceOption = document.getElementById('VoiceOption');
    if (voiceOption) voiceOption.style.display = 'none';
    
    if (action === 'transcribe') {
        const transcriptBtn = document.getElementById('transcriptBtn');
        transcriptBtn.classList.add('transcript-pending');
        transcriptBtn.classList.remove('transcript-done');
        transcriptBtn.title = 'Transcription in progress...';
    } else if (action === 'translate') {
        const translateBtn = document.getElementById('translateBtn');
        translateBtn.classList.add('translate-pending');
        translateBtn.classList.remove('translate-done');
        translateBtn.title = 'Translation in progress...';
        if (voiceOption) voiceOption.style.display = 'block';
    }
}

// Start the loading bar animation
function startLoadingBar() {
    const bar = document.getElementById('loadBar');
    bar.style.width = '0%';
    let progress = 0;
    bar.interval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 5;
            bar.style.width = progress + '%';
        }
    }, 200);
}

// Complete the loading bar animation
function completeLoadingBar() {
    const bar = document.getElementById('loadBar');
    clearInterval(bar.interval);
    bar.style.width = '100%';
    setTimeout(() => {
        bar.style.width = '0%';
    }, 1000);
}




function uploadReplacedVideo(input) {
    const file = input.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.mp4')) {
        showError("❌ Only .mp4 files are allowed.");
        return;
    }

    const formData = new FormData();
    formData.append('video', file);

    fetch('/upload_video', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess("✅ Video replaced successfully!");
            // Optionally: reload video preview
            location.reload(); // or dynamically update the video preview
        } else {
            showError("❌ " + data.message);
        }
    })
    .catch(error => {
        console.error('Upload failed:', error);
        showError("❌ Upload failed.");
    });
}

// Initialize video source when page loads
window.onload = function() {
    const videoPlayer = document.getElementById('videoPlayer');
    if (videoPlayer) {
        videoPlayer.src = '/static/status/current.mp4';
    }
};
