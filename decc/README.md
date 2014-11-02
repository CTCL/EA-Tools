#DECC Processing Scripts

These scripts handle decc processing as managed by the Flask app. Each script is detailed below

+  *processScans.py* processes newly received digital or physical orders.
  +  *findClients()* accepts a psycopg2 cursor object and queries the DECC database to list clients.
  +  *getProject()* accepts a client ID and psycopg2 cursor object. It queries the DECC database and returns a list of projects associated with the provided client ID.
  +  *findOrders()* accepts a project ID and psycopg2 cursor object. It queries the DECC database and returns a list of orders associated with the provided project ID.
  +  *createOrder()* accepts a project ID and psycopg2 cursor object. It inserts a new order record into the DECC database.
  +  *findTypes()* accepts a project ID and psycopg2 cursor object. It queries the DECC database and returns a list of form types associated with the provided project ID.
  +  *createPart()* accepts an order ID, type ID, state, booleans indicating whether the order is rush, will be uploaded to van, matched to vendor, or sent to quad, a psycopg2 cursor object, and a psycopg2 db connection object. It inserts a new part record into the DECC database and returns the part ID.
  +  *obtainStartNum()* accepts a client ID and psycopg2 cursor object. It queries the DECC database and returns the next batch number associated with the given client.
  +  *processPDF()* is run for digitally transmitted orders. It accepts an input directory, output directory, starting batch number, part ID, psycopg2 cursor object, and psycopg2 database connection object. It iterates over every file listed recursively in the input directory and inserts a new batch record (including total pages) in the DECC database for each. It returns the ending batch number and the total number of pages processed.
  +  *processPhysical()* is run for physically shipped orders. It accepts an input file, output file, part ID, starting batch number, psycopg2 database connection object, psycopg2 cursor object, and order ID. It reads the input file and creates a new batch record for each row using the 'Batch Name' column in the input file. It the writes out all batches created with name and ID.
  +  *getCursor()* accepts a host, database, username, and password, and returns a psycopg2 cursor object and a psycopg2 database connection object.


+  *processXLSX.py* process returned data from the Data-entry vendor. 
  +  *getBatches()* accepts a psycopg2 cursor object and returns a dictionary listing all DECC batch information from the DECC database.
  +  *writeFile()* accepts a list of row dictionaries to be written, an output filename, and a list of headers. It writes out the list of dictionaries with the given headers to the output filename.
  +  *processXLSX()* accepts an input filename referencing an Excel file, a psycopg2 database connection object, and a psycopg2 cursor object. It reads in the excel file, and iterates over each row matching to its original batch name. It then updates batch entries with the final number of records.
  +  *main()* accepts a boolean indicating whether a file contains VR records, an input filename, and an output filename. It connects to the DECC database, reads in the input file, runs processXLSX, and calls vrqc.py if the file is voter registration. It then outputs to the output file.

+  *vrqc.py* runs quality checks on returned voter registration data.
  +  *readCSV()* accepts a filename and returns a list of dictionaries containing data for each row.
  +  *writeCSV()* accepts a list of dictionaries containing row data, an output filename, and a list of headers. It writes the list of dictionaries out to the output filename using the list of headers.
  +  *getFIPS()* accepts a url containing FIPS code translation data. It returns a dictionary mapping FIPS codes to county names, and a dictionary mapping county names to state abbreviations.
  +  *getZipURL()* accepts the URL of the page listing HUD zip-FIPS code mapping files, and obtains the URL of the most recent HUD file mapping Zip Codes to county FIPS codes.
  +  *getZips()* accepts a URL of a HUD file mapping zip codes to county FIPS codes. It returns a list of dictionaries with keys ZIP and FIPS.
  +  *buildZipTranslator()* accepts the FIPS dictionary created in getFIPS(), and the list created by getZips() and creates a single dictionary with zip codes as keys, and as values, a list of dictionaries with STATE and COUNTY as keys
  +  *inspectRows()* accepts the list of row dictionaries, the zip translator, and the stateDict. It iterates over each row of voter registration data and checks whether the data included make any sense. It returns an updated list of row dictionaries, and an aggregate report.
  +  *report()* writes out as JSON the object passed to it as an argument.
  +  *concatenateFields()* concatenates the values for addresses and dates to create values that are more acceptable to VAN.
  +  *run()* accepts as argument the list of Dictionaries from processXLSX.py, and returns a final QC'd version of that list.
