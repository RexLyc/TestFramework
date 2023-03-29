from flask import Flask, request, Response
from service.TestService import TestService
import json
from flask_cors import *
from graph.Component import RunResult
from service.TestService import CommonResponse,CommonResponseEnum

app = Flask('test-framework-backend')
CORS(app,supports_credentials=True,resources=r'/*')

def buildBaseResp():
    resp = Response(status=200)
    resp.headers['Access-Control-Allow-Origin']='*'
    resp.headers['Access-Control-Allow-Methods']='OPTIONS,HEAD,GET,POST'
    resp.headers['Access-Control-Allow-Headers']='x-requested-with'
    return resp

@app.route('/hello',methods=['post'])
def hello():
    print(request.data)
    return 'greetings from backed.'

@app.route('/runTestGraph',methods=['post'])
def runTestGraph():
    print(runTestGraph.__name__+' begin')
    resp = buildBaseResp()
    # 必须添加异常处理，否则会无法返回CORS
    try:
        resp.data = json.dumps(TestService.run(request.get_data()))
    except Exception as err:
        resp.data = json.dumps(CommonResponse(CommonResponseEnum.EXCEPTION.value,RunResult(0,'{}'.format(err))))
    return resp

@app.route('/linkTest',methods=['post'])
def runLinkTest():
    resp = buildBaseResp()
    # 必须添加异常处理，否则会无法返回CORS
    try:
        resp.data = json.dumps(TestService.linkTest(request.get_data()))
    except Exception as err:
        resp.data = json.dumps(CommonResponse(CommonResponseEnum.EXCEPTION.value))
    print(resp.data)
    return resp

if __name__ == '__main__':
    app.run(debug=True)