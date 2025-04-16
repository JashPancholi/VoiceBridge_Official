document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Stop default form submission

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    let errors = [];

    // Username validation
    const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(username);
    const isUsername = /^[a-zA-Z0-9]{3,15}$/.test(username);
    
    if (!isEmail && !isUsername) {
        errors.push("Enter a valid username (3–15 alphanumeric characters) or email address.");
    }


    // Password validation
    if (password.length < 8) {
        errors.push("Password must be at least 8 characters long.");
    }

    // Reference the error message container and clear previous errors
    const errorContainer = document.getElementById('errorContainer');
    if (!errorContainer) return;

    errorContainer.innerHTML = ''; // Clear previous errors

    // If there are validation errors, display each error in its own box and exi
    if (errors.length > 0) {
        errors.forEach((error, index) => {
            setTimeout(() => {
                const errorBox = document.createElement('div');
                errorBox.classList.add('errorBox');
                errorBox.textContent = error;

                errorContainer.appendChild(errorBox);

                setTimeout(() => {
                    errorBox.remove();
                }, 5000);
            }, index * 200);
        });
        return;
    }
    
    
    // If validation passes, send login request to server
    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        
        // If login fails, display error message from server
        if (!data.success) {
            const errorBox = document.createElement('div');
            errorBox.classList.add('errorBox');
            errorBox.textContent = data.message;
            errorContainer.appendChild(errorBox);
            setTimeout(() => errorBox.remove(), 5000);
        } else {
            // On successful login, alert user and redirect to dashboard
            alert("Login successful!");
            window.location.href = "/dashboard.html";
        }
    } catch (error) {
        // Handle network or unexpected errors
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
    }
});
