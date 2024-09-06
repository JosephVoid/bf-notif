import os, sys, ast
import pika
from pika import exceptions
import time
import smtplib
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from email.message import EmailMessage
from email.utils import formataddr

load_dotenv()

sms_queue = os.environ["RBT_MQ_SMSQ"]
email_queue = os.environ["RBT_MQ_EMLQ"]
telegram_queue = os.environ["RBT_MQ_TGMQ"]

def log(output: str):
    with open("log.txt", "a+", encoding="UTF-8") as f:
        f.writelines(time.ctime(time.time()) + " : " + f"{output}" + "\n")


def send_sms(to: str, msg: str) -> bool:
    form_msg = u'{}\u000a - Buyers First'.format(msg)
    payload = {"message": form_msg, "phoneNumbers": [to]}
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
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = formataddr(('Buyers First', os.environ["EML_USR"]))
        message["To"] = to
        message.set_content(generate_email(subject, body), subtype='html')

        with smtplib.SMTP(os.environ["EML_SRV"], int(os.environ["EML_PRT"])) as smtp:
            smtp.starttls()
            smtp.login(os.environ["EML_USR"], os.environ["EML_PSS"])
            smtp.send_message(message)
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


def on_telegram_receive(ch, method, props, body: bytes):
    # Capture received message to file
    log(body)

    # Parse the byte to a dict
    msg = ast.literal_eval(body.decode("UTF-8"))
    print(
        time.ctime(time.time()) + " : title-> " + msg["title"] + "   desc-> " + msg["desc"] + "   photo-> " + msg["photo"]+ "   price-> " + msg["price"]+ "   url-> " + msg["url"]
    )
    log("Received : title-> " + msg["title"] + "   desc-> " + msg["desc"] + "   photo-> " + msg["photo"]+ "   price-> " + msg["price"]+ "   url-> " + msg["url"])
    if send_telegram(title=msg["title"], description=msg["desc"], photo=msg["photo"], avg_price=msg["price"], link=msg["url"]):
        # Acknowledge the message
        ch.basic_ack(method.delivery_tag)
        log("Message acknowledged")
    else:
        ch.basic_nack(method.delivery_tag, requeue=True)
        print("Unable to send telegram message")
        log("Unable to send telegram message")


def generate_email(heading, body_text):
    with open('index.html') as f: 
        html = f.read()
        final_str = html.replace('*Heading*', heading).replace('*Text*', body_text)
        return final_str


def send_telegram(title: str, description: str, photo: str, avg_price: float, link: str) -> bool:
    body = {}
    body['text'] = f'Someone wants: \n__*{title}*__ \n{description} \nPrice: *{str(avg_price)}* \nGo here: {link}'
    body['caption'] = f'Someone wants: \n__*{title}*__ \n{description}\nPrice: *{str(avg_price)}* \nGo here: {link}'
    body['chat_id'] = os.environ["CHNL_ADDR"]
    body['parse_mode'] = 'markdown'
    body['photo'] = photo

    try:
        if (photo == ''):
            response = requests.post(
                f'https://api.telegram.org/bot{os.environ['BOT_TOKEN']}/sendMessage',
                data=body,
            )
        else:
            response = requests.post(
                f'https://api.telegram.org/bot{os.environ['BOT_TOKEN']}/sendPhoto',
                data=body,
            )
        log(str(response.status_code) + "-:-" + response.text)
        if response.status_code >= 200 or response.status_code < 210:
            log(body)
            return True
        else:
            return False
    except Exception as e:
        print(e)
        log(e)
        return False

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
    channel.basic_consume(
        queue=telegram_queue, auto_ack=False, on_message_callback=on_telegram_receive
    )
    print(" [*] Waiting for messages")
    channel.start_consuming()

except RuntimeError as e:
    print(e)
except (
    exceptions.AMQPChannelError,
    exceptions.AMQPConnectionError,
    exceptions.ReentrancyError,
    exceptions.ChannelClosed,
) as e:
    print(e)
except KeyboardInterrupt:
    try:
        sys.exit()
    except:
        os._exit()
