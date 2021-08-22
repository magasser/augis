/**
 * Authors: Manuel Gasser, Julian Haldimann
 * Created: 07.12.2020
 * Last Modified: 21.03.2021
 */

window.onload = () => {
    validateToken(loadPage);
};

let loadPage = () => {
    loadRoutes();
}

/**
 * Get all the routes from the database and print them
 */
let loadRoutes = () => {
    const routesList = document.querySelector('#routes-list');
    fetch(`${host}/api/routes`, {
        method: 'GET',
        headers: {
            'Accept': '*/*'
        },
    })
        .then(resp => resp.json())
        .then(result => {
            let html = '<ul>';
            result.forEach((r) => {
                html += `<li class="route"><p>${r.name}<img src="../images/save.svg" onclick="downloadRoute('${r.name}')"/></p></li>`;
            });
            html += '</ul>';

            routesList.innerHTML = html;
        });
};

/**
 * Function to download the route
 * @param name Name of the route
 */
let downloadRoute = (name) => {
    fetch(`${host}/api/routes/${name}`, {
        method: 'GET',
        headers: {
            'Accept': '*/*'
        },
    })
        .then(resp => resp.json())
        .then(file => {
            download(`${name}.geojson`, JSON.parse(file.json));
        });
};

