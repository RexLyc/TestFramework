<script setup lang="ts">

import * as tn from '@/TestNode';
import { ElNotification } from 'element-plus'
import { onMounted, ref, watch } from 'vue';
import { ElTable } from 'element-plus';
import { HttpUtil } from '@/Webutils';

enum GraphRunStateEnum {
  UNKNOWN       = '未知',
  WAITING       = '等待',
  PREPARING     = '准备',
  RUNNING       = '运行中',
  SUCCESS       = '测试成功',
  FAILED        = '测试失败'
}

enum ServerLinkStateEnum {
  UNKNOWN       = '未知',
  WAITING       = '空闲',
  BUSY          = '繁忙',
  OFFLINE       = '离线',
  INCOMPATIBLE  = '不兼容'
}

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

  }

  updateRunState(graphName:string){
    HttpUtil.runTestGraph(this.address
      ,tn.TestGraphFactory.exportGraph(graphName)
      ,(resp:string) => {this.log = resp;}
      ,(error:string) => {this.log = error;});
  }

  updateLog(graphName:string){

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
  serverTable.value.push(new ServerInfo(tempUrl.label,tempUrl.value,ServerLinkStateEnum.UNKNOWN,GraphRunStateEnum.UNKNOWN,""));
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

          <el-table-column prop="link" label="连接状态">
            
          </el-table-column>
          
          <el-table-column prop="runState" label="运行状态">
            
          </el-table-column>
          
          <el-table-column prop="log" label="运行日志">
            
          </el-table-column>
        </el-table>
    </el-scrollbar>
  </div>
</template>

<!-- <el-popover
                placement="top-start"
                title="Title"
                :width="200"
                trigger="hover"
                content="this is content, this is content, this is content"
              >
                <template #reference>
                  <el-text v-text="scope.name"></el-text>
                </template>
                <el-button
                  size="small"
                  type="danger"
                  @click="handleDelete(scope.$index, scope.row)"
                  ><el-icon><Delete/></el-icon>
                </el-button>
              </el-popover> -->

<style scoped>
/* #container {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
} */

</style>