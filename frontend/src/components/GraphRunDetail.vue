<script setup lang="ts">

import * as tn from '@/TestNode';
import { ElNotification, uploadBaseProps } from 'element-plus'
import { onMounted, ref, watch, getCurrentInstance, nextTick, onBeforeUnmount } from 'vue';
import { ElTable } from 'element-plus';
import { HttpUtil, SocketIOUtil, CommonMessageType, CommonMessage,SubmitResultType,ExitStateEnum,TestCommandType,TestCommand} from '@/Webutils';
import { toNumber } from 'lodash';

enum GraphRunStateEnum {
  UNKNOWN       = '未知',
  WAITING       = '等待',
  PREPARING     = '准备中',
  RUNNING       = '运行中',
  SUCCESS       = '测试成功',
  FAILED        = '测试失败',
  EXCEPTION     = '测试异常',
  INCOMPATIBLE  = '不兼容',
  KILLED        = '强制结束',
  TIMEOUT       = '超时',
  INVALID       = '无效',
  ASSERTERROR   = '断言失败',
}

enum ServerLinkStateEnum {
  UNKNOWN       = '未知',
  WAITING       = '空闲',
  BUSY          = '繁忙',
  OFFLINE       = '离线',
  EXCEPTION     = '连接异常'
}

class RunResult{
  timeElapsed:number
  log:string
  constructor(timeElasped:number,log:string){
    this.timeElapsed=timeElasped;
    this.log=log;
  }
}

enum CommonResponseEnum {
  SUCCESS       = 0,
  INCOMPATIBLE  = 1,
  BUSY          = 2,
  EXCEPTION     = 3,
  FAILED        = 4,
}

class CommonResponse<T = any> {
  code:number;
  data:T;
  constructor(code:number,data:T){
    this.code=code;
    this.data=data;
  }
}


const {ctx:that} = getCurrentInstance() as any;



class ServerInfo{
  name        :string;
  address     :string;
  link        :ServerLinkStateEnum;
  runState    :GraphRunStateEnum;
  log         :string;
  isReleased  :boolean;
  testUUID    :string;
  constructor(name:string,address:string,link:ServerLinkStateEnum,runState:GraphRunStateEnum,log:string){
    this.name=name;
    this.address=address;
    this.link=link;
    this.runState=runState;
    this.log=log;
    this.isReleased=false;
    this.testUUID="";
  }

  socketConnect() {
    SocketIOUtil.open(this.address
        // onOpen
      , (message:any)=>{
        console.log("onOpen",message)
        console.log("%o",this)
        SocketIOUtil.send(this.address,new CommonMessage(CommonMessageType.PING,{}))
      }
        // onClose
      , (message:any)=>{
        console.log("onClose",message)
        this.socketDisconnect();
        this.link=ServerLinkStateEnum.OFFLINE;
      }
        // onError
      , (message:any)=>{
        console.log("onError",message)
        this.link=ServerLinkStateEnum.OFFLINE;
        this.socketDisconnect()
      }
      , new Map([
        // 心跳反馈
        [CommonMessageType.PING.toString(),(message:any)=>{
          console.log("ping message: %o",message)
          this.link=ServerLinkStateEnum.WAITING;
        }],
        [CommonMessageType.SUBMIT.toString(),(message:any)=>{
          console.log("submit message: %o",message)
          if(this.testUUID==message.msgData.testUUID){
            console.log("get result faster than submit ack");
            return;
          }
          switch(message.msgData.result){
            case SubmitResultType.SUCCESS:{
              this.runState=GraphRunStateEnum.RUNNING;
              break;
            }
            case SubmitResultType.INCOMPATIBLE:{
              this.runState=GraphRunStateEnum.INCOMPATIBLE;
              break;
            }
            case SubmitResultType.EXCEPTION:{
              this.runState=GraphRunStateEnum.EXCEPTION;
              break;
            }
            default:{
              this.runState=GraphRunStateEnum.UNKNOWN;
              break;
            }
          }
          this.log = message.msgData.message
          this.testUUID=message.msgData.testUUID;
        }],
        [CommonMessageType.TEST_RESULT.toString(),(message:CommonMessage)=>{
          console.log('test result message: %o',message)
          if(!message.msgData){
            this.runState = GraphRunStateEnum.INVALID;
          }
          switch(message.msgData.exitState){
            case ExitStateEnum.EXCEPTION:{
              this.runState = GraphRunStateEnum.EXCEPTION;
              break;
            }
            case ExitStateEnum.INVALID:{
              this.runState = GraphRunStateEnum.INVALID;
              break;
            }
            case ExitStateEnum.SUCCESS:{
              this.runState = GraphRunStateEnum.SUCCESS;
              break;
            }
            case ExitStateEnum.TIMEOUT:{
              this.runState = GraphRunStateEnum.TIMEOUT;
              break;
            }
            case ExitStateEnum.KILLED:{
              this.runState = GraphRunStateEnum.KILLED;
              break;
            }
            case ExitStateEnum.TESTERROR:{
              this.runState = GraphRunStateEnum.FAILED;
              break;
            }
            case ExitStateEnum.ASSERTERROR:{
              this.runState = GraphRunStateEnum.ASSERTERROR;
              break;
            }
            default:{
              this.runState = GraphRunStateEnum.INVALID;
              break;
            }
          }
          this.log=message.msgData.log
        }],
        [CommonMessageType.TEST_COMMAND.toString(),(message:CommonMessage)=>{
          console.log('test command message: %o',message)
          if(message.msgData.result==true){
            ElNotification.success({
              title: '注意',
              message: '控制成功',
              showClose: true,
              duration: 5000
            })
          } else {
            ElNotification.error({
              title: '注意',
              message: '控制失败: '+message.msgData.message,
              showClose: true,
              duration: 5000
            })
          }
        }],
        [CommonMessageType.TEST_REPORT.toString(),(message:CommonMessage)=>{
          console.log('test report message: %o',message);
          const e = new CustomEvent('showTestReport',{detail:{'topology':message.msgData.topology,'timeline':message.msgData.timeline}})
          dispatchEvent(e);
        }],
      ])
    )
  }

  socketDisconnect() {
    SocketIOUtil.close(this.address);
    if(!this.isReleased){
      this.updateLink();
    }
  }

  updateLink(){
    this.link = ServerLinkStateEnum.OFFLINE;
    this.socketConnect();
  }

  updateRunState(graphName:string){
    // TODO: 保存旧测试计划
    this.testUUID="";
    SocketIOUtil.send(this.address,new CommonMessage(CommonMessageType.SUBMIT,tn.TestGraphFactory.exportGraph(graphName)))
    this.runState = GraphRunStateEnum.PREPARING;
    this.log = '';    
  }

  updateLog(graphName:string){
    // TODO: 获取完整日志
  }

  release(){
    this.isReleased=true;
    this.socketDisconnect();
  }

  sendCommand(commandType: TestCommandType){
    SocketIOUtil.send(this.address,new CommonMessage(CommonMessageType.TEST_COMMAND,new TestCommand(this.testUUID,commandType)))
  }
}

const serverUrl = ref("")
const serverUrlList = ref([
  {
    value:'127.0.0.1:5000',
    label:'本地'
  }
])

const props = defineProps({
  graphName:String,
});

onMounted(()=>{
  
})

onBeforeUnmount(()=>{
  
})

watch(props,()=>{
  
})

// URL必须是一个ip:port的形式
function isURL(str_url:string) {
  if(str_url.match(/^\d+\.\d+\.\d+\.\d+\:\d+$/)===null){
    return false;
  }
  // 进一步检测各段数字是否合法
  var parts = str_url.split(/[\.\:]/)
  for(var i=0;i!=4;++i){
    if(0>toNumber(parts[i]) || toNumber(parts[i]) >=255){
      return false
    }
  }
  if(toNumber(parts[4])>65535||toNumber(parts[4])<0){
    return false;
  }
  return true;
  // try {
  //   str_url.trim()
  //   const newUrl = new URL(str_url);
  //   console.log(newUrl);
  //   return newUrl.protocol === 'http:' || newUrl.protocol === 'https:';
  // } catch (err) {
  //   return false;
  // }
}

const serverTable = ref<ServerInfo[]>([]);

const addTestServer = ()=>{
  console.log('addTestServer: %o,%o',serverUrl.value,selectFilterValue.value)
  let tempUrl:any = serverUrl.value;
  if(typeof(serverUrl.value)=='string'){
    tempUrl = {value:serverUrl.value,label:'自定义'};
  }
  tempUrl.value= tempUrl.value.replace(/\s/g,'');
  if(isURL(tempUrl.value)==false){
    ElNotification.error({
      title: '注意',
      message: '请输入 IP地址:端口',
      showClose: true,
      duration: 5000
    })
    return;
  }
  else if(serverTable.value.findIndex((value,index)=>{return value.address===tempUrl.value})!=-1){
    ElNotification.warning({
      title: '注意',
      message: '已有该地址测试服务器',
      showClose: true,
      duration: 5000
    })
    return;
  }  
  // 必须使用ref，否则未代理对象，无法正确触发重新渲染（v-if动态决定tag的颜色）
  const server = ref(new ServerInfo(tempUrl.label,tempUrl.value,ServerLinkStateEnum.UNKNOWN,GraphRunStateEnum.UNKNOWN,""))
  serverTable.value.push(server.value);
  server.value.updateLink();
  serverUrl.value='';
}

const runAllTest = ()=>{
  if(multipleSelection.value.length==0){
    ElNotification.error({
      title: '注意',
      message: '请选择要运行测试的服务器',
      showClose: true,
      duration: 5000
    })
  }
  for(let server of multipleSelection.value){
    server.updateRunState(props.graphName!);
  }
}

const stopAllTest = ()=>{
  if(multipleSelection.value.length==0){
    ElNotification.error({
      title: '注意',
      message: '请选择要停止测试的服务器',
      showClose: true,
      duration: 5000
    })
  }
  for(let server of multipleSelection.value){
    server.sendCommand(TestCommandType.KILL);
  }
}

const selectFilterValue = ref('')
const selectFilter = (val:any)=>{
  // console.log('filter: %o',val);
  selectFilterValue.value=val;
  if(selectFilterValue.value!='')
    serverUrl.value='';
}

const selectBlur=(event:any)=>{
  // 失焦时不清空
  // console.log('blur: %o',serverUrl.value,selectFilterValue.value);
  if(serverUrl.value===''&&selectFilterValue.value!==''){
    serverUrl.value=selectFilterValue.value;
  }
}

const handleDelete = ()=>{
  for(let select of multipleSelection.value) {
    select.release();
    serverTable.value.splice(serverTable.value.findIndex((value,index)=>{return value===select}),1);
  }
}

const multipleTableRef = ref<InstanceType<typeof ElTable>>()
const multipleSelection = ref<ServerInfo[]>([])
const handleSelectionChange = (val: ServerInfo[]) => {
  multipleSelection.value = val
}
const handleRowClick = (row:any,column:any,event:any)=>{
  if(column==null)
    return;
  // console.log(column,event.srcElement);
  if(multipleSelection.value.includes(row)){
    multipleSelection.value.slice(multipleSelection.value.findIndex((value)=>{return value===row}),1);
    multipleTableRef.value?.toggleRowSelection(row,false);
  } else {
    multipleSelection.value.push(row);
    multipleTableRef.value?.toggleRowSelection(row,true);
  }
}
const logDownload=(row:any)=>{
  ElNotification.error({
      title: '注意',
      message: '尚未实装',
      showClose: true,
      duration: 5000
    })
}
</script>

<template>
  <div id="container">
    <el-scrollbar>
        
        <el-space size="large">
          
          <el-select
            v-model="serverUrl"
            filterable
            clearable
            :filter-method="selectFilter"
            :reserve-keyword="false"
            placeholder="选择或输入测试服务器"
            @blur="selectBlur"
          >
            <el-option
              v-for="item in serverUrlList"
              :key="item.value"
              :label="item.label +' '+ item.value"
              :value="item"
            />
            
          </el-select>
          <el-button @click="addTestServer" type="primary">添加</el-button>
          <el-button @click="runAllTest" type="success">执行测试</el-button>
          <el-button @click="stopAllTest" type="warning">停止测试</el-button>
          <el-button @click="logDownload" type="info">获取日志</el-button>
        </el-space>
        <el-button @click="handleDelete" type="danger" style="position:absolute;right: 0px;"><el-icon><Delete/></el-icon></el-button>
        <el-table ref="multipleTableRef" :data="serverTable" @selection-change="handleSelectionChange" @row-click="handleRowClick">
          <el-table-column type="selection" width="55" />
          <el-table-column prop="name" label="名称" min-width="20px">
          </el-table-column>

          <el-table-column prop="address" label="地址" min-width="50px">
          </el-table-column>

          <el-table-column label="连接状态" min-width="50px">
            <template #default="scope">
              <el-tag v-if="scope.row.link==ServerLinkStateEnum.WAITING" effect="dark" size="large" type="success">{{ scope.row.link }}</el-tag>
              <el-tag v-else-if="scope.row.link==ServerLinkStateEnum.UNKNOWN" effect="dark" size="large" type="info">{{ scope.row.link }}</el-tag>
              <el-tag v-else-if="scope.row.link==ServerLinkStateEnum.BUSY" effect="dark" size="large" type="warning">{{ scope.row.link }}</el-tag>
              <el-tag v-else-if="scope.row.link==ServerLinkStateEnum.OFFLINE
                              ||scope.row.link==ServerLinkStateEnum.EXCEPTION" effect="dark" size="large" type="danger">{{ scope.row.link }}</el-tag>
              <el-tag v-else effect="dark" size="large" type="info">{{ scope.row.runState }}</el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="运行状态" min-width="50px">
            <template #default="scope">
              <el-tag v-if="scope.row.runState==GraphRunStateEnum.RUNNING" effect="dark" size="large" type="warning">{{ scope.row.runState }}</el-tag>
              <el-tag v-else-if="scope.row.runState==GraphRunStateEnum.WAITING
                              ||scope.row.runState==GraphRunStateEnum.PREPARING" effect="dark" size="large">{{ scope.row.runState }}</el-tag>
              <el-tag v-else-if="scope.row.runState==GraphRunStateEnum.SUCCESS" effect="dark" size="large" type="success">{{ scope.row.runState }}</el-tag>
              <el-tag v-else-if="scope.row.runState==GraphRunStateEnum.UNKNOWN" effect="dark" size="large" type="info">{{ scope.row.runState }}</el-tag>
              <el-tag v-else-if="scope.row.runState==GraphRunStateEnum.FAILED
                              ||scope.row.runState==GraphRunStateEnum.ASSERTERROR
                              ||scope.row.runState==GraphRunStateEnum.INCOMPATIBLE
                              ||scope.row.runState==GraphRunStateEnum.TIMEOUT
                              ||scope.row.runState==GraphRunStateEnum.INVALID
                              ||scope.row.runState==GraphRunStateEnum.EXCEPTION" effect="dark" size="large" type="danger">{{ scope.row.runState }}</el-tag>
              <el-tag v-else effect="dark" size="large" type="info">{{ scope.row.runState }}</el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="log" label="运行日志" show-overflow-tooltip min-width="300px">
          </el-table-column>
        </el-table>
    </el-scrollbar>
  </div>
</template>

<style scoped>
:deep(.el-popper){
  word-break:normal; 
  max-width: 300px; 
  display:block; 
  white-space: pre-wrap;
  word-wrap : break-word ;
  overflow: hidden ;
}
</style>