#EA-Tools 2014
This repository contains a flask app which managed processes for VIP QA and DECC through the 2014 Election. VIP-specific scripts are stored in the vip folder, and decc-specific scripts are stored in the decc folder. Each folder, except app, contains its own README detailing the included scripts.


##For this app to run, the following environment variables must be defined:
###For DECC:
+  *DECCINPUT:* the directory to use to input to decc scripts
+  *DECCOUTPUT:* the directory to output decc files after processing
+  *PGHOST:* the URL or IP of the DECC database server
+  *PGUSER:* the username to connect to the DECC database
+  *PGPASSWORD:* the password associated with PGUSER
+  *PGDB:* the DECC database name

###For VIP QA:
+  *GOOGLE_NATIVE_APP_CLIENT_ID:* The client ID associated with the VIP QA app
+  *GOOGLE_NATIVE_APP_CLIENT_SECRET:* The client secret associated with the VIP QA app
+  *GOOGLE_PUBLIC_API_KEY:* The API key used to query the Google civicInfo API
+  *GOOGLE_GEOCODE_API_KEY:* The API key used to query the Google geocode API
+  *VIPQADATA:* The directory containing TargetSmart PII spreadsheets used to QA election-day voting sites 
+  *EVIPQADATA:* The directory containing TargetSmart PII spreadsheets used to QA early voting sites
