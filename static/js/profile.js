document.addEventListener("DOMContentLoaded", function () {
    // Profile picture upload functionality
    const uploadBtn = document.getElementById("upload-btn");
    const fileInput = document.getElementById("file-input");

    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener("click", function () {
            fileInput.click();
        });

        fileInput.addEventListener("change", function () {
            const file = fileInput.files[0];
            if (file) {
                const formData = new FormData();
                formData.append("profile_pic", file);
                fetch("/upload-profile-pic", {
                    method: "POST",
                    body: formData,
                })
                .then(response => response.json())
                .then(data => {
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
                console.log('Video history data:', videos);
                if (videos.error) {
                    alert(videos.error);
                    return;
                }

                videos.forEach(video => {
                    const item = document.createElement('div');
                    item.className = 'history-item';
                    
                    // Add thumbnail image to the history section
                    const thumbnail = document.createElement('img');
                    if (video.thumbnail_url) {
                        thumbnail.src = video.thumbnail_url;
                    } else {
                        thumbnail.src = '/static/placeholder-thumbnail.jpg';
                    }
                    thumbnail.alt = 'Video Thumbnail';
                    thumbnail.className = 'history-thumbnail';
                    item.appendChild(thumbnail);
                    
                    // Add filename text to the history section
                    const filename = document.createElement('p');
                    filename.textContent = video.original_filename;
                    item.appendChild(filename);
                    
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
}

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `${tab}-transcript`);
    });
}