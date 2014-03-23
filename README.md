iCloud Tabs Updater
==================

Update iCloud tabs without Safari.

**This may mess up your iCloud account or your Safari.app config-cache, perhaps if/when Apple changes their API. Use at your own risk.**

Try it on your iCloud-enabled Mac
-------
```bash
$ pip install -r requirements.txt
$ gen_update_config.py > update_config.py
```

Check your credentials in update_config.py and change `DEVICE_NAME` to a testing name.  
Then edit the tabs list in update.py and run it to upload them to iCloud:
```bash
$ python update.py
```
You should see the tabs in your other iCloud-linked Safaris at this point.  
You can now run this from any pythonic computer with no Apple bits required.  

[iCloud purges un-updated tabs](http://support.apple.com/kb/HT5372?viewlocale=en_US&locale=en_US) after 2 weeks. Use `update_tabs([])` to purge them manually.


Config (the hard way)
------
Most constants for update_config.py.template can be grabbed from watching requests with mitmproxy:

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
