# MRT Status Page

A simple Flask web application that reports the status of Minecraft (Java Edition) servers, Mumble servers, and websites. This application also retrieves up-to-date version and player data from Minecraft and Mumble servers.

This page was built for the **[Minecart Rapid Transit (MRT) Minecraft Server](https://www.minecartrapidtransit.net)** to help inform players of the status of various services.

## Live Demo

The actual live status page can be viewed at: **[https://status.minecartrapidtransit.net](https://status.minecartrapidtransit.net)**.

## Prerequisites

This application was built using **Python 3.6.2**, and using the following packages:

- **Flask 0.12.2**
- **mcstatus 2.2**
- **redis 2.10.6**
- **requests 2.18.4**
- **schedule 0.4.3**
- **zeroc-ice 3.7.0**

After installing Python, the easiest way to install these packages is by using **pip**:

    pip install Flask mcstatus redis requests schedule zeroc-ice

## Configuration

See **config.cfg** and choose your desired settings. This application supports two types of data stores, which are used to store the statuses retrieved from the services:

- **SQLite 3** (stored in a database file of negligible size)
- **Redis** (stored in-memory, you must set up your own Redis instance for this option)

## Setting up Services

You can specify the servers you want to monitor in the JSON files in the **services** folder.

### Minecraft Servers

This application uses **[mcstatus](https://github.com/Dinnerbone/mcstatus)**, a library made by the Minecraft developer Dinnerbone, to retrieve the status from a Minecraft server that has queries enabled. To enable queries on your server, go to your **server.properties file** and set the following:

    enable-status=true
    query.port=25565

Then, in **mc_servers.json**, add an entry with the name, address, and port of your Minecraft server:

	{
	  "name": "Main",
	  "address": "minecartrapidtransit.net",
	  "status": null,
	  "message": null
	}

If your Minecraft server uses a different port or query port, you can specify them in the JSON entry:

    {
	  "name": "Beta",
	  "address": "minecartrapidtransit.net",
      "port": 35565,
      "query": 40001,
	  "status": null,
	  "message": null
	}

### Mumble Servers

This application uses **Zero-C ICE** to retrieve information from a Mumble server. To enable ICE on your server, go to your **murmur.ini** and uncomment the following line:

    ice="tcp -h 127.0.0.1 -p 6502"

Note that the loopback address 127.0.0.1 will only work if you are hosting the Mumble server on the same host as the status page. Change the address and/or port according to your needs.

It is strongly recommended that you specify an ICE read-only secret on your Mumble server, as well as keep the ICE write secret blank. This will ensure that parties that connect to your Mumble server by ICE can only read information about your server if they have the secret, and that they can never make any changes to the server. Specify the secrets in **murmur.ini**: 

    icesecretread=secret
    icesecretwrite=

Finally, in **mumble\_servers.json**, add an entry for your Mumble server. Note that `address` and `port` refers to the normal method that Mumble clients should use to connect to your server, while `ice_address` and `ice_port` should match what you specified in murmur.ini. If you added an ICE read-only secret to your server, be sure to specify it here under `ice_secret`:

    {
      "name": "Mumble",
      "address": "minecartrapidtransit.net",
      "port": 64738,
      "ice_address": "127.0.0.1",
      "ice_port": 6502,
      "ice_secret": "secret",
      "status": null,
      "message": null
    }

### Web Services

This application can ping websites to ensure that they are at least responding with a 2xx or 3xx status code. Any other status code will result in a "No Service" status shown on the page.

In **web_services.json**, enter the name and address of your website:

    {
      "name": "Website",
      "address": "https://www.minecartrapidtransit.net",
      "status": null,
      "message": null
    }

Websites protected by HTTP Basic Auth are also supported. For such websites, add `basic_auth_username` and `basic_auth_password`:

    {
      "name": "File Server",
      "address": "https://files.minecartrapidtransit.net",
      "basic_auth_username": "username",
      "basic_auth_password": "password",
      "status": null,
      "message": null
    }

### Third-Party Services

This category is intended for services that you do not own, and services where you do not want to actively check the status. Instead, a link can be specified to the third-party provider's own status page.

In **third\_party\_services.json**, specify `address` as the address of the service if applicable, and `status_address` as the address of the service's status page. If `address` is null, it will display as "N/A".

    {
      "name": "Mojang",
      "address": null,
      "status_address": "https://help.mojang.com"
    }

## Overridable Statuses and Messages

For all types of services except for third party services, you can replace the retrieved status and/or the default message with your own. This is useful if you want to notify players of any maintenance or alerts, or if your services are intentionally down or having issues for a period of time.

To change the status, set `status` in the JSON service entry to one of the following:

- **`"ONLINE"`** = **"Good Service"**
- **`"OFFLINE"`** = **"No Service"**
- **`"PARTIAL"`** = **"Fair Service"**
- **`"ALERT"`** = **"Alert"**
- **`"MAINTENANCE"`** = **"Maintenance"**
- **`"UNKNOWN"`** = **"Unknown"**

To change the message, set `message` in the JSON service entry to your desired message. You can use "\n" characters to create new lines in your message.

Example:

    {
      "name": "Main",
      "address": "minecartrapidtransit.net",
      "port": 25565,
      "status": "MAINTENANCE",
      "message": "The server will be down for maintenance\nthis Monday, January 1st from 1-3pm UTC."
    }