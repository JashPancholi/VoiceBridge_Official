// Attach submit event handler to the registration form to handle user registration
document.getElementById('registrationForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Stop default form submission

    // Get input values from the registration form
    const fullname = document.getElementById('fullname').value.trim();
    const email = document.getElementById('email').value.trim();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const confirmPassword = document.getElementById('confirm-password').value.trim();
    const terms = document.getElementById('terms').checked;

    let errors = [];

    // Username validation
    if (username.length < 3 || username.length > 15 || !/^[a-zA-Z0-9]+$/.test(username)) {
        errors.push("Username must be 3-15 characters long and can only contain letters and numbers.");
    }

    // Password validation
    if (password.length < 8) {
        errors.push("Password must be at least 8 characters long.");
    }
    if (password !== confirmPassword) {
        errors.push("Passwords do not match.");
    }

    // Email validation (basic check)
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errors.push("Enter a valid email address.");
    }

    // Terms validation
    if (!terms) {
        errors.push("You must agree to the Terms & Conditions.");
    }
    
    // Reference the error message container and clear previous errors
    const errorContainer = document.getElementById('errorContainer');
    if (!errorContainer) return;

    errorContainer.innerHTML = ''; // Clear previous errors

    // If there are validation errors, display them and exit
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

    // --- Send registration data to the server ---
    try {
        const response = await fetch("/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ fullname, email, username, password })
        });

        const data = await response.json();
        // If registration fails, display server-provided error message
        if (!data.success) {
            const errorBox = document.createElement('div');
            errorBox.classList.add('errorBox');
            errorBox.textContent = data.message;
            errorContainer.appendChild(errorBox);
            setTimeout(() => errorBox.remove(), 5000);
        } else {
            // On successful registration, alert user and redirect to login page
            alert("Registration successful!");
            window.location.href = "/login.html";
        }
    } catch (error) {
        // Handle network or unexpected errors
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
    }
});

