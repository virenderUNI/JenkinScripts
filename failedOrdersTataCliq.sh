TenantCodes=$1
DetailsDated=$2
Recipient=$3
python3 ufDetails.py "$TenantCodes" "$DetailsDated"

# yesterday_date=$(date -d "$DetailsDated" +'%d-%b-%Y')

# echo ${yesterday_date}

temp=/tmp/tataCliq-failedSaleOrders-
temp+=${DetailsDated}
temp+='.csv'

echo ${temp}

ls ${temp}

reportFilename=`ls ${temp}`
echo "Report file: ${reportFilename}"

MAIL_RECIPIENTS="virender.singh@unicommerce.com,"
MAIL_RECIPIENTS+=$3

echo ${MAIL_RECIPIENTS}

MAIL_SUBJECT="TataCliq Failed SaleOrdersDetails"
MAIL_CONTENT="Please find the attachment. Report prepared by APP team"

echo ${MAIL_CONTENT} | mutt -s "${MAIL_SUBJECT}" -a "${reportFilename}" -- "${MAIL_RECIPIENTS}"
