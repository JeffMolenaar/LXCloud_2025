# LXCloud - IoT Controller Management Platform

LXCloud is a comprehensive cloud-based dashboard platform for managing IoT controllers and visualizing their data. The platform supports real-time data collection via MQTT, user management with 2FA, and an extensible architecture for future enhancements.

## Features

Controller working explained:
-	The controller sends the following data to a MQTT Mosquitto server
o	Serial Number
o	Type of controller, the types are (speedradar, beaufortmeter, weatherstation, aicamera).
The types are also expandable in the future.
o	Data, the data is sended as a json string and should be read via the web portal.
	The web portal should be able to have addons so there is a possibility to easily intergrate new controllers types and the web portal can use those addons to read the data and convert those to the dashboard.

The things we want for the first startup of this project are as follows.

For logged in users:
-	Dashboard
o	A live map view where the controllers are shown as pinpoints, when you click on one of those controllers it should take the user to another page where they can modify the controller or watch it’s data.
o	Controller statuses (online/offline)

-	Screen management
o	Binding controller to the user by serial number controller, but only if the serial number has once reported live status to the server via MQTT.
o	Changing name of the controller (Serial number controller).
o	Removing binded controller.
o	View data of binded controller.

-	User management
o	Change name, address,e-mail,password
o	2FA enable option, (for logging in cloud platform)
o	Remove account option (by removing should every screen that is connected to this user unbind automatically)










For logged in super admin
-	Dashboard (the same as for users)
-	Screen management (same as for users but more)
o	As super admin its possible to unbind every screen from any user.
o	As super admin its possible to view all data from any screen from any user.
o	As super admin its possible to view and manage unbind controllers aswell.
-	User management (same as for users but more)
o	As super admin its possible to remove 2FA from any user.
o	As super admin its possible to change the password of any user.
o	As super admin its possible to delete any user completely (any controller binded to that user should be unbind automatically.
-	U.I. Customization
o	As super admin its possible to customize the complete cloud U.I. interface via custom CSS (per page)
o	As super admin its possible to modify the complete header (height, width, header logo or text, colors and so on.
o	As super admin its possible to modify the complete footer (height, width, footer logo or text, colors and so on.
o	As super admin its possible to change marker icons for the dashboard map (via uploading new ones)
o	As super admin it should be possible to modify any u.i. element via buttons/dropdown menu’s/sizes and so on.
-	Addon management
o	As super admin its possible to add new addons (which can also include elements that can be shown on the dashboard and should also be placeable on the dashboard aswell.
o	As super admin its possible to remove addons or edit them.






This cloud based platform is a bit inspired by Home Assistant (like adding addons and stuff and showing them on display). It must feel easy and user friendly to implement controllers and watch their data. Even having cards that can be placed in the dashboard and so on.
The dashboard must have a modern look, that is easy to understand.


As database I want to use MariaDB.

I want a complete installation script for ubuntu server LTS 24.
If their going to be updates in the github repository it should be easy to run this update via an update script aswell.
Also every update that is make should give the version number a bump, starting at V1.0.0
As example after an update the version should say V1.0.1 and so on.
