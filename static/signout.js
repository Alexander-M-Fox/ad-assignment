const signOutElement = document.getElementById("sign-out");

window.addEventListener("load", async function () {
    if (!!signOutElement) {
        signOutElement.onclick = function () {
            console.log("sign out button clicked");
            console.log(firebase);
            document.cookie = "token=";
            firebase
                .auth()
                .signOut()
                .then(() => {
                    console.log("firebase.auth().signOut() ran");
                    window.location.href = "../";
                });
            fetch("/signout")
                .then((response) => {
                    if (response.status === 200) {
                        document.cookie = "token=";
                        console.log("session destroyed");
                    } else {
                        console.log("/signout response !== 200");
                    }
                })
                .catch((err) => {
                    console.log(err);
                });
        };
    }

    // firebase.auth().onAuthStateChanged(function (user) {
    //     if (user) {
    //         user.providerData.forEach((profile) => {
    //             console.log("Sign-in provider: " + profile.providerId);
    //             console.log("  Provider-specific UID: " + profile.uid);
    //             console.log("  Name: " + profile.displayName);
    //             console.log("  Email: " + profile.email);
    //             console.log("  Photo URL: " + profile.photoURL);
    //         });
    //     }
    // });
});
