import flask
from flask import request
import os
from bot import ObjectDetectionBot
import boto3
from botocore.exceptions import ClientError
import json
from loguru import logger


app = flask.Flask(__name__)

TELEGRAM_APP_URL = os.environ['TELEGRAM_APP_URL']
REGION_NAME = os.environ['REGION_NAME']
DYNAMO_TABLE = os.environ['DYNAMO_TABLE']


# TODO load TELEGRAM_TOKEN value from Secret Manager shermanawsproject
def get_secret():
    secret_name = "shermanawsproject"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name = REGION_NAME
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secret = json.loads(get_secret_value_response['SecretString'])
    secret_value = secret['TELEGRAM_TOKEN']
    return secret_value


TELEGRAM_TOKEN = get_secret()


@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    bot.handle_message(req['message'])
    print("the jason is: " + str(req))
    return 'Ok'


@app.route(f'/results/', methods=['GET', 'POST'])
def results():
    prediction_id = request.args.get('prediction_id')
    chat_id = request.args.get('chat_id')
    # TODO use the prediction_id to retrieve results from DynamoDB and send to the end-user
    dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
    table = dynamodb.Table(DYNAMO_TABLE)
    try:
        logger.info(f'prediction_id is: {prediction_id} and the chat_id is: {chat_id}')
        res = table.get_item(
            Key = {
                'prediction_id': prediction_id,
                'chat_id': chat_id
            }, TableName= 'AmirAWSpro'
        )
        logger.info(f'prediction_id is: {prediction_id} and the chat_id is: {chat_id}')
        item = res['Item']
        if item:
            bot.send_text(chat_id, text=str(item))
            return 'WE HAVE THE RESULT AND WE SEND IT TO THE USER'
        else:
            bot.send_text(chat_id, text="test")

    except Exception as e:
        raise e
        logger.info(f'prediction_id is: {prediction_id} and the chat_id is: {chat_id}')
        return f'Error: {str(e)}'


@app.route(f'/loadTest/', methods=['POST'])
def load_test():
    req = request.get_json()
    bot.handle_message(req['message'])
    return 'Ok'


if __name__ == "__main__":
    bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL)

    app.run(host='0.0.0.0', port=8443)
