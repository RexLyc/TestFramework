<script setup lang="ts">

import { ref } from 'vue'

const sendExportEvent=(event)=>{
  const e = new CustomEvent('exportTestGraph');
  dispatchEvent(e);
}

const sendImportEvent=(event)=>{
  const e = new CustomEvent('importTestGraph');
  dispatchEvent(e);
}


const dialogTableVisible = ref(false)

</script>

<template>
  <el-row class="row-bg" justify="space-between">
    <el-col :span="6">
      <img style="max-height: 60px;" src="TestFramework.jpg" object-fit="scale-down"/>
    </el-col>
    <el-col :span="6">

    </el-col>
    <el-col :span="6">
      <el-icon @click="dialogTableVisible = true" ><Tools /></el-icon>
      <el-icon @click="sendExportEvent" title="导出测试图"><Download /></el-icon>
      <el-icon @click="sendImportEvent" title="加载测试图"><FolderOpened /></el-icon>
    </el-col>
  </el-row>

  <el-dialog v-model="dialogTableVisible" title="设置">
    <div>这里还什么都没做呐</div>
  </el-dialog>
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