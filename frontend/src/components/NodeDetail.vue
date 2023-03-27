<script setup lang="ts">

import * as tn from '@/TestNode';
import { formContextKey } from 'element-plus';
import { onMounted, ref, watch } from 'vue';

const form= ref(new tn.BaseNode('',{params:[]},{params:[]},0,0,'',{},'???'));

const inputName = ref(new String());
const shown =ref(false);

const props = defineProps({
  graphName:String,
  nodeName:String
});

onMounted(()=>{
  setFormNode();
})

watch(props,()=>{
  setFormNode();
})

const setFormNode = ()=>{
  if(props.graphName!=null&&props.nodeName!=null){
    form.value=tn.TestGraphFactory.getTestGraph(props.graphName).nameNodeMap.get(props.nodeName)!;
  }
}

const dataChanged = (event)=>{
  const updateEvent = new CustomEvent('dataNodeChanged',{detail:{graphName:props.graphName,nodeName:props.nodeName}});
  dispatchEvent(updateEvent);
}

</script>

<template>
  <div id="container">
    <el-form :v-model="shown" :model="form" @submit.prevent>
      <el-form-item label="节点名称">
        <el-input  v-model="form.html" @input="dataChanged"/>
      </el-form-item>
      <!--
      <el-form-item label="输入参数">
        <el-table :data="form.inputs.params" style="width: 100%">
          <el-table-column prop="paramName" label="参数名称"/>
          <el-table-column prop="paramType" label="参数动态类型" />
          <el-table-column prop="paramRef" label="参数引用" />
          <el-table-column prop="paramValue" label="参数值"/>
        </el-table>
      </el-form-item>
      -->
      <!-- ConstantNode专用，注意禁止引用类型参数 -->
      <el-form-item label="输出参数" v-if="form.typeName==tn.ConstantNode.name">
        <el-table :data="form.outputs.params" style="width: 100%">
          <el-table-column label="参数名称">
            <template #default="scope">
              <el-input v-model="scope.row.paramName" :value="scope.row.paramName" @input="dataChanged"></el-input>
            </template>
          </el-table-column>

          <el-table-column label="参数类型">
            <template #default="scope">
              <el-select v-model="scope.row.paramType" placeholder="Select" @change="dataChanged">
                <template v-for="item in tn.ParamRuntimeTypeEnums">
                  <el-option v-if="item !=tn.ParamRuntimeTypeEnums.VarNameValue" :key="item" :label="tn.ParamTranslator.translate(item)" :value="item"/>
                </template>
              </el-select>
            </template>
          </el-table-column>

          <el-table-column label="参数值">
            <template #default="scope">
              <el-input v-model="scope.row.paramValue" :value="scope.row.paramValue" @input="dataChanged"></el-input>
            </template>
          </el-table-column>
        </el-table>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
#container {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
}

</style>