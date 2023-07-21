#!/usr/bin/python
import sys, datetime, pytz, re
from pymongo import MongoClient
from collections import Counter
import mysql.connector


tenantCode=sys.argv[1];
detailsDated=sys.argv[2];
summary=sys.argv[3];

print(tenantCode)
print(summary)
print(detailsDated)


def getClient(uri1, uri2):
	try:
	    c = MongoClient(uri1, 27017);
	    db= c['uniwareConfig'];
	    db.test.insert_one({});
	    print(str(uri1))
	except:
	    c = MongoClient(uri2, 27017);
	    print(str(uri2) + " - common changed")

	return c


def ifDetailsExists(ufData):
	for data in ufData:
		if ("saleOrderCode" not in data):
			return False

	return True


# def getTenantCategory(tenantCode):
# 	for tenant in tenantList:
# 		if (tenantCode == tenant['code']):
# 			return tenant['category']

# 	return ""

def getDetails(ufData, tenantCode):

	details=""
	
	if (len(ufData)>0):
		for theDetail in ufData:
			unfTS=theDetail["unfulfillableTimeStamp"].strftime("%d/%m/%Y")
			details = details + (tenantCode + "," 
				+ theDetail["saleOrderCode"] +"," 
				+ theDetail["saleOrderItemCode"] + "," 
				+ theDetail["facilityAllocatorData"]["facilityCode"] + "," 
				+ unfTS+"\n")
	elif (len(ufData) == 0): 
		details = (detailsDated)

	else:
		print("ufData length: " + str(len(ufData)))
		details = (tenantCode + "," 
			 + ","  + "," + "," )

	return details;


def getServerNameFromTenant(tenantCode):
	commonMongoUri1 = "common1.mongo.unicommerce.infra:27017"
	commonMongoUri2 = "common2.mongo.unicommerce.infra:27017"
	commonMongoClient = getClient(commonMongoUri1, commonMongoUri2)
	db = commonMongoClient['uniware']
	col = db['tenantProfile']

	return col.find_one({"tenantCode" : tenantCode})['serverName']


def getTenantSpecificMongoFromServerName(serverName):
	commonMongoUri1 = "common1.mongo.unicommerce.infra:27017"
	commonMongoUri2 = "common2.mongo.unicommerce.infra:27017"
	commonMongoClient = getClient(commonMongoUri1, commonMongoUri2)
	db = commonMongoClient['uniwareConfig']
	col = db['serverDetails']

	return col.find_one({"name" : serverName})['tenantSpecificMongoHosts']


def getTenantSpecificMongoUri(tenantCode):
	serverName = getServerNameFromTenant(tenantCode)
	print(tenantCode + ", Server Name: " + serverName)
	mongoUri = []
	if (serverName):
		mongoUri = getTenantSpecificMongoFromServerName(serverName)
		print("Server Name: " + serverName + ", mongoUri: " + str(mongoUri))
	else :
		print("Cannot find serverName for " + str(tenantCode))

	return mongoUri




# 										-- Main --
try:
	ufColName = "unfulfillableItemsSnapshot"


	midnightDateTime_today = datetime.datetime.strptime(detailsDated, '%d-%m-%Y')
	midnightDateTime_yesterday = midnightDateTime_today - datetime.timedelta(days = 1)

	utcMidnightDateTime_today = midnightDateTime_today.astimezone(pytz.UTC)
	utcMidnightDateTime_yesterday = midnightDateTime_yesterday.astimezone(pytz.UTC)
	ufSummaryDate = datetime.date.today() - datetime.timedelta(days = 1)
	ufSummaryDateStr = ufSummaryDate.strftime("%d-%m-%Y")

	totalSoiCountFromDate = ufSummaryDate.strftime("%Y-%m-%d")
	totalSoiCountToDate = datetime.date.today().strftime("%Y-%m-%d")

	print("utcMidnightDateTime_today: " + str(utcMidnightDateTime_today))
	print("utcMidnightDateTime_yesterday: " + str(utcMidnightDateTime_yesterday))
	print("ufSummaryDate: " + str(ufSummaryDate))

	# Create output file
	outputFileName = "/tmp/uf-details-" + ufSummaryDateStr + ".csv"
	outputFile = open(outputFileName, "w")
	outputFile.write("TenantCode,SaleOrderCode,SaleOrderItemCode,FacilityCode,Created\n")

	# For specified tenant only
	try:
		# Get mongodbUri of tenant 			
		mongoUri = []
		mongoUri = getTenantSpecificMongoUri(tenantCode)

		if (len(mongoUri) == 2):
			# Create mongo client
			myclient = getClient(mongoUri[0], mongoUri[1])
			mydb = myclient[tenantCode]
			mycol = mydb[ufColName]

			# Get ufData
			query = {
					"tenantCode" : tenantCode,
					"unfulfillableTimeStamp" : { 
						"$gte" : utcMidnightDateTime_yesterday, 
						"$lte" : utcMidnightDateTime_today 
					},
					"summary" : summary,
			}
			projection = {
				"saleOrderItemCode":1,
				"facilityAllocatorData.facilityCode":1,
				"saleOrderCode":1,
				"unfulfillableTimeStamp":1
			}

			ufData = list(mycol.find(query, projection)) 			

			# Get Details
			details = getDetails(ufData, tenantCode)
			print("------------")
			print(details)
			# print(ufData)
			print("------------")
			# outputFile.write(details + "\n")

	except Exception as e:
		print("Exception while calculating uf data for tenant: " + tenantCode)
		print(e)

except Exception as e:
	print(e)
	print(sys.exc_info()[0]);
	print("FAILED");

finally:
	outputFile.close()