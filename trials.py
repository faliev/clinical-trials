#!/usr/bin/python

import argparse
import trialsDB.trialsDB as db
import trialCharts.trialCharts as charts
import os

def main():
	# Handle the arguments
	args = parseArguments()

	# Create the database if requested
	if args.dbPath is not None:
		if args.xmlFilesPath is None:
			print "If you're going to create a database, you must pass in the path to the XML files directory"
			return 0
		else:
			db.create(args.dbPath, args.xmlFilesPath, args.startID, args.limit)

	# Create the charts
	chartsPath = "web/"
	if args.chartsPath is not None:
		chartsPath = args.chartsPath

	charts.create(chartsPath)




def parseArguments():
	parser = argparse.ArgumentParser(description='Manage and data mine a clinical trials database')
	parser.add_argument('--create-db', dest='dbPath',
						help='create and initalize the DB file using the path provided')
	parser.add_argument('--xmlFilesPath', dest='xmlFilesPath',
						help='a directory of trials in ClinicalTrials.gov\'s XML format')
	parser.add_argument('--chartsPath', dest='chartsPath',
						help='choose a destination for the HTML/JS files containing the charts, defaults to "web/"')
	parser.add_argument('--limit', dest='limit', type=int,
						help='set a limit on the number of files from the XML path to be included')
	parser.add_argument('--startID', dest='startID', help='choose an NCT ID to start from')
						
	return parser.parse_args()



# Default function is main()
if __name__ == '__main__':
    main()