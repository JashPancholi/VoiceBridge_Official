// Get references to DOM elements for file input, upload button, and error message display
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const errorMessage = document.getElementById('errorMessage');


// When the upload button is clicked, trigger the hidden file input dialog
uploadBtn.addEventListener('click', () => fileInput.click());

// When a file is selected, handle the upload process
fileInput.addEventListener('change', handleUpload);


/**
 * Handles the file upload process:
 * - Validates the file type
 * - Sends the file to the server via POST
 * - Redirects to viewer on success
 * - Displays error messages on failure
 */
async function handleUpload() {
    const file = fileInput.files[0];

    if (file && file.type === 'video/mp4') {
        errorMessage.textContent = '';

        const formData = new FormData();
        formData.append('video', file);

        try {
            const response = await fetch('/upload_video', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (result.success) {
                // Redirect to viewer with filename as query param
                window.location.href = `/viewer.html?filename=${encodeURIComponent(result.filename)}`;
            } else {
                errorMessage.textContent = result.message || 'Upload failed.';
            }
        } catch (err) {
            console.error(err);
            errorMessage.textContent = 'An error occurred during upload.';
        }

    } else {
        errorMessage.textContent = 'Only .mp4 files are accepted.';
    }
}
