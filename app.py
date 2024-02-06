import os, sys, ast
import pika
import time
from dotenv import load_dotenv

load_dotenv()

def on_recieve (ch, method, props, body: bytes):
    # Capture received message to file
    with open('log.txt', 'a+', encoding = 'UTF-8') as f:
        f.writelines(time.ctime(time.time())+" : "+ f'{body}'+"\n")
    
    # Parse the byte to a dict
    msg = ast.literal_eval(body.decode("UTF-8"))
    print(time.ctime(time.time())+" : to-> "+ msg['to'] +"   msg-> "+ msg['message'])

    # Acknowledge the message
    ch.basic_ack(method.delivery_tag)


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
