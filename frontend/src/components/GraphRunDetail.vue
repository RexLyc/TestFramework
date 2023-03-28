<script setup lang="ts">

import * as tn from '@/TestNode';
import { ElNotification } from 'element-plus'
import { onMounted, ref, watch, getCurrentInstance, nextTick } from 'vue';
import { ElTable } from 'element-plus';
import { HttpUtil } from '@/Webutils';

enum GraphRunStateEnum {
  UNKNOWN       = '未知',
  WAITING       = '等待',
  PREPARING     = '准备',
  RUNNING       = '运行中',
  SUCCESS       = '测试成功',
  FAILED        = '测试失败',
  EXCEPTION     = '测试异常'
}

enum ServerLinkStateEnum {
  UNKNOWN       = '未知',
  WAITING       = '空闲',
  BUSY          = '繁忙',
  OFFLINE       = '离线',
  INCOMPATIBLE  = '不兼容',
  EXCEPTION     = '连接异常'
}

class RunResult{
  isSuccess:boolean
  isException:boolean
  timeElapsed:number
  log:string
  constructor(isSuccess:boolean,isException:boolean,timeElasped:number,log:string){
    this.isSuccess=isSuccess;
    this.isException=isException;
    this.timeElapsed=timeElasped;
    this.log=log;
  }
}

enum CommonResponseEnum {
  SUCCESS       = 0,
  INCOMPATIBLE  = 1,
  BUSY          = 2,
  EXCEPTION     = 3,
}

class CommonResponse {
  msg:string
  code:number;
  constructor(msg:string,code:number){
    this.msg=msg;
    this.code=code;
  }
}


const {ctx:that} = getCurrentInstance() as any;

class ServerInfo{
  name        :string;
  address     :string;
  link        :ServerLinkStateEnum;
  runState    :GraphRunStateEnum;
  log         :string;
  constructor(name:string,address:string,link:ServerLinkStateEnum,runState:GraphRunStateEnum,log:string){
    this.name=name;
    this.address=address;
    this.link=link;
    this.runState=runState;
    this.log=log;
  }

  updateLink(graphName:string){
    
    HttpUtil.linkTest(this.address
      ,tn.TestGraphFactory.exportGraph(graphName)
      ,(resp:any)=>{
        if(resp.status===200){
          // success run over
          const commonResp = new CommonResponse(resp.data.msg,resp.data.code);
          if(commonResp.code===CommonResponseEnum.BUSY)
            this.link=ServerLinkStateEnum.BUSY;
          else if(commonResp.code===CommonResponseEnum.SUCCESS)
            this.link=ServerLinkStateEnum.WAITING;
          else if(commonResp.code===CommonResponseEnum.INCOMPATIBLE)
            this.link=ServerLinkStateEnum.INCOMPATIBLE;
          else if(commonResp.code===CommonResponseEnum.EXCEPTION)
            this.link=ServerLinkStateEnum.EXCEPTION;
        } else {
          this.link = ServerLinkStateEnum.EXCEPTION;
        }
      }
      ,(error:any)=>{
        console.log(error);
        if(error.response==null || error.response.status===404)
          this.link = ServerLinkStateEnum.OFFLINE;
        else
          this.link = ServerLinkStateEnum.EXCEPTION;
      });
  }

  updateRunState(graphName:string){
    HttpUtil.runTestGraph(this.address
      ,tn.TestGraphFactory.exportGraph(graphName)
      ,(resp:any) => {
        if(resp.status===200){
          // success run over
          const runResult = new RunResult(resp.data.isSuccess,resp.data.isException,resp.data.timeElapsed,resp.data.log);
          this.runState = runResult.isSuccess?GraphRunStateEnum.SUCCESS:GraphRunStateEnum.FAILED;
          this.runState = runResult.isException?GraphRunStateEnum.EXCEPTION:this.runState;
          this.log = runResult.log;
        } else {
          this.log = resp.statusText;
          this.runState = GraphRunStateEnum.EXCEPTION;
        }
      }
      ,(error:any) => {
        this.log = error;
        this.runState = GraphRunStateEnum.EXCEPTION;
      });
  }

  updateLog(graphName:string){
    // 获取完整日志
  }
}

const serverUrl = ref("")
const serverUrlList = ref([
  {
    value:'http://127.0.0.1:5000',
    label:'本地'
  }
])

const props = defineProps({
  graphName:String,
});

onMounted(()=>{
  
})

watch(props,()=>{
  
})

function isURL(str_url:string) {// 验证url
  try {
    const newUrl = new URL(str_url);
    console.log(newUrl);
    return newUrl.protocol === 'http:' || newUrl.protocol === 'https:';
  } catch (err) {
    return false;
  }
}

const serverTable = ref<ServerInfo[]>([]);

const addTestServer = ()=>{
  console.log('addTestServer: %o,%o',serverUrl.value,selectFilterValue.value)
  let tempUrl:any = serverUrl.value;
  if(typeof(serverUrl.value)=='string'){
    tempUrl = {value:serverUrl.value,label:'自定义'};
  }
  if(isURL(tempUrl.value)==false){
    ElNotification.error({
      title: '注意',
      message: '无效的URL',
      showClose: false,
      duration: 1000
    })
    return;
  }
  else if(serverTable.value.findIndex((value,index)=>{return value.address===tempUrl.value})!=-1){
    ElNotification.warning({
      title: '注意',
      message: '已有该地址测试服务器',
      showClose: false,
      duration: 1000
    })
    return;
  }  
  // 必须使用ref，否则未代理对象，无法正确触发重新渲染（v-if动态决定tag的颜色）
  const server = ref(new ServerInfo(tempUrl.label,tempUrl.value,ServerLinkStateEnum.UNKNOWN,GraphRunStateEnum.UNKNOWN,""))
  serverTable.value.push(server.value);
  server.value.updateLink(props.graphName!);
  serverUrl.value='';
}

const runAllTest = ()=>{
  for(let server of multipleSelection.value){
    server.updateRunState(props.graphName!);
  }
}

const selectFilterValue = ref('')
const selectFilter = (val:any)=>{
  console.log('filter: %o',val);
  selectFilterValue.value=val;
  if(selectFilterValue.value!='')
    serverUrl.value='';
}

const selectBlur=(event:any)=>{
  // 失焦时不清空
  console.log('blur: %o',serverUrl.value,selectFilterValue.value);
  if(serverUrl.value===''&&selectFilterValue.value!==''){
    serverUrl.value=selectFilterValue.value;
  }
}

const handleDelete = ()=>{
  for(let select of multipleSelection.value) {
    serverTable.value.splice(serverTable.value.findIndex((value,index)=>{return value===select}),1);
  }
}


const multipleTableRef = ref<InstanceType<typeof ElTable>>()
const multipleSelection = ref<ServerInfo[]>([])
const handleSelectionChange = (val: ServerInfo[]) => {
  multipleSelection.value = val
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
        </el-space>
        <el-button @click="handleDelete" type="danger" style="position:absolute;right: 0px;"><el-icon><Delete/></el-icon></el-button>
        <el-table ref="multipleTableRef" :data="serverTable" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="55" />
          <el-table-column prop="name" label="名称">
          </el-table-column>

          <el-table-column prop="address" label="地址">
          </el-table-column>

          <el-table-column label="连接状态">
            <template #default="scope">
              <el-tag v-if="scope.row.link==ServerLinkStateEnum.WAITING" effect="dark" size="large" type="success">{{ scope.row.link }}</el-tag>
              <el-tag v-if="scope.row.link==ServerLinkStateEnum.INCOMPATIBLE
                              ||scope.row.link==ServerLinkStateEnum.UNKNOWN" effect="dark" size="large" type="info">{{ scope.row.link }}</el-tag>
              <el-tag v-if="scope.row.link==ServerLinkStateEnum.BUSY" effect="dark" size="large" type="warning">{{ scope.row.link }}</el-tag>
              <el-tag v-if="scope.row.link==ServerLinkStateEnum.OFFLINE
                              ||scope.row.link==ServerLinkStateEnum.EXCEPTION" effect="dark" size="large" type="danger">{{ scope.row.link }}</el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="运行状态">
            <template #default="scope">
              <el-tag v-if="scope.row.runState==GraphRunStateEnum.WAITING
                              ||scope.row.runState==GraphRunStateEnum.PREPARING" effect="dark" size="large">{{ scope.row.runState }}</el-tag>
              <el-tag v-if="scope.row.runState==GraphRunStateEnum.SUCCESS" effect="dark" size="large" type="success">{{ scope.row.runState }}</el-tag>
              <el-tag v-if="scope.row.runState==GraphRunStateEnum.UNKNOWN" effect="dark" size="large" type="info">{{ scope.row.runState }}</el-tag>
              <el-tag v-if="scope.row.runState==GraphRunStateEnum.FAILED
                              ||scope.row.runState==GraphRunStateEnum.EXCEPTION" effect="dark" size="large" type="danger">{{ scope.row.runState }}</el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="log" label="运行日志">
          </el-table-column>
        </el-table>
    </el-scrollbar>
  </div>
</template>

<style scoped>

</style>