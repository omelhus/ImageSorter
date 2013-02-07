#!/usr/bin/python
import Image
from ExifTags import TAGS
import httplib
import simplejson as json
from urllib import urlencode
import time
import datetime
import os 
import shutil
import argparse

parser = argparse.ArgumentParser(description='Move images to folders based on date of capture and place')
parser.add_argument('input', help='Path to find images')
parser.add_argument('output', help='Base path to drop images')
parser.add_argument('-u', '--username', help="Username to use with Geonames.org", default="demo")
parser.add_argument('-y', help="Continue even if Geonames fails", default=False, type=bool, nargs='?', const=True)

args = parser.parse_args()

USERNAME=args.username
INPUTPATH=args.input
OUTPUTPATH=args.output

if USERNAME == "demo" :
	print "Username for Geonames is demo. This is not a good idea!"

def getDecimal (n) :
	d = float(n[0][0])/float(n[0][1]) + (float(n[1][0])/float(n[1][1]))/60 + (float(n[2][0])/float(n[2][1]))/3600
	return d

def getLocation (loc) :
	if loc == None :
		pass
	if loc != None and 2 in loc and 4 in loc :
		n = getDecimal(loc[2])
		e = getDecimal(loc[4])
		return (n, e)
	pass

def loadExif(filepath) :
	img = Image.open(filepath)
	exif = img._getexif()
	return (exif[34853], exif[36867])	

def getPlace(gps) :
	location = getLocation(gps)
	if(location != None) :
		try :
			(north, east) = location
			c = httplib.HTTPConnection("api.geonames.org");
			func = "findNearbyPostalCodesJSON"
			url = "/%s?username=%s&lang=no&lat=%s&lng=%s&maxRows=1" % (func, USERNAME, north, east);
			c.request("GET", url);
			response = c.getresponse();
			location = json.load(response);
			##return location['geonames'][0]['toponymName']
			city = location['postalCodes'][0]['adminName2']
			return city
		except Exception, e :
			if not args.y :
				print "Fetching city name failed. API credits used up?"
				print "If you want to continue anyway add -y to arguments"
				exit(1)
	pass

def formatDate(date, format="%Y-%m-%d") :
	exifformat = "%Y:%m:%d %H:%M:%S"
	parseddate = time.strptime(date, exifformat)
	fulldate = time.strftime(format, parseddate)
	return fulldate

def getPhotoPath(filename) :
	(gps, date) = loadExif(filename)
	locName = getPlace(gps)
	fulldate = formatDate(date, format="%Y/%Y-%m-%d")
	if(locName == None) :
		filepath = "%s" % fulldate
	else :
		filepath = "%s %s" % (fulldate, locName)
	return filepath

if not os.path.exists(INPUTPATH) :
	print "%s does not exist!" % INPUTPATH 
	exit(1)

for file in os.listdir(INPUTPATH) :
	if '.jpg' in file :
		try :
			fullfile = os.path.join(INPUTPATH, file)
			newpath = os.path.join(OUTPUTPATH, getPhotoPath(fullfile))
			if not os.path.exists(newpath) :
				os.makedirs(newpath)
			shutil.move(fullfile, os.path.join(newpath, file))
			print "%s	=>	%s/%s" % (file, newpath, file)
		except Exception, e :
			print "Couldn't read EXIF from %s (%s)" % (file, e)