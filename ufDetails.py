#!/usr/bin/python
import sys, datetime, pytz, re
from pymongo import MongoClient
from collections import Counter
import mysql.connector


tenantCode=sys.argv[1];
summary=sys.argv[2];
created=sys.argv[3];


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

# def getDetails(ufData, tenantCode, date):
# 	# totalUFCount = len(ufData)
# 	# totalSoiCount = int(getTotalSOICount(tenantCode))

# 	if (ufData):
# 		channelIssue = Counter(tok['summary'] for tok in ufData)['CHANNEL_ISSUE']
# 		syncTimingIssue = Counter(tok['summary'] for tok in ufData)['SYNC_TIMING_ISSUE']
# 		operationalIssue = Counter(tok['summary'] for tok in ufData)['OPERATIONAL_ISSUE']
# 		facilityMappingIssue = Counter(tok['summary'] for tok in ufData)['FACILITY_MAPPING_ISSUE']
# 		inventoryFormulaIssue = Counter(tok['summary'] for tok in ufData)['INVENTORY_FORMULA_ISSUE']
# 		summaryUnavailable = Counter(tok['summary'] for tok in ufData)['SUMMARY_UNAVAILABLE']

# 		{
# 	"_id" : ObjectId("64a7e57e399d7502668db78a"),
# 	"saleOrderCode" : "Test30k1",
# 	"saleOrderItemCode" : "TestKeshav-0-0",
# 	"facilityAllocatorData" : {
# 		"facilityCode" : "05"
# 	},
# 	"created" : ISODate("2023-07-07T10:14:22.162Z")
# }

# 		if (totalSoiCount != 0):
# 			ufPercentage = round(((float(totalUFCount) / totalSoiCount) * 100), 3);
# 			nonOpsUf = channelIssue + syncTimingIssue + summaryUnavailable
# 			nonOpsUfPercentage = round(((float(nonOpsUf) / totalSoiCount) * 100), 3);

# 		summary = (tenantCode + "," 
# 			+ getTenantCategory(tenantCode) + "," 
# 			+ str(totalSoiCount) + "," 
# 			+ str(totalUFCount) + "," 
# 			+ str(ufPercentage) + "," 
# 			+ str(nonOpsUfPercentage) + "," 
# 			+ str(channelIssue) + "," 
# 			+ str(syncTimingIssue) + "," 
# 			+ str(operationalIssue) + "," 
# 			+ str(facilityMappingIssue) + "," 
# 			+ str(inventoryFormulaIssue) + "," 
# 			+ str(summaryUnavailable) + "," 
# 			+ str(date))

# 	# elif (len(ufData) == 0): 
# 	# 	details = (str(date))

# 	# else:
# 	# 	print("ufData length: " + str(len(ufData)))
# 	# 	summary = (tenantCode + "," 
# 	# 		+ getTenantCategory(tenantCode) + "," 
# 	# 		+ str(totalSoiCount) + "," 
# 	# 		+ str(totalUFCount) + "," 
# 	# 		+ ",,,,,,,," 
# 	# 		+ str(date))

# 	return summary


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

	midnightDateTime_today = datetime.datetime.today().replace(hour = 0, minute = 0, second = 0, microsecond = 0)
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
					"created" : created,
					"summary" : summary,
			}
			projection = {
				"saleOrderItemCode":1,
				"facilityAllocatorData.facilityCode":1,
				"saleOrderCode":1,
				"created":1
			}

			ufData = list(mycol.find(query, projection)) 			

			# Get Details
			# details = getDetails(ufData, tenantCode, str(ufSummaryDateStr))
			print(ufData)
			outputFile.write(ufData + "\n")

	except Exception as e:
		print("Exception while calculating uf data for tenant: " + tenant['code'])
		print(e)

except Exception as e:
	print(e)
	print(sys.exc_info()[0]);
	print("FAILED");

finally:
	outputFile.close()