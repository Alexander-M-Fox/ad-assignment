const signOutElement = document.getElementById("sign-out");
const logInElement = document.getElementById("login-info");

window.addEventListener("load", function () {
    // FirebaseUI config.
    var uiConfig = {
        // signInSuccessUrl: window.location.href,
        signInOptions: [firebase.auth.EmailAuthProvider.PROVIDER_ID],
        // Terms of service url.
        tosUrl: "<your-tos-url>",
        callbacks: {
            signInSuccess: function (currentUser, credential, redirectUrl) {
                // Handle the result
                currentUser.getIdToken().then(function (token) {
                    document.cookie = `token=${token}; path=/`;
                    window.location.href = "/signIn";
                });
            },
        },
    };

    firebase.auth().onAuthStateChanged(
        function (user) {
            console.log("onauthchanged admin running");
            if (user) {
                if (!!signOutElement) {
                    signOutElement.hidden = false;
                }
                if (!!logInElement) {
                    logInElement.hidden = false;
                }
                console.log(`Signed in as ${user.displayName} (${user.email})`);
            } else {
                // User is signed out.
                // Initialize the FirebaseUI Widget using Firebase.
                var ui = new firebaseui.auth.AuthUI(firebase.auth());
                // Show the Firebase login button.
                ui.start("#firebaseui-auth-container", uiConfig);
                // Update the login state indicators.
                if (!!signOutElement) {
                    signOutElement.hidden = true;
                }
                if (!!logInElement) {
                    logInElement.hidden = false;
                }
                // Clear the token cookie.
                console.log("clearing token");
                document.cookie = "token=; path=/";
            }
        },
        function (error) {
            console.log(error);
            alert("Unable to log in: " + error);
        },
    );
});
