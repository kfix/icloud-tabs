#!/usr/bin/env python
if __name__ == '__main__':
      #if using an iCloud enabled Mac, we automagically derive the magic iCloud tokens
      import biplist, plistlib, os, subprocess, urllib2, getpass
      ret = {}
      
      ret['APNS_TOKEN'] = biplist.readPlist(os.path.expanduser("~/Library/SyncedPreferences/com.apple.syncedpreferences.plist"))["com.apple.syncedpreferences.push"]["lastTokenOnServer"]
      #retrieve KVS.icloud.com app-specific token for APNS push. plist is updated by syncdefaultsd, seems to rotate every so often. token is generated by HTTP exchange.
      #   /System/Library/PrivateFrameworks/SyncedDefaults.framework/Support/syncdefaultsd

      try: #if SysPrefs->iCloud->FindMyMac is enabled, we can get its cached iCloud account token without manually-authing to icloud.com for it
         nvram = plistlib.readPlistFromString(subprocess.check_output("nvram -x -p".split()))
         icl_token = biplist.readPlistFromString(nvram['fmm-mobileme-token-FMM'].data)['authToken'] 
	 icl_id = biplist.readPlistFromString(nvram['fmm-mobileme-token-FMM'].data)['personID']
      except: #ask for icloud user/pass and manually auth to iCloud to get a working iCloud token
         icl_user = raw_input('iCloud username: ')
         icl_pass = getpass.getpass('iCloud password: ')

         #Thanks ElcomSoft! http://www.elcomsoft.com/PR/recon_2013.pdf
         request = urllib2.Request('https://setup.icloud.com/setup/authenticate/$APPLE_ID$', headers={
               "Host": 'setup.icloud.com',
               "User-Agent" : 'iCloud.exe(unkown version) CFNetwork/520.2.6',
               "Accept": "*/*",
               "Accept-Language": "en-us",
               "Authorization": 'Basic ' + ('%s:%s' % (icl_user, icl_pass)).encode("base64").strip(),
               "X-MMe-Client-Info": '<PC> <Windows; 6.1.7601/SP1.0; W> <com.apple.AOSKit/88>',
               } )
         u = urllib2.urlopen(request)
         data = u.read()
         icloud_auth = plistlib.readPlistFromString(data)
         print icloud_auth
         icl_id = icloud_auth['appleAccountInfo']['dsid']
         icl_token = d_auth['tokens']['mmeAuthToken']

      ret['AUTHORIZATION'] = 'X-MobileMe-AuthToken ' + (icl_id + ':' + icl_token).encode("base64").strip()
      
      ioreg = subprocess.check_output("ioreg -rd1 -c IOPlatformExpertDevice -a".split())
      hw_uuid = plistlib.readPlistFromString(ioreg)[0]['IOPlatformUUID'] #UDID on iOS?
      ret['DEVICE_UUID'] = biplist.readPlist(os.path.expanduser("~/Library/Preferences/ByHost/com.apple.Safari.%s.plist" % hw_uuid))["SyncedTabsDeviceUUID"] #safari.app specific device id, `uuidgen` outputs same format
      ret['DEVICE_NAME'] = subprocess.check_output(["hostname", "-s"]).strip()
     
      for k,v in ret.items():
         print "%s = %s" % (k,v.__repr__())
