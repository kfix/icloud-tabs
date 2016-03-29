#!/usr/bin/env python
if __name__ == '__main__':
      #if using an iCloud enabled Mac, we can automagically derive the magic iCloud tokens
      import biplist, plistlib, os, subprocess, urllib2, getpass, sys
      ret = {}
      
      try:
         ret['APNS_TOKEN'] = biplist.readPlist(os.path.expanduser("~/Library/SyncedPreferences/com.apple.syncedpreferences.plist"))["com.apple.syncedpreferences.push"]["lastTokenOnServer"]
         #retrieve KVS.icloud.com app-specific token for APNS push. plist is updated by syncdefaultsd, seems to rotate every so often. token is saved after HTTP exchange.
         # biplist.readPlist(os.path.expanduser("~/Library/SyncedPreferences/com.apple.syncedpreferences.plist"))["com.apple.syncedpreferences"]["config"]["apnsTokenTTL"]
	 #  codesign --display --entitlements - /System/Library/PrivateFrameworks/SyncedDefaults.framework/Support/syncdefaultsd
      except:
         ret['APNS_TOKEN'] = '' #it appears to not be crucial to send this with tab updates

      try: #if SysPrefs->iCloud->FindMyMac is enabled, we can get its cached iCloud account token without manually-authing to icloud.com for it
         raise
         nvram = plistlib.readPlistFromString(subprocess.check_output("nvram -x -p".split()))
         icl_token = biplist.readPlistFromString(nvram['fmm-mobileme-token-FMM'].data)['authToken'] 
	 icl_id = biplist.readPlistFromString(nvram['fmm-mobileme-token-FMM'].data)['personID']
      except: #ask for icloud user/pass and manually auth to iCloud to get a working iCloud token
         sys.stderr.write('iCloud username: ')
         icl_user = raw_input('')
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
         icl_token = icloud_auth['tokens']['mmeAuthToken']

      ret['AUTHORIZATION'] = 'X-MobileMe-AuthToken ' + (icl_id + ':' + icl_token).encode("base64").strip()
      
      try:
         ioreg = subprocess.check_output("ioreg -rd1 -c IOPlatformExpertDevice -a".split())
         hw_uuid = plistlib.readPlistFromString(ioreg)[0]['IOPlatformUUID'] #UDID on iOS?
         ret['DEVICE_UUID'] = biplist.readPlist(os.path.expanduser("~/Library/Preferences/ByHost/com.apple.Safari.%s.plist" % hw_uuid))["SyncedTabsDeviceUUID"] #safari.app specific device id
         ret['DEVICE_NAME'] = subprocess.check_output(["scutil", "--get", "ComputerName"]).strip()
      except: #running on a non-mac?
         ret['DEVICE_UUID'] = subprocess.check_output(["uuidgen"]).strip() #systemd is workng on persistent uuid: http://man7.org/linux/man-pages/man5/machine-id.5.html
         ret['DEVICE_NAME'] = subprocess.check_output(["hostname", "-s"]).strip()
     
      for k,v in ret.items():
         print "%s = %s" % (k,v.__repr__())
