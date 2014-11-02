#VIP QA Scripts
This folder contains the scripts which QA early and election-day voting sites. Each of the scripts are summarized below.


+  *readData.py* contains a very simple function (read()) which accepts a directory and a state abbreviation. Reads in a csv named {state abbreviation}.csv from the provided directory.


+  *civicInfo.py* interacts with the Google CivicInfo API. Contains 3 functions. 
..+  *getVoterInfo()* returns a decoded json object for the provided address string and electionID, by default the electionID is set to 4100-the 2014 General Election. 
..+  *getVIPValues()* accepts the object provided by getVoterInfo() and returns the election day polling location details.
..+  *getEVValue()* accepts the object provided by getVoterInfo() and returns the early-vote polling location details. 


+  *sheets.py* interacts with the Google Drive and Spreadsheets API's includes functions which can be used to copy a Google Sheet and then write rows to it. 
..+ *getService()* accepts as arguments the service name, version, and credential object. It creates and authorizes a service which can be used with the Google API client library
..+ *copySheet()* accepts as arguments a sheet name, an original sheet key, and a credentials object. It uses the Google API client library (and calls getService()) to copy a sheet template.
..+  *getClient()* creates a gData spreadsheets client and authorizes it using stored credentials (created in app/views.py)
..+  *convertRow()* accepts a dictionary with row values. It replaces the keys in the dictionary with lower-case, spaceless versions of themselves.
..+  *writeRow()* accepts a dictionary with row values, a gdata client, a sheetKey, and sheetID (sheet within the google spreadsheet). It converts the input dictionary using convertRow() and then writes it to the sheet provided.


+ *geocode.py* geocodes and finds the distance between address strings.
..+  *geocode()* accepts a string containing an address and returns a dictionary with the latitude (lat) and longitude (lng) of the best match for that address.
..+  *haversine()* accepts two location dictionaries and returns the haversine distance (in miles) between them. 


+ The scripts named *{state abbreviation}.py* each have a different structure based on the state on which they work. The unifying factor is a function titled *run()* which accepts a row dictionary from the TargetSmart data and returns the Polling Place ID, name, and address.


+ *execute.py* calls all of the other scripts in this folder to read and process VIP QA data.
..+  *getRowData()* accepts a row dictionary from TargetSmart data, and returns an address string and county which can be used to query the civicInfo API.
..+  *VIP()* accepts a state abbreviation and credentials object which reads in that state's TargetSmart data, creates a Google Spreadsheet, and then iterates over the data to query the civicInfo API, query the state lookup tool, and write the returned data to the new Google Spreadsheet.
..+  *EVIP()*: accepts a state abbreviation, a credentials object, and a boolean indicating whether to run 25 or 50 rows. This function reads in state Data, creates a google spreadsheet, and then iterates over rows querying the Google CivicInfo API and writing returned data to the new spreadsheet. No SOS tools were created for EV data.

