<script setup lang="ts">

import * as tn from '@/TestNode';
import { ConstantNode } from '@/TestNode';
import { formContextKey, formItemValidateStates } from 'element-plus';
import type { column } from 'element-plus/es/components/table-v2/src/common';
import { onMounted, ref, watch } from 'vue';

const form= ref(new tn.BaseNode('',{params:[]},{params:[]},0,0,'',{},'???'));

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
    if(form.value.typeName==tn.ConstantNode.name||form.value.typeName==tn.VariableNode.name){
      paramCount.value=form.value.outputs.params.length;
    } else {
      paramCount.value=form.value.outputs.params.length-1;
    }
    
  }
}

const dataChanged = (event)=>{
  const updateEvent = new CustomEvent('dataNodeChanged',{detail:{graphName:props.graphName,nodeName:props.nodeName}});
  dispatchEvent(updateEvent);
}

const paramCount = ref(0)
const minCount = ref(0);

const countChange = ()=>{
  if(form.value.typeName==tn.ConstantNode.name){
    while(paramCount.value>form.value.outputs.params.length){
      form.value.outputs.addParam(tn.ConstantParam,'data_'+form.value.outputs.params.length,tn.ParamRuntimeTypeEnums.StringValue);
    }
    while(paramCount.value<form.value.outputs.params.length){
      form.value.outputs.pop()
    }
  } else if(form.value.typeName==tn.SwitchNode.name) {
    while(paramCount.value + 1>form.value.outputs.params.length){
      form.value.inputs.addParam(tn.VariableParam,'case_'+form.value.outputs.params.length,tn.ParamRuntimeTypeEnums.VarNameValue);
      form.value.outputs.addParam(tn.FlowParam,'next_'+form.value.outputs.params.length,tn.ParamRuntimeTypeEnums.VarNameValue);
    }
    while(paramCount.value + 1<form.value.outputs.params.length){
      form.value.inputs.pop()
      form.value.outputs.pop()
    }
  } else if(form.value.typeName==tn.ModuleBeginNode.name||form.value.typeName==tn.ModuleEndNode.name){
    while(paramCount.value + 1>form.value.outputs.params.length){
      form.value.inputs.addParam(tn.VariableParam,'data_'+form.value.outputs.params.length,tn.ParamRuntimeTypeEnums.VarNameValue);
      form.value.outputs.addParam(tn.VariableParam,'data_'+form.value.outputs.params.length,tn.ParamRuntimeTypeEnums.VarNameValue);
    }
    while(paramCount.value + 1<form.value.outputs.params.length){
      form.value.inputs.pop()
      form.value.outputs.pop()
    }
  }
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

      <!-- 可变参数类型节点，数量修改 -->
      <el-form-item label="可变参数数量" v-if="form.typeName==tn.ConstantNode.name 
                                            || form.typeName==tn.SwitchNode.name 
                                            || form.typeName==tn.ModuleBeginNode.name
                                            || form.typeName==tn.ModuleEndNode.name">
        <el-input-number v-model="paramCount" :max="5" :min="minCount" @change="countChange"></el-input-number>
      </el-form-item>

      <!-- ============ 常量、变量节点 ============ -->
      <el-form-item label="输出参数" v-if="form.typeName && form.typeName==tn.ConstantNode.name || form.typeName==tn.VariableNode.name">
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
      <!-- ============ 常量、变量节点 ============ -->

      <!-- ============ Switch节点 ============ -->
      <el-form-item label="分支用例" v-if="form.typeName && form.typeName==tn.SwitchNode.name">
        <el-table :data="form.inputs.params.slice(2)" style="width: 100%" >
          <el-table-column label="分支用例名称" >
            <template #default="scope">
              <template v-if="scope.row.paramName!='prev'&&scope.row.paramName!='data'">
                <el-input v-model="scope.row.paramName" :value="scope.row.paramName" @input="dataChanged"></el-input>
              </template>
            </template>
          </el-table-column>
        </el-table>
      </el-form-item>

      <el-form-item label="输出分支" v-if="form.typeName && form.typeName==tn.SwitchNode.name">
        <el-table :data="form.outputs.params.slice(1)" style="width: 100%" >
          <el-table-column label="输出分支名称">
            <template #default="scope">
              <el-input v-model="scope.row.paramName" :value="scope.row.paramName" @input="dataChanged"></el-input>
            </template>
          </el-table-column>
        </el-table>
      </el-form-item>
      <!-- ============ Switch节点 ============ -->

      <!-- ============ 模块起始终止节点 ============ -->
      <el-form-item label="模块输入" v-if="form.typeName && form.typeName==tn.ModuleBeginNode.name">
        <el-table :data="form.outputs.params.slice(1)" style="width: 100%" >
          <el-table-column label="输入参数名称">
            <template #default="scope">
              <el-input v-model="scope.row.paramName" :value="scope.row.paramName" @input="dataChanged"></el-input>
            </template>
          </el-table-column>
        </el-table>
      </el-form-item>
      
      <el-form-item label="模块输出" v-if="form.typeName && form.typeName==tn.ModuleEndNode.name">
        <el-table :data="form.outputs.params.slice(1)" style="width: 100%" >
          <el-table-column label="输出参数名称">
            <template #default="scope">
              <el-input v-model="scope.row.paramName" :value="scope.row.paramName" @input="dataChanged"></el-input>
            </template>
          </el-table-column>
        </el-table>
      </el-form-item>
      <!-- ============ 模块起始终止节点 ============ -->
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