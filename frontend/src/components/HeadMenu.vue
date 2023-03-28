<script setup lang="ts">

import { onMounted, ref } from 'vue'

const inputElement = ref();

onMounted(()=>{
  inputElement.value = document.createElement('input');
  inputElement.value.type='file';
  inputElement.value.onchange=sendImportEvent;
  inputElement.value.accept=".json";
})

const sendExportEvent=(event)=>{
  const e = new CustomEvent('exportTestGraph');
  dispatchEvent(e);
}

const showUpload=(event)=>{
  inputElement.value.click();
}

const sendImportEvent=(event)=>{
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

const showRunTestGraph = (event)=>{
  const e = new CustomEvent('runTestGraph')
  dispatchEvent(e);
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
        <el-col :span="2"><el-icon @click="showRunTestGraph" title="运行测试图"><VideoPlay /></el-icon></el-col>  
        <el-col :span="2"><el-icon @click="showUpload" title="加载测试图"><FolderOpened /></el-icon></el-col>  
        <el-col :span="2"><el-icon @click="sendExportEvent" title="导出测试图"><Download /></el-icon></el-col>  
        <el-col :span="2"><el-icon @click="dialogTableVisible = true" ><Tools /></el-icon></el-col>  
      </el-row>
      
      
    </el-col>
    <el-dialog v-model="dialogTableVisible" title="设置">
      <div>这里还什么都没做呐</div>
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