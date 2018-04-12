import os
import smtplib
from email.mime.text import MIMEText

EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')
EMAIL_SERVER = os.getenv('EMAIL_SERVER')


def send_alert_by_mail(temperature, humidity, alerttype):

    msg = MIMEText("Temperature in Server Room: " + str(temperature) + "\r\n" +
                   "Humidity in Server Room: " + str(humidity)
                   )


    msg['Subject'] = 'Server Room Climate ' + alerttype
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP(EMAIL_SERVER)
    s.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
    s.quit()


if __name__ == "__main__":
    print("Mail Test")
    print("EMail Sender:" + EMAIL_SENDER)
    print("EMail Receiver:" + EMAIL_RECEIVER)
    print("EMail Server:" + EMAIL_SERVER)
    send_alert_by_mail(0, 0, 'READER ALARM')

