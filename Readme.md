# 基于图的测试框架
## 前端
&emsp;&emsp;使用vue3、element-plus、typescript、以及Drawflow编写。支持json导入导出。
## 后端
&emsp;&emsp;使用python3，接收测试图json序列化数据，从BeginNode，按照流程分别运行各个测试节点，并最终到达EndNode，或告知失败。
## 更新计划
1. 前端：
    - [ ] 添加左键区域框选、中间移动整体的能力
    - [ ] 添加和后端的接口
1. 后端
    - [ ] 重写，跟进协议更新
1. 客户端
    - [ ] 使用electron打包
1. 完善文档和注释