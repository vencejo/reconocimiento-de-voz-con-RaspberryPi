# -*- coding: utf-8-*-
import os
import re
from getpass import getpass
import yaml
from pytz import timezone
import feedparser
import jasperpath

def run():
	profile = {}
	
	print("Welcome to the profile populator. If, at any step, you'd prefer " +
		  "not to enter the requested information, just hit 'Enter' with a " +
		  "blank field to continue.")
	
	def simple_request(var, cleanVar, cleanInput=None):
		input = raw_input(cleanVar + ": ")
		if input:
			if cleanInput:
				input = cleanInput(input)
			profile[var] = input
	
	# name
	simple_request('first_name', 'First name')
	simple_request('last_name', 'Last name')
	
	# gmail
	print("\nJasper uses your Gmail to send notifications. Alternatively, " +
		  "you can skip this step (or just fill in the email address if you " +
		  "want to receive email notifications) and setup a Mailgun " +
		  "account, as at http://jasperproject.github.io/documentation/" +
		  "software/#mailgun.\n")
	simple_request('gmail_address', 'Gmail address')
	profile['gmail_password'] = getpass()
	
	# location
	def verifyLocation(place):
		feed = feedparser.parse('http://rss.wunderground.com/auto/rss_full/' +
								place)
		numEntries = len(feed['entries'])
		if numEntries == 0:
			return False
		else:
			print("Location saved as " + feed['feed']['description'][33:])
			return True
	
	print("\nLocation should be a 5-digit US zipcode (e.g., 08544). If you " +
		  "are outside the US, insert the name of your nearest big " +
		  "town/city.  For weather requests.")
	location = raw_input("Location: ")
	while location and not verifyLocation(location):
		print("Weather not found. Please try another location.")
		location = raw_input("Location: ")
	if location:
		profile['location'] = location
	
	# timezone
	print("\nPlease enter a timezone from the list located in the TZ* " +
		  "column at http://en.wikipedia.org/wiki/" +
		  "List_of_tz_database_time_zones, or none at all.")
	tz = raw_input("Timezone: ")
	
	try:
		timezone(tz)
		profile['timezone'] = tz
	except:
		print("Not a valid timezone. We asing you the Madrid Timezonde")
		tz = "Europe/Madrid"
	
	profile['prefers_email'] = True
	
	stt_engines = {
		"ibm": "IBM",
		"att": "ATT"
	}
	
	response = raw_input("\nIf you would like to choose a specific STT " +
					 "engine, please specify which.\nAvailable " +
					 "implementations: %s" % stt_engines.keys() + 
					  " Press Enter to default AT&T ")
	
	if not response.lower() in stt_engines.keys():
		response = "at&t"
		
	profile["stt_engine"] = stt_engines[response]
		
	api_key_name = stt_engines[response]
	
	key1 = raw_input("\nPlease enter your API key or user name: ")
	key2 = raw_input("\nPlease enter your API secret or password: ")
	profile["keys"] = {"USER": key1, "PASS": key2}
	
	# write to profile
	print("Writing to profile...")
	if not os.path.exists(jasperpath.CONFIG_PATH):
		os.makedirs(jasperpath.CONFIG_PATH)
	outputFile = open(jasperpath.config("profile.yml"), "w")
	yaml.dump(profile, outputFile, default_flow_style=False)
	print("Done.")

if __name__ == "__main__":
    run()
