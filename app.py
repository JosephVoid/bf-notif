import os, sys, ast
import pika
import time
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

def log (output: str):
    with open('log.txt', 'a+', encoding = 'UTF-8') as f:
        f.writelines(time.ctime(time.time())+" : "+ f'{output}'+"\n")

def send_sms (to: str, msg: str) -> bool:
    payload = {"message": msg, "phoneNumbers":[to]}

    try:
        response = requests.post(os.environ['SMS_URL'], auth=HTTPBasicAuth(os.environ['SMS_USR'], os.environ['SMS_PSS']), data=payload)
        log(str(response.status_code)+'-:-'+response.text)
        if (response.status_code >= 200 or response.status_code < 210):
            log(payload)
            return True
        else:
            return False
    except Exception as e:
        print(e)
        log(e)
        return False

def send_email (to: str, body: str, subject: str):
    pass

def on_recieve (ch, method, props, body: bytes):
    # Capture received message to file
    log(body)

    # Parse the byte to a dict
    msg = ast.literal_eval(body.decode("UTF-8"))
    print(time.ctime(time.time())+" : to-> "+ msg['to'] +"   msg-> "+ msg['message'])
    log("Received : to-> "+ msg['to'] +"   msg-> "+ msg['message'])
    if (send_sms(msg['to'], msg['message'])):
        # Acknowledge the message
        ch.basic_ack(method.delivery_tag)
        log("Message acknowledged")
    else:
        print("Unable to send message")
        log("Unable to send message")


try:

    credentials = pika.PlainCredentials(os.environ['RBT_MQ_USER'], os.environ['RBT_MQ_PASS'])
    connection  = pika.BlockingConnection(pika.ConnectionParameters(os.environ['RBT_MQ'], credentials = credentials))
    channel  = connection.channel()
    channel.queue_declare(queue = 'test', durable = True)

    channel.basic_consume(queue = 'test', auto_ack = False, on_message_callback = on_recieve)

    print(' [*] Waiting for messages')
    channel.start_consuming()

except Exception as e:
    print (e)

except KeyboardInterrupt:
    try:
        sys.exit()
    except:
        os._exit()
