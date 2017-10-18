import urllib2
import re
import sys
from datetime import datetime

# Config options
REMOTE_URL = 'http://physis.arch.tamu.edu/files/http_access_log'
LOCAL_FILE = 'http_access_log.bak'
LOG_PATH = 'logs/'

# Initialize some variables
i = 0
requests_by_month = {}
files = {}
counts = {}
errors = []

# Fetch the file from the remote server and save it to disk
print "\n\nDownloading log file from URI... "
response = urllib2.urlopen(REMOTE_URL)
with open(LOCAL_FILE, "wb") as local:
	local.write(response.read())
print "File retrieved and saved to disk (%s) \n\n" % LOCAL_FILE

# Prepare the regex...
regex = re.compile(".*\[(.*) \-[0-9]{4}\] \"([A-Z]+) (.+?)( HTTP.*\"|\") ([2-5]0[0-9]) .*")

# Loop through each line of the file on disk
for line in open(LOCAL_FILE, 'r'):

	# A simple progress meter
	i += 1
	if i % 1000 == 0:
		print ".",
	
	# Use Regex to split the line into parts
	parts = regex.split(line)
	print parts

	# Sanity check the line -- capture the error and move on
	if not parts or len(parts) < 7:
		print "Error parsing line! Log entry added to errors[] list..."
		errors.append(line)
		continue

	# Parse the date from the second array element
	entry_date = datetime.strptime(parts[1], "%d/%b/%Y:%H:%M:%S")

	print entry_date