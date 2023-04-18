from flask import Flask, request, Response
from service.TestService import TestService
import json
from flask_cors import *
from graph.Component import RunResult
from service.TestService import MessageType
# from service.WebSocketService import WebSocketService
from flask_socketio import SocketIO, emit,join_room,leave_room
from service.MessageService import MessageService,MessageType
import time

app = Flask('test-framework-backend')
# 为http添加cors支持
# CORS(app,supports_credentials=True,resources=r'/*')

# 为socket io 添加cors支持
# 为跨线程socketio添加async_mode支持
socketio = SocketIO(app,cors_allowed_origins='*',async_mode='threading')

# def buildBaseResp():
#     resp = Response(status=200)
#     resp.headers['Access-Control-Allow-Origin']='*'
#     resp.headers['Access-Control-Allow-Methods']='OPTIONS,HEAD,GET,POST'
#     resp.headers['Access-Control-Allow-Headers']='x-requested-with'
#     return resp

# @app.route('/hello',methods=['post'])
# def hello():
#     print(request.data)
#     return 'greetings from backed.'

# @app.route('/runTestGraph',methods=['post'])
# def runTestGraph():
#     print(runTestGraph.__name__+' begin')
#     resp = buildBaseResp()
#     # 必须添加异常处理，否则会无法返回CORS
#     try:
#         resp.data = json.dumps(TestService.run(request.get_data()))
#     except Exception as err:
#         resp.data = json.dumps(CommonResponse(CommonResponseEnum.EXCEPTION.value,RunResult(0,'{}'.format(err))))
#     return resp

# @app.route('/linkTest',methods=['post'])
# def runLinkTest():
#     resp = buildBaseResp()
#     # 必须添加异常处理，否则会无法返回CORS
#     try:
#         resp.data = json.dumps(TestService.linkTest(request.get_data()))
#     except Exception as err:
#         resp.data = json.dumps(CommonResponse(CommonResponseEnum.EXCEPTION.value))
#     print(resp.data)
#     return resp

ws_namespace = '/websocket'


# ==================================== 基础消息 ====================================
# 连接处理
@socketio.on(message='connect',namespace=ws_namespace)
def on_connect(message):
    print("client connected. {}".format(request.sid))
    # socketio.emit('connect', {'data': 'connect'},namespace=ws_namespace)

# 连接断开处理
@socketio.on('disconnect', namespace=ws_namespace)
def on_disconnect():
    print('client disconnected.')

# 连接错误处理
@socketio.on('error', namespace=ws_namespace)
def on_error():
    print('client connect error.')

# ==================================== 自定义消息 ====================================
# 心跳
@socketio.on(MessageType.PING.value, namespace=ws_namespace)
def on_ping(message):
    print('client ping')
    print(socketio)
    emit(MessageType.PING.value, {}, namespace = ws_namespace)

# 提交测试图
@socketio.on(MessageType.SUBMIT.value,namespace=ws_namespace)
def on_submit(message):
    print('get test graph submit {}'.format(message))
    result = TestService.submit(message['msgData'],request.sid)
    emit(MessageType.SUBMIT.value,result,to=request.sid)

@socketio.on(MessageType.TEST_RESULT.value,namespace=ws_namespace)
def on_test_result(message):
    print('query test result {}'.format(message['msgData']))
    result = TestService.getTestResult(message,request.sid)
    emit(MessageType.TEST_RESULT.value,result,to=request.sid)

@socketio.on(MessageType.TEST_STATE.value,namespace=ws_namespace)
def on_test_state(message):
    print('query test state {}'.format(message))
    result = TestService.getTestState(message['msgData'],request.sid)
    emit(MessageType.TEST_STATE.value,result,to=request.sid)

@socketio.on(MessageType.TEST_COMMAND.value,namespace=ws_namespace)
def on_test_command(message):
    print('command test {}'.format(message))
    result = TestService.setTestCommand(message['msgData'],request.sid)
    emit(MessageType.TEST_COMMAND.value,result,to=request.sid)

if __name__ == '__main__':
    # app.run(debug=True)
    MessageService.initSocket(socketio,ws_namespace)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)