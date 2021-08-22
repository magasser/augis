/**
 * Authors: Manuel Gasser, Julian Haldimann
 * Created: 07.12.2020
 * Last Modified: 20.03.2021
 */

const host = 'https://jn5c33164f.execute-api.eu-central-1.amazonaws.com/dev';


/**
 * Generic Function to make a redirect in the browser
 * @param route
 */
let redirect = (route) => {
    let local = '';
    if (host.includes('localhost')) {
        local = '/Augis/website'
    }
    window.location.href = `${local}${route}`;
}

/**
 * Downloads the new generated json file
 *
 * @param filename The filename for the file to export
 * @param text The text to save into the file
 */
let download = (filename, text) => {
    let element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(JSON.stringify(text)));
    element.setAttribute('download', filename);

    element.style.display = 'none';
    document.body.appendChild(element);

    element.click();

    document.body.removeChild(element);
};

/**
 * Send request to server to check if JWT is valid
 * @param token
 * @returns {Promise<boolean>}
 */
let isValidToken = (token) => {
    // Send message to server --> Send the token in the header
    return fetch(`${host}/api/is-valid`, {
        method: 'POST',
        headers: {
            'Accept': '*/*',
            'Authorization': token
        }
    }).then((resp) => resp.json())
        .then(data => {
            return !!data.username;
        });
}

/**
 * Get Cookie by name
 * @param cname
 * @returns {string}
 */
let getCookie = (cname) => {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

/**
 * Is token valid run th function f else redirect
 * @param f function to pass
 */
let validateToken = (f) => {
    if (document.cookie) {
        let token = getCookie('token');
        if (token !== "") {
            isValidToken(token)
                .then(valid => {
                    if (valid) {
                        f();
                    } else {
                        redirect('/pages/login.html');
                    }
                })

        } else {
            redirect('/pages/login.html');
        }
    } else {
        redirect('/pages/login.html');
    }
};
