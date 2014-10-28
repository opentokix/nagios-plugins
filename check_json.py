#!/usr/bin/env python
"""
Copyright (c) 2014, Peter Eriksson
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of the FreeBSD Project.


Plugin to check json output from a http status server and report on
exactly one key


This is an example of a json file provided by http server
{
   "rotator": {
      "ads": "1000",
      "threads": "10",
      "heap-usage":  "70",
      "gc": "1.5"
   },
   "bidder": {
      "bids": "543",
      "bidspersec": "10",
      "threads": "25",
      "heap-usage":  "70",
      "gc": "1.5"
   }

}
"""
import sys
import getopt
import urllib2
import json

def usage():
	print """
	This plugin opens and url with simple json
	parses the result and report warning for a single key
	written to be very versatile and compatible with nrpe
	options:
		-w warning (int) mandatory
		-c critical (int) mandatory
		-k minor_key (string) mandatory
		-K major_key (string) mandatory
		-U url (string) mandatory
		-L lazy Reports OK when key not found optional
		-h print help
	"""

def plugin_exit(code, message):
	print message
	sys.exit(code)

def sanity_check(warn, crit):
	# Perform some sanity checks for the plugin.
	# Making sure the server reports 200 and warning and critical
	# is correct values compared to each other.

	if warn > crit:
		usage()
		plugin_exit(2, "Warning is above critical value, that does not make sense")

def search_json_and_report(major_key, key, data, strict = True):
	# Search json data for key and report if
	# ok, warning or critcal
	# report unknown if key not found unless strict is False
	try:
		return float(data[major_key][key])
	except KeyError:
		if strict == False:
			plugin_exit(RETURN_OK, "OK: Key was not found by lazy flag is set")
		else:
			plugin_exit(RETURN_UNKNOWN, "UNKNOWN: Key not found")

def analyze_value_and_exit(value, warn, crit):
	if value > crit:
		exit_code = RETURN_CRITICAL
		report = "CRITICAL: Value is " + str(value) + " and critical limit is " + str(crit)
	elif value > warn:
		exit_code = RETURN_WARNING
		report = "WARNING: Value is " + str(value) + " and warning limit is " + str(warn)
	elif value < warn:
 		exit_code = RETURN_OK
		report = "OK: Value is " + str(value)
	else:
		exit_code = RETURN_UNKNOWN
		report = "UNKNOWN: Value is unparasble but here it is: " + str(value)

	plugin_exit(exit_code, report)

def main(argv):
	# Global flags and variables
	global RETURN_OK
	global RETURN_WARNING
	global RETURN_CRITICAL
	global RETURN_UNKNOWN
	# Return out of bounds is for exit codes 0,1,2,3 is reserved for nagios
	# To see if its implmentation error, or a error for the check with exit codes
	# when used with nagios etc.

	global RETURN_OUTOFBOUNDS

	FLAG_STRICT = True

	RETURN_OK = 0
	RETURN_WARNING = 1
	RETURN_CRITICAL = 2
	RETURN_UNKNOWN = 3
	RETURN_OUTOFBOUNDS = 255

	try:
		opts, args = getopt.getopt(argv, 'w:c:k:K:U:h:L')
	except getopt.GetoptError:
		usage()
		plugin_exit(RETURN_OUTOFBOUNDS, "Error: Out of bounds")

	# Parse options, and die if we get unexpected options
	for opt, arg in opts:
		if opt in ('-h'):
			usage()
			sys.exit(RETURN_OUTOFBOUNDS)
		elif opt in ('-w'):
			warning_treshold = float(arg)
		elif opt in ('-c'):
			critical_treshold = float(arg)
		elif opt in ('-k'):
			minor_key = arg
		elif opt in ('-K'):
			major_key = arg
		elif opt in ('-U'):
			URL = arg
		elif opt in ('-L'):
			FLAG_STRICT = False
		else:
			usage()
			sys.exit(RETURN_OUTOFBOUNDS)

	# ugly try block for non optinal variables, but to avoid making them global
	try:
		major_key
	except NameError:
		usage()
		plugin_exit(RETURN_OUTOFBOUNDS, "major key not defined")
	try:
		minor_key
	except NameError:
		usage()
		plugin_exit(RETURN_OUTOFBOUNDS, "minor key not defined")

	try:
		warning_treshold
	except NameError:
		usage()
		plugin_exit(RETURN_OUTOFBOUNDS, "Warning not defined")

	try:
		critical_treshold
	except NameError:
		usage()
		plugin_exit(RETURN_OUTOFBOUNDS, "Critical not defined")

	try:
		URL
	except NameError:
		usage()
		plugin_exit(RETURN_OUTOFBOUNDS, "URL not defined")

	# Make sure the url handles error elegant
	try:
		response = urllib2.urlopen(URL);
	except urllib2.HTTPError, e:
		usage()
		message = "Server reported: " + str(e.code)
		plugin_exit(RETURN_OUTOFBOUNDS, message)

	try:
		json_data = json.loads(response.read())
	except ValueError as e:
		message = "%s: %r", e, response.read()
		plugin_exit(RETURN_OUTOFBOUNDS, message)

	sanity_check(warning_treshold, critical_treshold)

	value = search_json_and_report(major_key, minor_key, json_data, FLAG_STRICT)
	analyze_value_and_exit(value, warning_treshold, critical_treshold)

if __name__ == '__main__':
	main(sys.argv[1:])