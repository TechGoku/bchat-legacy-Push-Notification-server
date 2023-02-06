# Session Push Notification Server

## This is a python script for Session remote notification service

[API Documentation](https://github.com/oxen-io/session-push-notification-server/blob/master/DOCUMENTATION.md)

#### Use Python 3.7
#### To run the server:
First, install some dependencies from the Oxen deb repository

```
    sudo curl -so /etc/apt/trusted.gpg.d/oxen.gpg https://deb.oxen.io/pub.gpg
    echo "deb https://deb.oxen.io $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/oxen.list
    sudo apt update
    sudo apt install python3-pyonionreq # used for the v4 onion requests
```

Use `pip install -r requirements.txt` to install all the requirements first.


To start the server, use `python server.py`


The server is built with [Flask](https://github.com/pallets/flask) and [tornado](https://github.com/tornadoweb/tornado).  
The server uses APN for iOS push notifications, [aioapns](https://github.com/Fatal1ty/aioapns) to interact with APNs, and FCM for Android push notifications.

Right now the server only receives onion requests through the endpoint `/loki/v2/lsrpc` or `/oxen/v4/lsrpc` for
- `register`: register a device token associated with a session id
- `unregister`: unregister a device token from a session id's devices
- `subscribe_closed_group`: add a session id to a closed group as a member
- `unsubscribe_closed_group` remove a session id from a closed group members
- `notify`: send a message from remote notification

The new push notification server works this way:
- The client (Session Desktop or Mobile app) sends encrypted message data with the recipients' session id to server.
- The server checks the database to see if the recipients has registered their devices.
- The server generates and sends the push notification to the devices registered with their tokens.

The server will store some statistics data every 12 hours for analysing the traffic going through. The data includes:
- The number of messages sent to the server
- The number of messages sent to closed groups
- The number of push notifications sent to iOS devices
- The number of push notifications sent to Android devices

There is also an endpoint `/get_statistics_data` to get the data above.


## Script to generate the key pair

```
 random = get_random_bytes(32)              # The private key 32 bytes
 priv = _curve25519.make_private(random)
 print(priv.hex())
 pub = _curve25519.make_public(priv)
 print(pub.hex())
```


## Potential issues

If you get an issue during the `sudo apt update` about the certificate chain being invalid,
try to create a file at `/etc/apt/apt.conf.d/99deboxenio-cert` with content:
`Acquire::https::deb.oxen.io::Verify-Peer "false";`


If you get issue with the Rust compiler, use
`pip3 install setuptools_rust docker-compose` (or just `pip3 install setuptools_rust`)

If something related to flask not having jinja2, run

```
pip3 uninstall flask
pip3 install flask
```