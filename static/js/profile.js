// Wait until the DOM is fully loaded before attaching event handlers
document.addEventListener("DOMContentLoaded", function () {
    
    // --- Profile picture upload functionality ---
    // Get references to upload button and file input elements    const uploadBtn = document.getElementById("upload-btn");
    const fileInput = document.getElementById("file-input");

    // If both upload button and file input exist, set up event listeners
    if (uploadBtn && fileInput) {
        // When upload button is clicked, trigger the hidden file input dialog
        uploadBtn.addEventListener("click", function () {
            fileInput.click();
        });

        // When a file is selected, upload the profile picture to the server
        fileInput.addEventListener("change", function () {
            const file = fileInput.files[0];
            if (file) {
                const formData = new FormData();
                formData.append("profile_pic", file);

                // Send the selected file to the server via POST request
                fetch("/upload-profile-pic", {
                    method: "POST",
                    body: formData,
                })
                .then(response => response.json())
                .then(data => {
                    // If upload is successful, update the profile picture on the page
                    if (data.success) {
                        document.getElementById("profile-pic").src = data.profile_pic_url;
                    } else {
                        alert("Error updating profile picture.");
                    }
                });
            }
        });
    }

    // Video history functionality
    const historyList = document.querySelector('.history-list');
    
    if (historyList) {
        // Fetch video history from the backend
        fetch('/get_video_history')
            .then(response => response.json())
            .then(videos => {
                 // If there's an error, alert the user
                console.log('Video history data:', videos);
                if (videos.error) {
                    alert(videos.error);
                    return;
                }
                // If history is empty, display a message
                if (videos.length === 0) {
                    const emptyMsg = document.createElement('div');
                    emptyMsg.className = 'empty-history-message';
                    emptyMsg.innerHTML = `<span>🕳️</span>
                        <p>Your history is empty.<br>Start uploading videos to see them here!</p>`;
                    historyList.appendChild(emptyMsg);
                    return;
                }
                // Otherwise, render each video in the history list
                videos.forEach(video => {
                    const item = document.createElement('div');
                    item.className = 'history-item';
                    
                    // Add thumbnail image to the history section
                    const thumbnail = document.createElement('img');
                    thumbnail.src = '/static/thmb/default_thumbnail.png'; 
                    thumbnail.alt = 'Video Thumbnail';
                    thumbnail.className = 'history-thumbnail';
                    item.appendChild(thumbnail);
                    
                    // Add filename text to the history section
                    const filename = document.createElement('p');
                    filename.textContent = video.original_filename;
                    item.appendChild(filename);
                    
                    // Add source and target languages to the history section
                    const languageInfo = document.createElement('p');
                    languageInfo.className = 'history-language-info';
                    languageInfo.textContent = `From ${video.source_language} to ${video.target_language}`;
                    item.appendChild(languageInfo);

                    // Set up the click event for opening the modal
                    item.style.cursor = 'pointer';
                    item.onclick = () => openModal(video);
                    
                    historyList.appendChild(item);
                });
            })
            .catch(error => console.error('Error fetching video history:', error));
    }

    // Set up tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-btn');
    if (tabButtons.length > 0) {
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => switchTab(btn.dataset.tab));
        });
    }

    // Set up modal close functionality
    const closeButton = document.querySelector('#content-modal .close');
    if (closeButton) {
        closeButton.onclick = () => {
            document.getElementById('content-modal').style.display = 'none';
            // Stop video playback when modal is closed
            const videoPlayer = document.getElementById('history-video');
            if (videoPlayer) {
                videoPlayer.pause();
                videoPlayer.src = '';
            }
        };
    }
});
//Open Modal for viewing history data in dept - final O/P aling with video in modal
function openModal(video) {
    console.log('Opening modal for video:', video);
    const modal = document.getElementById('content-modal');
    if (!modal) {
        console.error('Modal element not found');
        return;
    }
    
    modal.style.display = 'block';
    
    const videoPlayer = document.getElementById('history-video');
    if (!videoPlayer) {
        console.error('Video player element not found');
        return;
    }
    
    // Use the translated_video_id to construct the video URL
    if (video.translated_video_id) {
        console.log(`Setting video source to: /video/${video.translated_video_id}`);
        videoPlayer.src = `/video/${video.translated_video_id}`;
    } else {
        console.warn('No video ID found for this history item');
        videoPlayer.src = '';
    }
    
    // Set the transcript texts
    const originalTranscript = document.getElementById('original-transcript');
    const translatedTranscript = document.getElementById('translated-transcript');
    
    if (originalTranscript) {
        originalTranscript.textContent = video.original_text || 'No original transcript available';
    }
    
    if (translatedTranscript) {
        translatedTranscript.textContent = video.translated_text || 'No translated transcript available';
    }
    
    // Set default tab to original
    switchTab('original');
    
    // Update modal title with original filename
    const modalTitle = document.getElementById('modal-title');
    if (modalTitle) {
        modalTitle.textContent = video.original_filename;
    }
    const languageDisplay = document.getElementById('modal-language-info');
    if (languageDisplay) {
       languageDisplay.textContent = `Language: ${video.source_language} → ${video.target_language}`;
    }
}

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `${tab}-transcript`);
    });
}