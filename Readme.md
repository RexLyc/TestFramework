# 基于图的测试框架
## 展示
![主界面](show_case.png)
## 前端
&emsp;&emsp;使用vue3、element-plus、typescript、以及Drawflow编写。支持json导入导出。
## 后端
&emsp;&emsp;使用python3，接收测试图json序列化数据，从BeginNode，按照流程分别运行各个测试节点，并最终到达EndNode，或告知失败。
## 更新计划
1. 优先：
    - [x] Assert节点
    - [x] 增加Python节点
    - [ ] 提供一个占位符节点（代表一个现有的输入/输出变量，避免过长的连接线）
    - [ ] 提供开关，仅显示数据流动，仅显示运行流程
    - [ ] 为不同连接赋予不通颜色
    - [x] 提供一个串口测试Demo
    - [ ] 提供一个HTTP接口测试Demo
    - [ ] 提供一个Websocekt测试Demo
1. 其他：
    1. 测试协议：
        - [ ] 增加UI检测节点、鼠标&键盘操作节点
        - [ ] 优化各个现有节点，提供默认参数，并在界面上说明
        - [x] 增加“模块”级别
            - 由一系列节点组成
            - 可以被不同测试图复用
            - 存在本地或服务器
        - [ ] 模块节点可以双击绘制其子图
        - [ ] 批量化、压力测试
    1. 前端：
        - [ ] 添加左键区域框选、中间移动整体的能力
        - [x] 添加和后端的接口
        - [ ] 文档，各空间均提供说明，帮助文字直接放在前端
        - [ ] 详细测试报告，及其可视化（D3.js）
        - [ ] 交互式的基本教学
        - [ ] 复制、粘贴、撤销、重做
    1. 后端
        - [x] 重写，跟进协议更新
        - [x] ~~提供登录、身份验证~~、存储模块、存储测试图的功能
        - [ ] 存储历史测试计划、测试报告
    1. 客户端
        - [ ] 使用electron打包
1. 持续：
    1. 完善文档和注释
## 构建
1. Ubuntu
```bash
# git clone
cd TestFramework
git submodule update --init --recursive

# frontend
cd frontend
npm install
npm run dev
npm run build-only

# backend
cd ../backend
pip3 install logging flask flask_cors flask_socketio websockets pyserial eventlet pyinstaller pyautogui easyocr numpy
python3 ./server.py
pyinstaller server.spec

# electron
npm install
npm run start
```
## 开发依赖
- python3 (>=3.7,<3.11)
- npm 9.2.0
- nodejs v18.12.1