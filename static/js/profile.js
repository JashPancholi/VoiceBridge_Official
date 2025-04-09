document.addEventListener("DOMContentLoaded", function () {
    const uploadBtn = document.getElementById("upload-btn");
    const fileInput = document.getElementById("file-input");

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
});
