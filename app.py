import os, sys
import pika
import time
from dotenv import load_dotenv

load_dotenv()

def on_recieve (ch, method, props, body):
    print(time.ctime(time.time())+" : "+ f'{body}')

try:

    credentials = pika.PlainCredentials(os.environ['RBT_MQ_USER'], os.environ['RBT_MQ_PASS'])
    connection  = pika.BlockingConnection(pika.ConnectionParameters(os.environ['RBT_MQ'], credentials = credentials))
    channel  = connection.channel()
    channel.queue_declare(queue = 'test', durable = True)

    channel.basic_consume(queue = 'test', auto_ack = True, on_message_callback = on_recieve)

    print(' [*] Waiting for messages')
    channel.start_consuming()

except Exception as e:
    print (e)

except KeyboardInterrupt:
    try:
        sys.exit()
    except:
        os._exit()
