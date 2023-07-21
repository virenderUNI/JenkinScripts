TenantCode=$1
DetailsDated=$2
Summary=$3

python3 ufDetails.py "$TenantCode" "$DetailsDated" "$Summary"

yesterday_date=$(date -d "$DetailsDated" +'%d-%b-%Y')

temp=/tmp/uf-summary-
temp+=${yesterday_date}

ls ${temp}



reportFilename=`ls ${temp}`
echo "Report file: ${reportFilename}"

# MAIL_RECIPIENTS="sourabh.shrivastava@unicommerce.com,dixit.garg@unicommerce.com,ankur.pratik@unicommerce.com,ankit.jain03@unicommerce.com,bhupi@unicommerce.com,kapil@unicommerce.com,prateek.mahajan@unicommerce.com,adarsh.bajpai@unicommerce.com,rakshit.jain@unicommerce.com,oncall@unicommerce.com"

MAIL_RECIPIENTS="virender.singh@unicommerce.com"

MAIL_SUBJECT="Unfulfillable Sale Order Details | ${yesterday_date}"
MAIL_CONTENT="Please find the attachment. Report prepared by alpha team"

echo ${MAIL_CONTENT} | mutt -s "${MAIL_SUBJECT}" -a "${reportFilename}" -- "${MAIL_RECIPIENTS}"