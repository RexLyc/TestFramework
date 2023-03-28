from flask import Flask, request, Response
from service import TestService
import json

app = Flask('test-framework-backend')

@app.route('/hello',methods=['post'])
def hello():
    print(request.data)
    return 'greetings from backed.'

@app.route('/runTestGraph',methods=['post'])
def runTestGraph():
    print(request.data)
    resp = Response(status=200)
    resp.data = json.dumps(TestService.TestService.run(request.data))
    return resp

if __name__ == '__main__':
    app.run(debug=True)