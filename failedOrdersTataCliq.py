#!/usr/bin/python
import sys, datetime, pytz, re
from pymongo import MongoClient
from collections import Counter
import mysql.connector


tenantCodes=sys.argv[1]
detailsDated=sys.argv[2]

print(tenantCodes)
print(detailsDated)


def getClient(uri1, uri2):
	try:
		c = MongoClient(uri1, 27017)
		db= c['uniwareConfig']
		db.test.insert_one({})
		print(str(uri1))
	except:
		c = MongoClient(uri2, 27017)
		print(str(uri2) + " - common changed")
	return c




def getDetails(failedOrdersData, tenantCode):

	details=""
	
	if (len(failedOrdersData)>0):
		for theDetail in failedOrdersData:
			failedOrderCreatedTimeStamp=theDetail["created"].strftime("%d/%m/%Y")
			details = details + (theDetail["request"]["saleOrder"]["displayOrderCode"] +"," 
				+ theDetail["tenantCode"] + ","
				+ theDetail["request"]["saleOrder"]["channel"] +","
				+ theDetail["response"]["errors"][0]["message"] + ","
				+ theDetail["response"]["errors"][0]["description"] + ","
				+ failedOrderCreatedTimeStamp+"\n")
	elif (len(failedOrdersData) == 0): 
		details = (detailsDated)

	else:
		print("ufData length: " + str(len(failedOrdersData)))
		details = (tenantCode + "," 
			 + ","  + "," + "," )

	return details


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
	failedOrderColName = "saleOrder"


	midnightDateTime_today = datetime.datetime.now()
	midnightDateTime_backDays = midnightDateTime_today - datetime.timedelta(days=1)

	utcMidnightDateTime_today = midnightDateTime_today.astimezone(pytz.UTC)
	utcMidnightDateTime_backDays = midnightDateTime_backDays.astimezone(pytz.UTC)
	ufSummaryDate = midnightDateTime_today
	ufSummaryDateStr = ufSummaryDate.strftime("%d-%m-%Y")


	print("utcMidnightDateTime_today: " + str(utcMidnightDateTime_today))
	print("utcMidnightDateTime_15DaysBack: " + str(utcMidnightDateTime_backDays))
	print("ufSummaryDate: " + str(ufSummaryDate))

	# Create output file
	outputFileName = "/tmp/tataCliq-failedSaleOrders-" + detailsDated + ".csv"
	outputFile = open(outputFileName, "w")
	outputFile.write("OrderID,TenantID,ChannelCode,ErrorMessage,ErrorMessageSummary,FailureTimeStamp\n")

	# For specified tenant only
	for tenantCode in tenantCodes.split(","):
		try:
			# Get mongodbUri of tenant 			
			mongoUri = []
			mongoUri = getTenantSpecificMongoUri(tenantCode)

			if (len(mongoUri) == 2):
				# Create mongo client
				myclient = getClient(mongoUri[0], mongoUri[1])
				mydb = myclient[tenantCode]
				mycol = mydb[failedOrderColName]

				# Get FailedOrdersData

				query = {
						"tenantCode" : tenantCode,
						"request.saleOrder.channel":{
							"$regex" : "TATACLIQ"
						},
						"created" : { 
							"$gte" : utcMidnightDateTime_backDays, 
							"$lte" : utcMidnightDateTime_today
						},

					}
				
				projection = {
					"request.saleOrder.displayOrderCode":1,
					"tenantCode":1,
					"request.saleOrder.channel":1,
					"response.errors.message":1,
					"response.errors.description":1,
					"created":1
				}

				failedOrdersData = list(mycol.find(query, projection))
				print(str(failedOrdersData))

				# Get Details
				details = getDetails(failedOrdersData, tenantCode)
				print("------------")
				# print(details)
				# print(failedOrdersDetails)
				print("------------")
				outputFile.write(details + "\n")

		except Exception as e:
			print("Exception while calculating failedOrders data for tenant: " + tenantCode)
			print(e)

except Exception as e:
	print(e)
	print(sys.exc_info()[0])
	print("FAILED")

finally:
	outputFile.close()
