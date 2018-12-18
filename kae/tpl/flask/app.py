from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'


# this api is needed to do healthcheck, so don't remove it
@app.route('/healthz')
def hello_world():
    return 'ok'
