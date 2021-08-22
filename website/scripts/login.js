/**
 * Authors: Manuel Gasser, Julian Haldimann
 * Created: 24.11.2020
 * Last Modified: 23.03.2021
 */

/**
 * Function to login for the website.
 *
 */
function login() {
    // Get the input fields
    let username = document.querySelector('.username');
    let password = document.querySelector('.password');
    let warning = document.querySelector('.warning');
    // Check if username or password is set
    if ((username.value.length >= 0 && password.value.length >= 0)) {
        // Create data for the request
        const data = {
            username: username.value,
            password: password.value,
        };

        // Send request to the backend
        fetch(`${host}/api/login`, {
            method: 'POST',
            headers: {
                'Accept': '*/*',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `data=${JSON.stringify(data)}`,
        }).then((resp) => resp.json())
            .then(function (data) {
                if (data.status === 'success') {
                    createCookie(data.token);
                    redirect('/index.html');
                } else {
                    warning.innerHTML = "Wrong Username or Password"
                    warning.classList.remove('hidden');
                }
            });
    } else {
        warning.innerHTML = "Enter Username or Password"
        warning.classList.remove('hidden');
    }
}

/**
 * Function to create a session cookie for the website
 * @param token The user id from the database
 */
let createCookie = (token) => {
    let today = new Date();
    let expire = new Date();
    let number_of_days = 10;

    // Define expiration time
    expire.setTime(today.getTime() + 60 * 60 * 1000 * 24 * number_of_days);

    document.cookie = "token" + "=" + token + "; expires=" + expire.toGMTString() + ";path=/";
}
