# Custom Discord Rich Presence

Install dependencies with

`pip install -r dependencies.txt`

Run with

`python3 main.py`

Needs a config.py file in root of repository containing:

```
APPLICATION_ID = ""
DISCOG_USER_TOKEN = ""
```

Where `APPLICATION_ID` is obtained from creating an application on Discord and `DISCOG_USER_TOKEN` is obtained by creating an API account on discog.

---
## Run as a background service on Ubuntu

https://websofttechs.com/tutorials/how-to-setup-python-script-autorun-in-ubuntu-18-04/