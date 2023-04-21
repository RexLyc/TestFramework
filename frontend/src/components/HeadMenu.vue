<script setup lang="ts">

import { onMounted, reactive, ref } from 'vue'
import { HttpUtil } from '@/Webutils'
import { ElMessageBox, ElNotification } from 'element-plus';
import { ElTable } from 'element-plus';
import { toNestedArr } from 'element-plus/es/components/calendar/src/date-table';
import * as tn from '@/TestNode'
import { useGraphNameStore } from '@/stores/counter'

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
  // console.log(inputElement.value.files[0]);
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
const typeFilter = ref<any[]>([])
const categoryFilter = ref<any[]>([])
const browseServerSave = (event:any)=>{
  // console.log(import.meta.env)
  browseServerVisible.value=true;
  HttpUtil.getSave({}
    ,(message:any)=>{
      if(message.data.code!=0){
          ElNotification.error({
          title: '注意',
          message: '查询失败'+message.data,
          showClose: true,
          duration: 5000
        })
      } else {
        saveInfoData.value = message.data.data;
        const typeFilterSet = new Set();
        const categoryFilterSet = new Set();
        for(let row of message.data.data){
          typeFilterSet.add(row.type)
          categoryFilterSet.add(row.category)
        }
        typeFilter.value.splice(0)
        for(let item of typeFilterSet){
          typeFilter.value.push({text:item==0?'模块':'测试图',value:item})
        }
        categoryFilter.value.splice(0)
        for(let item of categoryFilterSet){
          categoryFilter.value.push({text:item,value:item})
        }
      }
    }
    ,(message:any)=>{
      ElNotification.error({
        title: '注意',
        message: '查询失败'+message,
        showClose: true,
        duration: 5000
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
const typeOptions = ref([
  {
    label:"模块",
    value:"0"
  },
  {
    label:"测试图",
    value:"1"
  }
])
const categoryOptions = ref<any[]>([])

// do not use same name with ref
const form = reactive({
  typeValue: '',
  categoryValue: '',
  save_name: '',
  description: '',
})
const shareSaveToServer = (event:any)=>{
  shareSave.value=true;
  HttpUtil.getSaveTypeCategory((message:any)=>{
    // console.log(message)
    categoryOptions.value.splice(0);
    for(let item of message.data.data.categoryName){
      categoryOptions.value.push({'value':item,'label':item});
    }
  }
  ,(message:any)=>{
    ElNotification.error({
      title: '注意',
      message: '查询失败'+message,
      showClose: true,
      duration: 5000
    })
  })
}

const queryCategory = (queryString: string, cb: any) => {
  const results = queryString
    ? categoryOptions.value.filter(createFilter(queryString))
    : categoryOptions.value
  // call callback function to return suggestions
  cb(results)
}
const createFilter = (queryString: string) => {
  return (restaurant: any) => {
    return (
      restaurant.value.indexOf(queryString.toLowerCase()) === 0
    )
  }
}

const handleImportServerSave = (event:any)=>{
  if(multipleSelection.value.length==0){
    ElNotification.warning({
      title: '注意',
      message: '请选择要导入的内容',
      showClose: true,
      duration: 5000
    })
  }
  // 可以同时导入多个模块，但不能导入多个测试图
  let moduleCount=0
  let graphCount=0
  const saveNames :string[] = [];
  for(let item of multipleSelection.value){
    if(item.type==0)
      moduleCount++;
    else
      graphCount++;
    saveNames.push(item.save_name)
  }

  const importCallback = ()=>{
    HttpUtil.getSave(saveNames
        ,(message:any)=>{
          if(message.data.code!=0){
            ElNotification.error({
              title: '注意',
              message: '导入失败'+message.data.data,
              showClose: true,
              duration: 5000
            })
          } else {
            const e = new CustomEvent('importShareSaves',{detail:message.data.data});
            dispatchEvent(e);

          }
        }
        ,(message:any)=>{
          ElNotification.error({
            title: '注意',
            message: '导入失败'+message.data.data,
            showClose: true,
            duration: 5000
          })
        });
  };

  if(graphCount>1){
    ElNotification.warning({
      title: '注意',
      message: '测试图类型最多只能导入一个',
      showClose: true,
      duration: 5000
    })
    return;
  }
  if(graphCount==1){
    ElMessageBox.confirm(
    '准备导入外部测试图，将会清空当前测试图，请确认',
    '请注意',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    .then(() => {
      importCallback();
    })
    .catch(() => {
      // 取消
    })
  } else {
    importCallback();
  }
  
}

const handleUploadShareSave = (event:any)=>{
  // 检查表单
  if(form.save_name.trim().length==0||form.typeValue.trim().length==0||form.categoryValue.trim().length==0){
    ElNotification.warning({
      title: '注意',
      message: '除备注外不可为空',
      showClose: true,
      duration: 5000
    })
    return;
  }
  let graph = '';
  if(form.typeValue=='0'){
    try{
      graph = tn.TestGraphFactory.exportModuleSave(useGraphNameStore().currentGraphName)
    } catch(error){
      ElNotification.warning({
        title: '注意',
        message: '导出模块失败'+error,
        showClose: true,
        duration: 5000
      })
      return;
    }
  } else {
    graph = tn.TestGraphFactory.exportGraph(useGraphNameStore().currentGraphName)
  }
  // 发送
  HttpUtil.uploadSave({
    data: graph,
    form: form
  }
  ,(message:any)=>{
    // resp
    if(message.data.code!=0){
      ElNotification.error({
        title: '注意',
        message: '发布失败'+message.data.data,
        showClose: true,
        duration: 5000
      })
    } else{
      ElNotification.success({
        title: '注意',
        message: '发布成功',
        showClose: true,
        duration: 5000
      })
      form.categoryValue='';
      form.description='';
      form.save_name='';
      form.typeValue='';
      shareSave.value=false;
    }
  }
  ,(message:any)=>{
    // error
    ElNotification.error({
      title: '注意',
      message: '发布失败'+message,
      showClose: true,
      duration: 5000
    })
  })
}

const saveInfoRef = ref<InstanceType<typeof ElTable>>()
const multipleSelection = ref<any[]>([])
const handleSelectionChange = (val: any[]) => {
  multipleSelection.value = val
}
const handleRowClick = (row:any,column:any,event:any)=>{
  if(column==null)
    return;
  // console.log(column,event.srcElement);
  if(multipleSelection.value.includes(row)){
    multipleSelection.value.slice(multipleSelection.value.findIndex((value)=>{return value===row}),1);
    saveInfoRef.value?.toggleRowSelection(row,false);
  } else {
    multipleSelection.value.push(row);
    saveInfoRef.value?.toggleRowSelection(row,true);
  }
}

const typeFormatter = (row: any, column: any) => {
  return row.type==0?'模块':'测试图'
}

const handleDeleteServerSavae = (event:any)=>{
  if(multipleSelection.value.length==0){
    return;
  }
  ElMessageBox.confirm(
    '删除操作不可逆，确定继续？',
    '请注意',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(() => {
      const deleteNames = []
      for(let item of multipleSelection.value){
        deleteNames.push(item.save_name)
      }
      HttpUtil.deleteSave(deleteNames
        ,(message:any)=>{
          // console.log(message)
          if(message.data.code!=0){
            ElNotification.error({
              title: '注意',
              message: '删除失败'+message.data.data,
              showClose: true,
              duration: 5000
            })
          } else {
            ElNotification.success({
              title: '注意',
              message: '删除成功',
              showClose: true,
              duration: 5000
            })
            // 刷新表格
            browseServerSave({});
          }
        }
        ,(message:any)=>{
          ElNotification.error({
            title: '注意',
            message: '删除失败'+message.data.data,
            showClose: true,
            duration: 5000
          })
        })
    })
    .catch(() => {
      // 取消
    })
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
      <el-table :data="saveInfoData" ref="saveInfoRef" @selection-change="handleSelectionChange" @row-click="handleRowClick">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="type" label="发布类型" show-overflow-tooltip width="120" sortable :filters="typeFilter" :filter-method="filterHandler" :formatter="typeFormatter">
        </el-table-column>
        <el-table-column prop="category" label="业务分类" show-overflow-tooltip width="140" sortable :filters="categoryFilter" :filter-method="filterHandler">
        </el-table-column>
        <el-table-column prop="save_name" label="名称" show-overflow-tooltip min-width="140" sortable>
        </el-table-column>
        <el-table-column prop="description" label="备注" show-overflow-tooltip min-width="80">
        </el-table-column>
        <el-table-column prop="save_time" label="发布时间" width="180" sortable>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button type="danger" @click="handleDeleteServerSavae">删除</el-button>
        <el-button type="primary" @click="handleImportServerSave">导入</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="shareSave"
      title="发布共享存档"
      width="30%"
      destroy-on-close
    >
      <el-form :model="form" label-width="120px">
        <el-form-item label="发布类型">
          <el-select v-model="form.typeValue" filterable placeholder="选择或输入">
            <el-option
              v-for="item in typeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <!-- <el-form-item label="发布分类">
          <el-select v-model="form.categoryValue" filterable placeholder="选择或输入">
            <el-option
              v-for="item in categoryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item> -->
        <el-form-item label="发布分类">
          <el-autocomplete
            v-model="form.categoryValue"
            :fetch-suggestions="queryCategory"
            clearable
            style="width:300px;"
            placeholder="选择或输入"
          />
        </el-form-item>
        <el-form-item label="名称">
          <el-input
            v-model="form.save_name"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="form.description"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="handleUploadShareSave">发布</el-button>
      </template>
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
.el-icon:hover{
  color:#79bbff;
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