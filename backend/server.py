# flask依赖
from flask import Flask, request, Response, g
from flask_cors import *
from flask_socketio import SocketIO, emit
# 其他依赖库
import json
import sqlite3
# 服务导入
from service.TestService import TestService
from service.SaveService import SaveService,SaveResponse,SaveResponseType
from service.MessageService import MessageService,MessageType

# ==================================== 工具函数 ====================================
def buildBaseResp():
    resp = Response(status=200)
    resp.headers['Access-Control-Allow-Origin']='*'
    resp.headers['Access-Control-Allow-Methods']='OPTIONS,HEAD,GET,POST'
    resp.headers['Access-Control-Allow-Headers']='x-requested-with'
    return resp


# ==================================== 框架实例创建 ====================================
app = Flask('test-framework-backend')
# 为http添加cors支持
# CORS(app,supports_credentials=True,resources=r'/*')

# 为socket io 添加cors支持
# 为跨线程socketio添加async_mode支持
socketio = SocketIO(app,cors_allowed_origins='*',async_mode='threading')

# ==================================== HTTP请求 ====================================

@app.route('/serverSave',methods=['post'])
def getServerSave():
    resp = buildBaseResp()
    # 必须添加异常处理，否则会无法返回CORS
    try:
        jsonData = request.get_data()
        print('get serverSave query: {}'.format(jsonData))
        query = json.loads(jsonData)
        print('get query {}'.format(query))
        if query is None or len(list(query))==0:
            # 返回整体信息列表
            resp.data = json.dumps(SaveService.getAllSaveInfo())
        else:
            # 返回指定名称的存档文件
            resp.data = json.dumps(SaveService.getSave(query))
    except Exception as err:
        resp.data = json.dumps(SaveResponse(SaveResponseType.EXCEPTION,'{}'.format(err)))
    print(resp)
    return resp

@app.route('/saveCategory',methods=['post'])
def getCategory():
    resp = buildBaseResp()
    try:
        resp.data = json.dumps(SaveResponse(SaveResponseType.SUCCESS,SaveService.getCategory()))
    except Exception as err:
        resp.data = json.dumps(SaveResponse(SaveResponseType.EXCEPTION,'{}'.format(err)))
    print(resp)
    return resp

@app.route('/uploadSave',methods=['post'])
def uploadSave():
    resp = buildBaseResp()
    try:
        jsonData = request.get_data()
        print('get serverSave query: {}'.format(jsonData))
        saveParam = json.loads(jsonData)
        print(saveParam)
        resp.data = json.dumps(SaveService.addSave(saveParam['form']['save_name']
                                                   ,saveParam['form']['typeValue']
                                                   ,saveParam['form']['categoryValue']
                                                   ,saveParam['form']['description']
                                                   ,saveParam['data']))
    except Exception as err:
        print(type(err))
        resp.data = json.dumps(SaveResponse(SaveResponseType.EXCEPTION,'{}'.format(err)))
    print(resp)
    return resp

@app.route('/deleteSave',methods=['post'])
def deleteSave():
    resp = buildBaseResp()
    try:
        jsonData = request.get_data()
        print('get serverSave query: {}'.format(jsonData))
        deleteNames = json.loads(jsonData)
        print(deleteNames)
        SaveService.deleteSave(deleteNames)
        resp.data = json.dumps(SaveResponse(SaveResponseType.SUCCESS))
    except Exception as err:
        resp.data = json.dumps(SaveResponse(SaveResponseType.EXCEPTION,'{}'.format(err)))
    print(resp)
    return resp

# ==================================== 基础消息 ====================================
ws_namespace = '/websocket'
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
    SaveService.init()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)