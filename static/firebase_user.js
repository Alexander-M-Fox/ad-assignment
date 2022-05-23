const signOutElement = document.getElementById("sign-out");
const logInElement = document.getElementById("login-info");

window.addEventListener("load", function () {
    // FirebaseUI config.
    var uiConfig = {
        signInSuccessUrl: "/signIn",
        signInOptions: [firebase.auth.GoogleAuthProvider.PROVIDER_ID],
        // Terms of service url.
        tosUrl: "<your-tos-url>",
    };

    firebase.auth().onAuthStateChanged(
        function (user) {
            console.log("on auth state changed running");
            if (user) {
                console.log("user is signed in");
                // User is signed in, so display the "sign out" button and login info.
                if (!!signOutElement) {
                    signOutElement.hidden = false;
                }
                if (!!logInElement) {
                    logInElement.hidden = false;
                }
                console.log(`Signed in as ${user.displayName} (${user.email})`);
                user.getIdToken().then(function (token) {
                    // Add the token to the browser's cookies. The server will then be
                    // able to verify the token against the API.
                    document.cookie = "token=" + token;
                });
            } else {
                // User is signed out.
                console.log("user is signed out");
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
                document.cookie = "token=";
            }
        },
        function (error) {
            console.log(error);
            alert("Unable to log in: " + error);
        },
    );
});
