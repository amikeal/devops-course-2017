from flask import Flask, render_template, request, jsonify
from redis import Redis, RedisError
from math import sqrt
import requests
import hashlib
import os

#
# Config vars for the Slack connectivity
#
SLACK_TEAM = "TCMG 476"
SLACK_DOMAIN = "tcmg476.slack.com"
#
# Check the ENV var set in Docker
#
if os.getenv('STAGE', 'dev') == 'dev':
    SLACK_CHANNEL = "@adam"
    SLACK_URL = "https://hooks.slack.com/services/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"
else:
    SLACK_CHANNEL = "#general"
    SLACK_URL = "https://hooks.slack.com/services/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"


#
# Helper functions
#
def fact(n):
    if n > 0:
        return n * fact(n-1)
    else:
        return 1

def fib(n):
    f_1, f_2 = 0, 1
    ret = [0]
    while f_2 <= n:
        ret.append(f_2)
        f_1, f_2 = f_2, f_1 + f_2
    return ret

def is_prime(n):
    if n < 2: return False
    for x in range(2, int(sqrt(n)) + 1):
        if n % x == 0:
            return False
    return True


#
# Application
#
app = Flask(__name__)
redis = Redis(host="redis", socket_connect_timeout=2, socket_timeout=2)

#
# API routes
#
@app.route('/')
def hello():
    return jsonify(
        output="Hello World!"
    )

@app.route('/md5/<string:input_str>')
def md5_response(input_str):
    return jsonify(
        input=input_str,
        output=hashlib.md5(input_str).hexdigest()
    )

@app.route('/factorial/<int:input_int>')
def factorial_resp(input_int):
    return jsonify(
        input=input_int,
        output=fact(input_int)
    )

@app.route('/fibonacci/<int:input_int>')
def fibonacchi_resp(input_int):
    return jsonify(
        input=input_int,
        output=fib(input_int)
    )

@app.route('/is-prime/<int:input_int>')
def prime_check(input_int):
    return jsonify(
        input=input_int,
        output=is_prime(input_int)
    )

@app.route('/kv-record/<string:key>', methods=['POST'])
def kv_create(key):
    input = key
    output = False
    err_msg = None
    try:
        # first ensure this key does NOT exist (POST == create only)
        value = redis.get(key)
        if not value == None: 
            err_msg = "Cannot create new record: key already exists."
        else:
            # ok, this is a new key. let's create it
            payload = request.get_json()
            create_red = redis.set(key, payload['value'])
            if create_red == False:
                err_msg = "ERROR: There was a problem creating the value in Redis."
            else:
                output = True
                input = payload
    except RedisError:
        err_msg = "Cannot connect to redis."

    return jsonify(
        input=input,
        output=output,
        error=err_msg
    )

@app.route('/kv-record/<string:key>', methods=['PUT'])
def kv_update(key):
    input = key
    output = False
    err_msg = None
    try:
        # first check to see if this key even exists (PUT == update only)
        value = redis.get(key)
        if value == None: 
            err_msg = "Cannot update: key does not exist."
        else:
            # ok, key exists. now update it
            payload = request.get_json()
            update_red = redis.set(key, payload['value'])
            if update_red == False:
                err_msg = "ERROR: There was a problem updating the value in Redis."
            else:
                output = True
                input = payload
    except RedisError:
        err_msg = "Cannot connect to redis."

    return jsonify(
        input=input,
        output=output,
        error=err_msg
    )

@app.route('/kv-retrieve/<string:key>')
def kv_retrieve(key):
    output = False
    err_msg = None
    try:
        value = redis.get(key)
        if value == None:
            err_msg = "Key does not exist."
        else:
            output = value
    except RedisError:
        err_msg = "Cannot connect to redis."

    return jsonify(
        input=key,
        output=output,
        error=err_msg
    )

@app.route('/slack-alert/<string:msg>')
def post_to_slack(msg):
    data = { 'text': msg }
    resp = requests.post(SLACK_URL, json=data)
    if resp.status_code == 200:
        result = True
        mesg = "Message successfully posted to Slack channel " + SLACK_CHANNEL
    else:
        result = False
        mesg = "There was a problem posting to the Slack channel (HTTP response: " + str(resp.status_code) + ")."
    
    return jsonify(
        input=msg, 
        message=mesg,
        output=result
    )

#
# Run the server if called directly
#
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)