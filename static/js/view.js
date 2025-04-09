function showTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
}

document.getElementById('videoPlayer').src = '/static/status/current.mp4';

function openModal(action) {
    document.getElementById('popupModal').style.display = "block";
    document.getElementById('actionType').value = action;
}

function closeModal() {
    document.getElementById('popupModal').style.display = "none";
}

document.getElementById('actionForm').onsubmit = async function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const actionType = formData.get('actionType');
    closeModal();
    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        document.getElementById('transcriptOutput').textContent = data.transcript || "";
        document.getElementById('translationOutput').textContent = data.translation || "";

        
        
        if (actionType === 'transcribe' && data.transcript) {
            showSuccess("📝 Transcription completed successfully!");
        } else if (actionType === 'translate' && data.translation) {
            showSuccess("🌐 Translation completed successfully!");
        } else {
            showError("Processing failed. Please try again.");
        }

    } catch (err) {
        console.error("Error:", err);
        showError("Something went wrong. Please check your input.");
    }
};


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



