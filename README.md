iCloud Tabs Updater
==================

Update iCloud tabs without Safari.

**This may mess up your iCloud account or your Safari.app config-cache, perhaps if/when Apple changes their API. Use at your own risk.**

Automagic configuration
-------
If you are on an iCloud-enabled OSX, configuration to match your Safari is fully automatic.  
If you are using anything else, you will need to type in your iCloud login when asked to generate a new device config.  
```bash
$ pip install -r requirements.txt
$ gen_update_config.py | tee update_config.py
iCloud username: someone@example.com
DEVICE_NAME = 'somecomputer'
AUTHORIZATION = 'X-MobileMe-AuthToken .....'
DEVICE_UUID = <128-bit uuidgen>
```

Feel free to change `DEVICE_NAME` and `DEVICE_UUID` for testing purposes. Safari.app will always overwrite whatever iCloud
has with its current tab set, so fear not losing your currently open tabs.
  
Edit the tabs list in update.py and run it to upload them to iCloud:
```bash
$ python update.py
```
You should see the tabs in your other iCloud-linked Safaris at this point.  

Config (the hard way)
------
Most constants for update_config.py.template can be grabbed from watching HTTP requests with mitmproxy:

```bash
$ pip install mitmproxy
$ mitmproxy -p 8080 
```
Set your OSX HTTPS proxy settings to use 8080, open Safari and watch for requests to `keyvalueservice.icloud.com`.
```bash
$ open ~/.mitmproxy/mitmproxy-ca-cert.cer #add and trust this cert
$ networksetup -getsecurewebproxy Ethernet
$ networksetup -setsecurewebproxy Ethernet localhost 8080
$ networksetup -setsecurewebproxystate Ethernet on
```

Chrome Extension
----------------
Send currently open Chrome tabs to iCloud every 5 minutes.

After filling in update_config.py, run the simple server:

```bash
$ python server.py
```

Then, load the chrome extension in the chrome_extension/ directory:

- Open `chrome://extensions/`
- Check the developer mode checkbox. 
- Click `Load Unpacked Extension`.
- Navigate to the chrome_extension/ directory and select it.
