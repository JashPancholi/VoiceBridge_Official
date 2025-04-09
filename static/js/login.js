// document.getElementById('loginForm').addEventListener('submit', function(event) {
//     event.preventDefault(); // Stop form submission

//     const username = document.getElementById('username').value.trim();
//     const password = document.getElementById('password').value.trim();

//     let errors = [];

//     // Email validation
//     if (username.length < 3 || username.length > 15 || !/^[a-zA-Z0-9]+$/.test(username)) {
//         errors.push("Username must be 3-15 characters long and can only contain letters and numbers.");
//     }

//     // Password validation
//     if (password.length < 6) {
//         errors.push("Password must be at least 6 characters long.");
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


document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Stop form submission

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    let errors = [];

    // Username validation    
    // if (username.length < 3 || username.length > 15 || !/^[a-zA-Z0-9]+$/.test(username)) {
    //     errors.push("Username must be 3-15 characters long and can only contain letters and numbers.");
    // }

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
        const response = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (!data.success) {
            const errorBox = document.createElement('div');
            errorBox.classList.add('errorBox');
            errorBox.textContent = data.message;
            errorContainer.appendChild(errorBox);
            setTimeout(() => errorBox.remove(), 5000);
        } else {
            alert("Login successful!");
            window.location.href = "/dashboard.html";
        }
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
    }
});
