// document.getElementById('registrationForm').addEventListener('submit', function(event) {
//     event.preventDefault(); // Stop form submission

//     const username = document.getElementById('username').value.trim();
//     const password = document.getElementById('password').value.trim();
//     const confirmPassword = document.getElementById('confirm-password').value.trim();
//     const terms = document.getElementById('terms').checked;

//     let errors = [];

//     // Username validation
//     if (username.length < 3 || username.length > 15 || !/^[a-zA-Z0-9]+$/.test(username)) {
//         errors.push("Username must be 3-15 characters long and can only contain letters and numbers.");
//     }

//     // Password validation
//     if (password.length < 6) {
//         errors.push("Password must be at least 6 characters long.");
//     }
//     if (password !== confirmPassword) {
//         errors.push("Passwords do not match.");
//     }

//     // Terms validation
//     if (!terms) {
//         errors.push("You must agree to the Terms & Conditions.");
//     }

//     // Reference error container
//     const errorContainer = document.getElementById('errorContainer');
//     if (!errorContainer) return; // Ensure container exists

//     errorContainer.innerHTML = ''; // Clear previous errors

//     // Display each error in its own box
//     errors.forEach((error, index) => {
//         setTimeout(() => {
//             const errorBox = document.createElement('div');
//             errorBox.classList.add('errorBox');
//             errorBox.textContent = error;
            
//             errorContainer.appendChild(errorBox);

//             // Remove the error after 5 seconds
//             setTimeout(() => {
//                 errorBox.remove();
//             }, 5000);
//         }, index * 200); // Slight delay for stacking effect
//     });
// });

document.getElementById('registrationForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Stop default form submission

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

    const errorContainer = document.getElementById('errorContainer');
    if (!errorContainer) return;

    errorContainer.innerHTML = ''; // Clear previous errors

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

    try {
        const response = await fetch("/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ fullname, email, username, password })
        });

        const data = await response.json();

        if (!data.success) {
            const errorBox = document.createElement('div');
            errorBox.classList.add('errorBox');
            errorBox.textContent = data.message;
            errorContainer.appendChild(errorBox);
            setTimeout(() => errorBox.remove(), 5000);
        } else {
            alert("Registration successful!");
            window.location.href = "/login.html";
        }
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
    }
});

