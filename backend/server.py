from flask import Flask, request, Response
from service.TestService import TestService
import json
from flask_cors import *
from graph.Component import RunResult
from service.TestService import CommonResponse,CommonResponseEnum
# from service.WebSocketService import WebSocketService
from flask_socketio import SocketIO, emit
import time

app = Flask('test-framework-backend')
# 为http添加cors支持
CORS(app,supports_credentials=True,resources=r'/*')
# 为socket io 添加cors支持
socketio = SocketIO(app,cors_allowed_origins='*')

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

ws_namespace = '/websocket'

@socketio.on(message='connect',namespace=ws_namespace)
def echo_socket(message):
    print("client connected.")
    socketio.emit('response', {'data': 'connect'},namespace=ws_namespace)


@socketio.on('disconnect', namespace=ws_namespace)
def disconnect_msg():
    print('client disconnected.')


@socketio.on('message', namespace=ws_namespace)
def mtest_message(message):
    print(message)
    # socketio.send(data='helloworld')
    emit('response', {"msg":123},namespace = ws_namespace)
    # emit("response")

if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)