<script setup lang="ts">

import { onMounted, ref } from 'vue'
import { HttpUtil } from '@/Webutils'
import { ElMessageBox, ElNotification } from 'element-plus';

const inputElement = ref();

onMounted(()=>{
  inputElement.value = document.createElement('input');
  inputElement.value.type='file';
  inputElement.value.onchange=sendImportEvent;
  inputElement.value.accept=".json";
})

const sendExportEvent=(event:any)=>{
  const e = new CustomEvent('exportTestGraph');
  dispatchEvent(e);
}

const showUpload=(event:any)=>{
  inputElement.value.click();
}

const sendImportEvent=(event:any)=>{
  console.log(inputElement.value.files[0]);
  const jsonFile = inputElement.value.files[0];
  var reader = new FileReader();
  reader.readAsText(jsonFile);
  reader.onload = function() {
      // console.log(this.result);
      const e = new CustomEvent('importTestGraph',{detail:this.result});
      dispatchEvent(e);
  }
}


const dialogTableVisible = ref(false)

const showRunTestGraph = (event:any)=>{
  const e = new CustomEvent('runTestGraph')
  dispatchEvent(e);
}

const browseServerVisible = ref(false)
const saveInfoData = ref()
const typeFilter = ref(new Set())
const categoryFilter = ref(new Set())
const nameFilter = ref(new Set())
const browseServerSave = (event:any)=>{
  console.log(import.meta.env)
  browseServerVisible.value=true;
  HttpUtil.getSave({}
    ,(message:any)=>{
      if(message.data.code!=0){
          ElNotification.error({
          title: '注意',
          message: '查询失败'+message.data,
          showClose: false,
          duration: 1000
        })
      } else {
        saveInfoData.value = message.data.data;
        typeFilter.value.clear()
        categoryFilter.value.clear()
        nameFilter.value.clear()
        for(let row of message.data.data){
          typeFilter.value.add({text:row.type,value:row.type})
          categoryFilter.value.add({text:row.category,value:row.category})
          nameFilter.value.add({text:row.save_name,value:row.save_name})
        }
      }
    }
    ,(message:any)=>{
      ElNotification.error({
        title: '注意',
        message: '查询失败'+message,
        showClose: false,
        duration: 1000
      })
    });
}

const filterHandler = (
  value: string,
  row: any,
  column: any
) => {
  const property = column['property']
  return row[property] === value
}

const shareSave = ref(false)

const shareSaveToServer = (event:any)=>{
  shareSave.value=true;
}

const handleImportServerSave = (event:any)=>{

}

</script>

<template>
  <el-row class="row-bg" justify="space-between">
    <el-col :span="6">
      <img style="max-height: 60px;" src="favicon.ico" object-fit="scale-down"/>
    </el-col>
    <el-col :span="6">
    </el-col>
    <el-col :span="6">
      <el-row justify="end">
        <el-col :span="2"><el-icon @click="browseServerSave" title="浏览服务器存档"><Goods /></el-icon></el-col>  
        <el-col :span="2"><el-icon @click="shareSaveToServer" title="发布共享存档"><Share /></el-icon></el-col>  
        <el-col :span="2"><el-icon @click="showRunTestGraph" title="运行测试图"><VideoPlay /></el-icon></el-col>  
        <el-col :span="2"><el-icon @click="showUpload" title="加载测试图"><FolderOpened /></el-icon></el-col>  
        <el-col :span="2"><el-icon @click="sendExportEvent" title="导出测试图"><Download /></el-icon></el-col>  
        <el-col :span="2"><el-icon @click="dialogTableVisible = true" ><User /></el-icon></el-col>  
      </el-row>
      
      
    </el-col>
    <el-dialog v-model="dialogTableVisible" title="设置" width="20%">
      <div>这里还什么都没做呐</div>
    </el-dialog>

    <el-dialog
      v-model="browseServerVisible"
      title="浏览服务器存档"
      width="50%"
      destroy-on-close
    >
      <el-table :data="saveInfoData" ref="saveInfoRef">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="type" label="发布类型" show-overflow-tooltip width="120" sortable :filters="typeFilter" :filter-method="filterHandler">
        </el-table-column>
        <el-table-column prop="category" label="业务分类" show-overflow-tooltip width="140" sortable :filters="categoryFilter" :filter-method="filterHandler">
        </el-table-column>
        <el-table-column prop="save_name" label="名称" show-overflow-tooltip min-width="140" sortable :filters="nameFilter" :filter-method="filterHandler">
        </el-table-column>
        <el-table-column prop="description" label="备注" show-overflow-tooltip min-width="80">
        </el-table-column>
        <el-table-column prop="save_time" label="发布时间" width="180" sortable>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="handleImportServerSave">导入</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="shareSave"
      title="发布共享存档"
      width="30%"
      destroy-on-close
      center
    >
      <span>show server saves</span>
    </el-dialog>
  </el-row>
</template>

<style scoped>
.el-row {
  height: 100%;
  padding:0;
}

.el-col {
  height: 100%;
  padding:0;
}

.grid-content {
  padding:0;
  height: 100%;
}

.el-icon {
  height: 100%;
  font-size: x-large;
  float: right;
  padding-right: 10px;
}

.el-button--text {
  margin-right: 15px;
}
.el-select {
  width: 300px;
}
.el-input {
  width: 300px;
}
.dialog-footer button:first-child {
  margin-right: 10px;
}


</style>