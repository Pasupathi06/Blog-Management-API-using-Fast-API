const API_BASE = "";

const message = document.getElementById("message");
const loginForm = document.getElementById("loginForm");
const passwordInput = document.getElementById("password");
const togglePassword = document.getElementById("togglePassword");
const forgotPassword = document.getElementById("forgotPassword");
const registerLink = document.getElementById("registerLink");


// =====================================================
// SHOW MESSAGE
// =====================================================

function showMessage(text, type = "info") {

    if (!message) {
        return;
    }

    message.textContent = text;

    if (type === "error") {

        message.style.color = "#dc2626";

    } else if (type === "success") {

        message.style.color = "#16a34a";

    } else {

        message.style.color = "#4f46e5";

    }
}


// =====================================================
// PASSWORD SHOW / HIDE
// =====================================================

if (togglePassword && passwordInput) {

    togglePassword.addEventListener("click", function () {

        if (passwordInput.type === "password") {

            passwordInput.type = "text";

            togglePassword.textContent = "🙈";

        } else {

            passwordInput.type = "password";

            togglePassword.textContent = "👁";

        }

    });

}


// =====================================================
// NORMAL LOGIN
// POST /auth/login
// =====================================================

if (loginForm) {

    loginForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const username =
                document.getElementById("username")
                    .value
                    .trim();

            const password =
                passwordInput
                    ? passwordInput.value
                    : "";

            const remember =
                document.getElementById("remember");


            // -------------------------------------------------
            // VALIDATION
            // -------------------------------------------------

            if (!username || !password) {

                showMessage(
                    "Please enter username and password.",
                    "error"
                );

                return;
            }


            showMessage("Logging in...");


            try {

                // -------------------------------------------------
                // LOGIN API
                // -------------------------------------------------

                const response = await fetch(
                    `${API_BASE}/auth/login`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "Accept":
                                "application/json"
                        },

                        body: JSON.stringify({
                            username: username,
                            password: password
                        })
                    }
                );


                // -------------------------------------------------
                // READ RESPONSE
                // -------------------------------------------------

                const data =
                    await response.json();


                // -------------------------------------------------
                // LOGIN FAILED
                // -------------------------------------------------

                if (!response.ok) {

                    showMessage(
                        data.detail ||
                        data.message ||
                        "Login failed. Please check your credentials.",
                        "error"
                    );

                    return;
                }


                // -------------------------------------------------
                // CHECK ACCESS TOKEN
                // -------------------------------------------------

                if (!data.access_token) {

                    showMessage(
                        "Login successful, but access token was not received.",
                        "error"
                    );

                    return;
                }


                // -------------------------------------------------
                // SAVE TOKEN
                // -------------------------------------------------

                localStorage.setItem(
                    "access_token",
                    data.access_token
                );


                localStorage.setItem(
                    "token_type",
                    data.token_type || "bearer"
                );


                // -------------------------------------------------
                // REMEMBER LOGIN
                // -------------------------------------------------

                if (remember && remember.checked) {

                    localStorage.setItem(
                        "remember_login",
                        "true"
                    );

                } else {

                    localStorage.removeItem(
                        "remember_login"
                    );

                }


                // -------------------------------------------------
                // SUCCESS
                // -------------------------------------------------

                showMessage(
                    "Login successful! Opening dashboard...",
                    "success"
                );


                // -------------------------------------------------
                // OPEN DASHBOARD
                // -------------------------------------------------

                setTimeout(
                    function () {

                        window.location.href =
                            "/static/dashboard.html";

                    },
                    700
                );

            } catch (error) {

                console.error(
                    "Login error:",
                    error
                );


                showMessage(
                    "Unable to connect to the server.",
                    "error"
                );

            }

        }
    );

}


// =====================================================
// GOOGLE LOGIN
// Backend:
// GET /auth/login/google
// =====================================================

function googleLogin() {

    showMessage(
        "Opening Google login..."
    );


    // Auth0 Google OAuth

    window.location.href =
        `${API_BASE}/auth/login/google`;

}


// =====================================================
// FACEBOOK LOGIN
// Backend:
// GET /auth/login/facebook
// =====================================================

function facebookLogin() {

    showMessage(
        "Opening Facebook login..."
    );


    // Auth0 Facebook OAuth

    window.location.href =
        `${API_BASE}/auth/login/facebook`;

}


// =====================================================
// FORGOT PASSWORD
// =====================================================

if (forgotPassword) {

    forgotPassword.addEventListener(
        "click",
        function (event) {

            event.preventDefault();


            showMessage(
                "Password reset is not connected yet.",
                "info"
            );

        }
    );

}


// =====================================================
// CREATE ACCOUNT
// POST /auth/register
// =====================================================

if (registerLink) {

    registerLink.addEventListener(
        "click",
        function (event) {

            event.preventDefault();


            showMessage(
                "Registration page is not connected yet.",
                "info"
            );

        }
    );

}


// =====================================================
// CHECK EXISTING TOKEN
// =====================================================

window.addEventListener(
    "load",
    function () {

        const token =
            localStorage.getItem(
                "access_token"
            );


        if (token) {

            showMessage(
                "You are already logged in.",
                "success"
            );

        }

    }
);