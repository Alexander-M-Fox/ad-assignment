// add event listener for submit button
document.getElementById("create-admin-account-submit").onclick = function () {
    const email = document.getElementById("ca_email").value;
    const password = document.getElementById("ca_pwd").value;

    firebase
        .auth()
        .createUserWithEmailAndPassword(email, password)
        .then(() => {
            window.location.href = "../signIn";
        })
        .catch(function (err) {
            console.log(err);
        });

    firebase.auth().onAuthStateChanged(
        function (user) {
            if (user) {
                user.getIdToken().then(function (token) {
                    document.cookie = `token=${token}; path=/`;
                });
            } else {
                document.cookie = "token=; path=/";
            }
        },
        function (error) {
            console.log(error);
            alert("Unable to log in: " + error);
        },
    );
};
