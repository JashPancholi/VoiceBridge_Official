
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const errorMessage = document.getElementById('errorMessage');

uploadBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', handleUpload);

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
