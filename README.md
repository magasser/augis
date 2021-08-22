## AUGIS

In this repository we want to store everything we use for our "Project 2" and "Bachelor Thesis".

# Documentation

All information and documents are stored in BFH SharePoint.
Sharepoint --> https://bernerfachhochschule-my.sharepoint.com/personal/haldj4_bfh_ch/_layouts/15/onedrive.aspx

# Exploration

Inside the exploration folder you can store everything you discovered.

# Website 

The route generator app is online available at --> https://project-augis.ch/

To start the AUGIS-Tour visit --> https://project-augis.ch/pages/drive.html

If you want to build the website on your local machine:

1. Navigate to the website folder
2. Run ```npm install``` to install all needed packages
3. Run ```npm run dev``` to build the css file
4. Open the website in your browser

You need to build the css because the project use scss files.  
The new generated css file is located inside the dist folder.

# Database

To save the generated routes there is a database available:

https://lx19.hoststar.hosting/lx-phpmyadmin/db_structure.php?server=1db=ch299816_augis

DB-Host: lx19.hoststar.hosting
DB-Name: ch299816_augis
Username: ch299816_admin
Password: 24ii&e3tK7d


# IOS App

With the IOS App you can calculate distance and the direction between two coordinates.
The Apps will be used as a sensor-block. It will read the gps and the heading data.
These information will be published on the mqtt broker.

To run the app you must have a Mac and Xcode installed.

# GPS Python

Inside this miniproject you can find the same logic as in the IOS App but in python

If you want to run it on your local machine you should use the following command:

```bash
python3 main.py
```

# MQTT Broker

To create a connection between the AUGIS and other software we use Websocket. 
If you want to exchange messages or send commands, you need a MQTT Broker.

Our selfhosted broker is available at:

ws://147.87.116.215:443

## MQTT Client
if you want to use the broker from the mqtt-explorer you have to configure the explorer like this:

![MQTT-Expolere Configuration](images/mqtt-explorer-config.png?raw=true "Configuration")

# Topics

Here is a list of topics we need to control the AUGIS

```
GPS Coordinates of AUGIS    ==>     augis/items/sensors/gps/coordinates
GPS Direction               ==>     augis/items/calculations/gps/direction
GPS Distance                ==>     augis/items/calculations/gps/distance
GPS Speed                   ==>     augis/items/calculations/gps/speed
Direction of AUGIS          ==>     augis/items/sensors/direction/degrees
Activity Status of AUGIS    ==>     augis/items/boat/active
Start Command               ==>     augis/command/start
Finish Command              ==>     augis/command/end
Change to RemoteControl     ==>     augis/command/remote
```

# API
The API of the project is running on AWS.
The API is a simple severless express nodejs project.

## Dependencies
    "aws-serverless-express": "^3.4.0",
    "bcryptjs": "^2.4.3",
    "cors": "^2.8.5",
    "dotenv": "^8.2.0",
    "express": "^4.17.1",
    "fs": "0.0.1-security",
    "jsonwebtoken": "^8.5.1",
    "mysql": "^2.18.1"

## Usage
To create a connection to the database you have to create a config file like this:
```
{
    "user": "db-username",
    "host": "db-server",
    "password": "db-user-password",
    "database": "db-table-name"
}
```
## Commands
To install all the packages for the api just type:
```
npm install 
```

To deploy the backend you can inside the api folder just type:
```
serverless deploy
```
