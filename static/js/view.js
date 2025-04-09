function showTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
}

document.getElementById('videoPlayer').src = '/static/status/current.mp4';


function closeModal() {
    document.getElementById('popupModal').style.display = "none";
}

document.getElementById('actionForm').onsubmit = async function (e) {
    e.preventDefault();
    closeModal();
    startLoadingBar();

    const formData = new FormData(this);
    const actionType = formData.get('actionType');

    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

         // 🔄 Move here!

        document.getElementById('transcriptOutput').textContent = data.transcript || "";
        document.getElementById('translationOutput').textContent = data.translation || "";
        completeLoadingBar();
        
        if (actionType === 'transcribe' && data.transcript) {
            showSuccess("📝 Transcription completed successfully!");
            document.getElementById('saveTranscriptBtn').disabled = false;
            const transcriptBtn = document.getElementById('transcriptBtn');
            transcriptBtn.classList.remove('transcript-pending');
            transcriptBtn.classList.add('transcript-done');
            transcriptBtn.title = 'Transcript ready';
        } else if (actionType === 'translate' && data.translation) {
            showSuccess("🌐 Translation completed successfully!");
            const translateBtn = document.getElementById('translateBtn');
            translateBtn.classList.remove('translate-pending');
            translateBtn.classList.add('translate-done');
            translateBtn.title = 'Translation ready';
        } else {
            showError("Processing failed. Please try again.");
        }

    } catch (err) {
        completeLoadingBar();
        console.error("Error:", err);
        showError("Something went wrong. Please check your input.");
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('popupModal');
    modal.style.display = "none";
    const transcriptBtn = document.getElementById('transcriptBtn');
    const transcriptText = document.getElementById('transcriptOutput').textContent.trim();

    if (!transcriptText || transcriptText === 'No transcription yet.') {
        transcriptBtn.classList.add('transcript-pending');
        transcriptBtn.title = 'Transcript not ready';
    } else {
        transcriptBtn.classList.add('transcript-done');
        transcriptBtn.title = 'Transcript ready';

        // ✅ Enable save button if transcript is already there
        document.getElementById('saveTranscriptBtn').disabled = false;
    }

    const translateBtn = document.getElementById('translateBtn');
    const translationText = document.getElementById('translationOutput').textContent.trim();

    if (!translationText || translationText === 'No translation yet.') {
        translateBtn.classList.add('translate-pending');
        translateBtn.title = 'Translation not ready';
    } else {
        translateBtn.classList.add('translate-done');
        translateBtn.title = 'Translation ready';
    }

    document.getElementById('saveTranscriptBtn').addEventListener('click', saveTranscript);
});

document.getElementById('popupModal').style.display = "flex";

async function saveTranscript() {
    const transcript = document.getElementById('transcriptOutput').textContent.trim();
    const videoName = "current.mp4"; // Replace with dynamic value if available
    const username = "john_doe";     // Replace with actual logged-in user dynamically

    if (!transcript || transcript === 'No transcription yet.') {
        showError("Transcript is empty. Please transcribe the video first.");
        return;
    }

    try {
        const response = await fetch('/save_transcript', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                transcript: transcript,
                video_name: videoName,
                username: username
            })
        });

        const data = await response.json();

        if (data.status === "success") {
            showSuccess(data.message || "✅ Transcript saved successfully!");
        } else {
            showError(data.message || "❌ Failed to save transcript.");
        }
    } catch (error) {
        console.error("Error saving transcript:", error);
        showError("🚫 Error occurred while saving transcript.");
    }
}


function openModal(action) {
    const modal = document.getElementById('popupModal');
    modal.style.display = "flex"; // This ensures modal shows centered
    modal.style.alignItems = "center";     // In case it needs re-centering
    modal.style.justifyContent = "center";

    document.getElementById('actionType').value = action;

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
    }
}

function showSuccess(message) {
    const successContainer = document.getElementById('successContainer');
    const successBox = document.createElement('div');
    successBox.classList.add('successBox');
    successBox.textContent = message;
    successContainer.appendChild(successBox);
    setTimeout(() => successBox.remove(), 5000);
}

function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    if (!errorContainer) return;

    const errorBox = document.createElement('div');
    errorBox.classList.add('errorBox');
    errorBox.textContent = message;
    errorContainer.appendChild(errorBox);
    setTimeout(() => errorBox.remove(), 5000);
}

function startLoadingBar() {
    const bar = document.getElementById('loadBar');
    bar.style.width = '0%';

    let progress = 0;
    bar.interval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 5; // increases to simulate progression
            bar.style.width = progress + '%';
        }
    }, 200);
}

function completeLoadingBar() {
    const bar = document.getElementById('loadBar');
    clearInterval(bar.interval);
    bar.style.width = '100%';
    setTimeout(() => {
        bar.style.width = '0%';
    }, 1000);
}


