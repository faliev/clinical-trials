#!/usr/bin/python

from collections import defaultdict
import os, os.path, subprocess
from datetime import datetime as dt
import datetime, calendar
import locale

def main():
	ACTList = getACTList()
	fines = defaultdict(int)
	allFines = 0
	locale.setlocale(locale.LC_ALL, 'en_US')
	
	
	for root, _, files in os.walk("study_fields_xml"):
		for index, file in enumerate(files):
			fullpath = os.path.join(root, file)

			trial = Trial(fullpath)
			trial.populate()
			
			if index == 0:
				print trial.outputHeader()
			
			if trial.isACT():
				print trial.outputLine()
				
				# calculate fines
				fine = trial.fine()
				fines[trial.sponsorClass] += fine
				allFines += fine
		
		print "\n"
		
		# print fines by class
		for key, value in fines.iteritems():
			percent = (float(value) / float(allFines)) * 100
			print percent
			print "%s = %d%% (%s)" % (key, percent, locale.format("%d", value, grouping=True))
		
		print "Total Fines: $" + locale.format("%d", allFines, grouping=True)
		print "\n" # end the file with a newline



def getACTList():
	return [line.strip() for line in open('Prayle ACTs.txt')]



def addMonths(sourcedate, months):
	month = sourcedate.month - 1 + months
	year = sourcedate.year + month / 12
	month = month % 12 + 1
	day = min(sourcedate.day, calendar.monthrange(year, month)[1])
	
	return sourcedate.replace(year, month, day)



class Trial(object):
	def __init__(self, path):
		self.path = path
		self.fields = []
		
		# Header fields
		self.headerFields = ['NCT ID', 'Lead Sponsor', 'Sponsor Class', 'Recruitment', 'Interventions',
							 'Start Date', 'Completion Date', 'Primary Completion Date', 'Results Date',
							 'Phase', 'Countries']
		
		# Field variables
		self.id = os.path.splitext(os.path.basename(path))[0]
		self.leadSponsor = ""
		self.sponsorClass = ""
		self.recruitment = ""
		self.interventions = ""
		self.startDate = None
		self.completionDate = None
		self.primaryCompletionDate = None
		self.resultsDate = None
		self.phase = ""
		self.countries = ""
	
	
	
	def populate(self):
		self.runXSLT()
		self.processFields()

	###
	# Getting the data and parsing it
	###
	def runXSLT(self):
		result = subprocess.check_output(["xsltproc", "process_xml.xslt", self.path])
		fieldString = result.split("\n")[2] # 0 = XML declaration; 1 = header; 2 = the good stuff
		
		if (len(fieldString)):
			self.fields = fieldString.split("\t")
	
	
	
	def processFields(self):
		(self.leadSponsor,
		 self.sponsorClass,
		 self.recruitment,
		 self.interventions,
		 self.startDate,
		 self.completionDate,
		 self.primaryCompletionDate,
		 self.resultsDate,
		 self.phase,
		 self.countries) = self.fields[1:]
		 
		# Date munging
		self.startDate = self.parseDate(self.startDate)
		self.completionDate = self.parseDate(self.completionDate)
		self.primaryCompletionDate = self.parseDate(self.primaryCompletionDate)
		self.resultsDate = self.parseDate(self.resultsDate)
	
	
	
	def parseDate(self, dateString):
		outDate = datetime.date(datetime.MINYEAR, 1, 1) # MINYEAR = invalid date
		
		if len(dateString):
			try:
				outDate = dt.strptime(dateString, '%B %d, %Y').date()
			except Exception as e:
				try:
					outDate = dt.strptime(dateString, '%B %Y').date()
				except Exception as e:
					print "Failed parsing date for %s, '%s': %s" % (self.id, dateString, e)
		
		return outDate
	
	
	
	###
	# Calculating whether the FDAAA applies to the trial (ACT = Applicable Clinical Trial)
	###
	
	def isACT(self):
		return self.meetsDateRequirements() and \
			   self.isPhase2Plus() and \
			   self.tookPlaceInTheUS() and \
			   self.hasApplicableIntervention()
	
	def meetsDateRequirements(self):
		initiationCutoff = datetime.date(2007, 9, 27)
		ongoingCutoff = datetime.date(2007, 12, 26)
		invalidDate	= datetime.date(datetime.MINYEAR, 1, 1) 
		
		initiationApplies = self.startDate > initiationCutoff
		completionApplies = (self.completionDate >= ongoingCutoff or
							 self.primaryCompletionDate >= ongoingCutoff)
		noStartDate		  = self.startDate == invalidDate
		noCompletionDate  = (self.completionDate == invalidDate and \
							 self.primaryCompletionDate == invalidDate)
		
		return initiationApplies or (not noStartDate and (noCompletionDate or completionApplies))
	
	def isPhase2Plus(self):
		return not (self.phase == "Phase 0" or self.phase == "Phase 1")
	
	def tookPlaceInTheUS(self):
		return "United States" in self.countries
	
	def hasApplicableIntervention(self):
		return any(x in self.interventions for x in ["Drug", "Biological", "Device"])
	
	
	
	###
	# And Prayle
	###
	
	def includedInPrayle(self):
		return self.primaryCompletionDate >= datetime.date(2009, 01, 01) and \
			   self.primaryCompletionDate <  datetime.date(2010, 01, 01)
	
	
	
	###
	# Calculating how much the trial owes
	###
	
	def fine(self):
		fine = 0
		
		if self.resultsDate:
			# Since the XML doesn't tell us the day on which the trial ended, work from the beginning of the next month
			fineStartDate = addMonths(self.primaryCompletionDate, 1)
			
			# The responsible person has a year to submit the trial results
			fineStartDate = addMonths(fineStartDate, 12)
			
			# The secretary issues a notice, which presumably has to arrive in the mail...
			fineStartDate += datetime.timedelta(days=7)
			
			# And the responsible person is allowed 30 days to comply
			fineStartDate += datetime.timedelta(days=30)
			
			fineLength = datetime.date.today() - fineStartDate
			fine = fineLength.days * 10000
		
		return fine


	
	###
	# Output
	###
	def outputHeader(self):
		return "\t".join(self.headerFields)
	
	def outputLine(self):
		return "\t".join(self.fields)

# Default function is main()
if __name__ == '__main__':
	main()
