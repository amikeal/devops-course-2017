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

@app.route('/echo/<string:input_str>')
def echo(input_str):
    return jsonify(
        input=input_str,
        output=' '.join([input_str]*3)
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

@app.route('/keyval', methods=['POST', 'PUT'])
def kv_upsert():
    # Set up the values for the return JSON
    _JSON = {
        'key': None,
        'value': None,
        'command': 'CREATE' if request.method=='POST' else 'UPDATE',
        'result': False,
        'error': None
    }

    # First check for a valid JSON payload
    try:
        payload = request.get_json()
        _JSON['key'] = payload['key']
        _JSON['value'] = payload['value']
        _JSON['command'] += f" {payload['key']}/{payload['value']}"
    except:
        _JSON['error'] = "Missing or malformed JSON in client request."
        return jsonify(_JSON), 400

    # Now try to connect to Redis
    try:
        test_value = redis.get(_JSON['key'])
    except RedisError:
        _JSON['error'] = "Cannot connect to redis."
        return jsonify(_JSON), 400

    # POST == create only
    if request.method == 'POST' and not test_value == None:
        _JSON['error'] = "Cannot create new record: key already exists."
        return jsonify(_JSON), 409

    # PUT == update only
    else if request.method == 'PUT' and test_value == None:
        _JSON['error'] = "Cannot update record: key does not exist."
        return jsonify(_JSON), 404

    # OK, create or update the record with the user-supplied values
    else:
        if redis.set(_JSON['key'], _JSON['value']) == False:
            _JSON['error'] = "There was a problem creating the value in Redis."
            return jsonify(_JSON), 400
        else:
            _JSON['result'] = True
            return jsonify(_JSON), 200


@app.route('/keyval/<string:key>', methods=['GET', 'DELETE'])
def kv_retrieve(key):
    # Set up the values for the return JSON
    _JSON = {
        'key': key,
        'value': None,
        'command': "{} {}".format('RETRIEVE' if response.method=='GET' else 'DELETE', key)
        'result': False,
        'error': None
    }

    # Try to connect to Redis
    try:
        test_value = redis.get(key)
    except RedisError:
        _JSON['error'] = "Cannot connect to redis."
        return jsonify(_JSON), 400

    # Can't retrieve OR delete if the value doesn't exist
    if test_value == None:
        _JSON['error'] = "Key does not exist."
        return jsonify(_JSON), 404
    else:
        _JSON['value'] = test_value

    # GET == retrieve
    if response.method == 'GET':
        _JSON['result'] = True
        return jsonify(_JSON), 200

    # DELETE == delete (duh)
    else if response.method == 'DELETE':
        ret = redis.delete(key)
        if ret == 1:
            _JSON['result'] = True
            return jsonify(_JSON)
        else:
            _JSON['error'] = f"Unable to delete key (expected return value 1; client returned {ret})"
            return jsonify(_JSON), 400

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
    ), 200 if resp.status_code==200 else 400

#
# Run the server if called directly
#
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
