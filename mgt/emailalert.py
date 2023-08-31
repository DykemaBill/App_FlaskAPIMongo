# For local testing, you can use the following relay server
# python3 -m smtpd -c DebuggingServer -n localhost:25

import sys, smtplib
from email.mime.text import MIMEText
import email.utils
import re

# Send email message
def send_email(email_smtp, email_sender, email_receiver, email_subject, email_message):
    for email_address in re.split(r',|;|:', email_receiver):
        email_content = MIMEText(email_message, _charset='UTF-8')
        email_content['Subject'] = email_subject
        email_content['Message-ID'] = email.utils.make_msgid()
        email_content['Date'] = email.utils.formatdate(localtime=1)
        email_content['From'] = email_sender
        for email_to_line in re.split(r',|;|:', email_receiver):
            email_content['To'] = email_to_line
        try:
            smtpObj = smtplib.SMTP(email_smtp, port=25, local_hostname=None, timeout=5)
            smtpObj.sendmail(email_sender, email_address, email_content.as_string())         
            smtpObj.quit()
        except Exception as email_error:
            print ("Email failure error: " + str(email_error))
            return False
    return True

# Get command line arguments
if __name__ == "__main__":
    if len(sys.argv) == 6:
        email_smtp = sys.argv[1]
        email_sender = sys.argv[2]
        email_receiver = sys.argv[3]
        email_subject = sys.argv[4]
        email_message = sys.argv[5]
        print ("Email server:", email_smtp)
        print ("Email from:", email_sender)
        print ("Email to:", email_receiver)
        print ("Email subject:", email_subject)
        print ("Email message:", email_message)
        email_delivered = send_email(email_smtp, email_sender, email_receiver, email_subject, email_message)
        if (email_delivered):
            print ("Email message was delivered!")
        else:
            print ("Email message delivery failed!")
    else:
        print ("Syntax:")
        print ("        " + sys.argv[0] + " 'smtp server name' 'emailfrom@somewhere.com' 'emailto@somewhere.com' 'Email Subject' 'Email message here!'")