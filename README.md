# Bark2Meet
## Architectural Overview
Bark2Meet’s server-side is based on the Flask Web Framework.
Graphs can be seen in the documentation in the submission itself.

Regarding the different python files and their purpose:
•	Routes.py – Main backend file that manages client’s requests and returns a response.
•	Forms.py – Responsible for the validity of all user input into the various forms on the app.
•	Init.py – responsible on initializing various variables and parameters on server start.
•	Models.py – Implements the User and Friend data structures that require interaction with the flask SQL database.
•	Event.py – manages the walk events of the application
•	Notification.py – manages the server-side notifications of the application (not the visual aspect of it nor the notifications emitted from the operating system).

All of the client side’s HTML files reside in the templates directory according to flask’s framework requirement.
All the client side’s assets, images, CSS, and JavaScript files reside in the static directory according to flask’s framework requirement. These assets include the subdirectory users_data which holds all the uploaded user images.
The JSON files that represent user’s notification history (by username) and walk-events (by date) reside in another main directory names databases.



## API

### Server-side inner communication
The application holds various data structures, each with its own API. The server-side uses these data structures to analyze and respond to client-side requests.
We can divide those data structures into 2 subcategories – data structures that their database is managed by flask SQL database and data structures that are managed by the application itself.
The data structures that their database is managed by flask SQL database:
•	User – Represents a user in the site
•	Friend – represent a friend connection between two users

To modify and change these data structure on the database we use flask SQL database’s API.
Data structures that are managed by the application itself:
•	Notifications – A class that uses access to the JSON files that holds the notifications data and send to the client-side various information about past and future notifications.
•	Events – A class that uses access to the JSON files that holds the walk-events data and send to the client-side various information about past and future walk-events of the current user, his friends, and his current area.


### Client-side to Server-side Communication
In each request coming from the client-side, the server will perform a series of API calls of the various data structures that were explained above, to generate the needed response (either if it is a GET request, PUT\POST request, or a routing request).
There are 2 main ways of communication between the two sides:
•	Routing – as the client side whishes to load a new page within the side, the server will first perform the needed actions to generate the data the page to be loaded requires even before the client-side code (HTML, CSS, and JavaScript) is loaded, so the client-side code could get various information while on the first loading of the DOM elements of the page.

 

•	GET, PUT Requests – In any situation the client-side wishes to get or update server-side information independently of a page load, the application implements the RESTFUL API way – the client sends a request using a special “/api/” routing, and the server responds with a JSON.

 
Examples for both cases can be seen in the documentation in the submission itself.





## Installation and usage

### Installing
To run the site, it is required to install the needed python packages by running the command “pip install -r req.txt” on the root folder.
If the installation will not run smoothly, all packages can just be copied from the given zip file “site-packages.zip”

### Running
Open the file “app.py” on the root directory and run the main (and only) function.
Example can be seen in the documentation in the submission itself.


### Usage
It is important to notice that the local app cannot execute a multiple devices with multiple users scenario. To solve that, we have created a special user that will emulate a user standing approximately 150m north of the device’s current GPS location, so you could experience the application the way it is intended to be experienced – with multiple users online and close to each other.
The user’s details are:
•	Username: test@test.com
•	Password: 123456


