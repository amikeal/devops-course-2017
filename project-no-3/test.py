import re
import os.path
from urllib.request import urlretrieve
from datetime import datetime

URL_PATH = 'https://s3.amazonaws.com/tcmg476/http_access_log'
LOCAL_FILE = 'local_copy.log'
ERRORS = []

# Counters
t300_count = 0
t400_count = 0
total_count = 0

# Dicts to store aggregate counts
COUNT_REQS_MON = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0}
STORE_REQS_MON = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [], 10: [], 11: [], 12: []}

# check to see if we can use a cached copy
if not os.path.isfile(LOCAL_FILE):
    print("Downloading file from URL...")
    local_file, headers = urlretrieve(URL_PATH, LOCAL_FILE, lambda x,y,z: print('.', end='', flush=True) if x % 100 == 0 else False)
    print("\nFile retrieved and saved to disk: {}".format(LOCAL_FILE))

# get the filehandle
fh = open(LOCAL_FILE)

#prepare the REgEx
regex = re.compile(".*\[([^:]*):(.*) \-[0-9]{4}\] \"([A-Z]+) (.+?)( HTTP.*\"|\") ([2-5]0[0-9]) .*")

# tell the user what's happening...
print("Parsing log file...")

# Loop through each line of the file
for line in fh:
    # split the line into parts
    parts = regex.split(line)

    # sanity check the parts list
    if not parts or len(parts) < 7:
        #print("Error parsing line! Log entry added to ERRORS[] list...")
        ERRORS.append(line)
        continue

    # increment the total counter
    total_count += 1

    # check the status code
    if parts[6][0] == '3':
        t300_count += 1
    
    if parts[6][0] == '4':
        t400_count += 1
    
    # parse the date into a date object
    r_date = datetime.strptime(parts[1], "%d/%b/%Y")

    # track the counts by month
    COUNT_REQS_MON[r_date.month] += 1
    STORE_REQS_MON[r_date.month].append(line)


# write out the log files separate into month files
print("Writing all log entries into separate files per month...")
for key, val in STORE_REQS_MON.items():
    # so inside this loop, the key is the month digit and the val is
    #   the list of all lines from the log that belong to that month
    mon_fname = "{}.log".format(key)
    print("  ...writing {}".format(mon_fname))
    mon_fh = open(mon_fname, 'w')
    mon_fh.writelines(val)
    mon_fh.close()


# Print out all the info to the user
print("Total requests: {}".format(total_count))
print("40x errors: {}".format(t400_count))
print("30x errors: {}".format(t300_count))
print("Total requests by month: {}".format(COUNT_REQS_MON))
print("# errors seen in log file: {}".format(len(ERRORS)))
