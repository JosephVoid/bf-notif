import os, sys, ast
import pika
import time
import smtplib
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from email.mime.text import MIMEText

load_dotenv()

sms_queue = os.environ["RBT_MQ_SMSQ"]
email_queue = os.environ["RBT_MQ_EMLQ"]


def log(output: str):
    with open("log.txt", "a+", encoding="UTF-8") as f:
        f.writelines(time.ctime(time.time()) + " : " + f"{output}" + "\n")


def send_sms(to: str, msg: str) -> bool:
    payload = {"message": msg, "phoneNumbers": [to]}
    try:
        response = requests.post(
            os.environ["SMS_URL"],
            auth=HTTPBasicAuth(os.environ["SMS_USR"], os.environ["SMS_PSS"]),
            data=payload,
        )
        log(str(response.status_code) + "-:-" + response.text)
        if response.status_code >= 200 or response.status_code < 210:
            log(payload)
            return True
        else:
            return False
    except Exception as e:
        print(e)
        log(e)
        return False


def send_email(to: str, body: str, subject: str):
    try:
        email_msg = MIMEText(f"{body}", "plain")
        email_msg["Subject"] = subject
        email_msg["From"] = os.environ["EML_USR"]

        with smtplib.SMTP(os.environ["EML_SRV"], int(os.environ["EML_PRT"])) as smtp:
            os.environ["EML_SRV"], int(os.environ["EML_PRT"])
            smtp.starttls()
            smtp.login(os.environ["EML_USR"], os.environ["EML_PSS"])
            smtp.sendmail(os.environ["EML_USR"], to, email_msg.as_string())
            return True
    except Exception as e:
        print(e)
        return False


def on_sms_receive(ch, method, props, body: bytes):
    # Capture received message to file
    log(body)

    # Parse the byte to a dict
    msg = ast.literal_eval(body.decode("UTF-8"))
    print(
        time.ctime(time.time()) + " : to-> " + msg["to"] + "   msg-> " + msg["message"]
    )
    log("Received : to-> " + msg["to"] + "   msg-> " + msg["message"])
    if send_sms(msg["to"], msg["message"]):
        # Acknowledge the message
        ch.basic_ack(method.delivery_tag)
        log("Message acknowledged")
    else:
        ch.basic_nack(method.delivery_tag, requeue=True)
        print("Unable to send message")
        log("Unable to send message")


def on_email_receive(ch, method, props, body: bytes):
    # Capture received message to file
    log(body)

    # Parse the byte to a dict
    msg = ast.literal_eval(body.decode("UTF-8"))
    print(
        time.ctime(time.time())
        + " : to-> "
        + msg["to"]
        + "  sbj-> "
        + msg["subject"]
        + "  bdy-> "
        + msg["body"]
    )
    log(
        "Received : to-> "
        + msg["to"]
        + "  sbj-> "
        + msg["subject"]
        + "  bdy-> "
        + msg["body"]
    )
    if send_email(msg["to"], msg["body"], msg["subject"]):
        # Acknowledge the message
        ch.basic_ack(method.delivery_tag)
        log("Email Message acknowledged")
    else:
        ch.basic_nack(method.delivery_tag, requeue=True)
        print("Unable to send email")
        log("Unable to send email")


try:
    credentials = pika.PlainCredentials(
        os.environ["RBT_MQ_USER"], os.environ["RBT_MQ_PASS"]
    )
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(os.environ["RBT_MQ"], credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=sms_queue, durable=True)
    channel.queue_declare(queue=email_queue, durable=True)
    channel.basic_consume(
        queue=sms_queue, auto_ack=False, on_message_callback=on_sms_receive
    )
    channel.basic_consume(
        queue=email_queue, auto_ack=False, on_message_callback=on_email_receive
    )

    print(" [*] Waiting for messages")
    channel.start_consuming()

except Exception as e:
    print(e)

except KeyboardInterrupt:
    try:
        sys.exit()
    except:
        os._exit()
