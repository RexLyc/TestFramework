<script setup lang="ts">

import * as tn from '@/TestNode';
import { ConstantNode } from '@/TestNode';
import { formContextKey, formItemValidateStates } from 'element-plus';
import type { column } from 'element-plus/es/components/table-v2/src/common';
import { onMounted, ref, watch } from 'vue';
import { Codemirror } from 'vue-codemirror';
import { python } from '@codemirror/lang-python';

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
      // 调整表格内的inputCode
      while(inputCode.value.length<form.value.outputs.params.length){
        inputCode.value.push(false);
      }
      inputCode.value.splice(form.value.outputs.params.length);
      let i=0;
      for(let item of form.value.outputs.params){
        if(item.paramType==tn.ParamRuntimeTypeEnums.PythonValue){
          inputCode.value[i]=true
        } else {
          inputCode.value[i]=false
        }
        i++;
      }
    } else {
      paramCount.value=form.value.outputs.params.length-1;
    }
  }
}

const inputCode = ref<boolean[]>([]);

const paramTypeChanged = (value:any)=>{
  // 目前只有常量、变量需要考虑这个问题
  // 检查所有参数，将类型为Python的修改为codemirror
  while(inputCode.value.length<form.value.outputs.params.length){
    inputCode.value.push(false);
  }
  inputCode.value.splice(form.value.outputs.params.length);
  let i = 0;
  for(let item of form.value.outputs.params){
    if(item.paramType==tn.ParamRuntimeTypeEnums.PythonValue){
      if(inputCode.value[i]==false){
        item.paramValue = 
`def func(args):
  # 你的代码
  return 'result'`
      }
      inputCode.value[i]=true
    } else {
      inputCode.value[i]=false
    }
    i++;
  }
  // 将非python的修改为普通
  dataChanged(value);
}

const dataChanged = (event:any)=>{
  if(form.value.typeName==tn.ModuleBeginNode.name||form.value.typeName==tn.ModuleEndNode.name){
    // 匹配输入输出名字
    for(let i=1;i!=form.value.inputs.params.length;++i){
      form.value.inputs.params[i].paramName=form.value.outputs.params[i].paramName;
    }
  }
  const updateEvent = new CustomEvent('dataNodeChanged',{detail:{graphName:props.graphName,nodeName:props.nodeName}});
  dispatchEvent(updateEvent);
}

const paramCount = ref(0)
const minCount = ref(0);

const countChange = ()=>{
  const declineNum = paramCount.value - form.value.outputs.params.length;
  if(form.value.typeName==tn.ConstantNode.name){
    while(paramCount.value>form.value.outputs.params.length){
      form.value.outputs.addParam(tn.ConstantParam,'data_'+form.value.outputs.params.length,tn.ParamRuntimeTypeEnums.StringValue);
    }
    while(paramCount.value<form.value.outputs.params.length){
      form.value.outputs.pop();
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
  // IO参数数量变动事件
  const updateEvent = new CustomEvent('nodeParamCountChanged',{detail:{graphName:props.graphName,nodeName:props.nodeName,decline:declineNum}});
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
          <el-table-column label="参数名称" width="150px">
            <template #default="scope">
              <el-input v-model="scope.row.paramName" :value="scope.row.paramName" @input="dataChanged"></el-input>
            </template>
          </el-table-column>

          <el-table-column label="参数类型" width="150px">
            <template #default="scope">
              <el-select v-model="scope.row.paramType" placeholder="Select" @change="paramTypeChanged">
                <template v-for="item in tn.ParamRuntimeTypeEnums">
                  <el-option v-if="item !=tn.ParamRuntimeTypeEnums.VarNameValue" :key="item" :label="tn.ParamTranslator.translate(item)" :value="item"/>
                </template>
              </el-select>
            </template>
          </el-table-column>

          <el-table-column label="参数值">
            <template #default="scope">
              <el-input v-if="!inputCode[scope.$index]" type="textarea" autosize v-model="scope.row.paramValue" :value="scope.row.paramValue" @input="dataChanged"></el-input>
              <codemirror v-if="inputCode[scope.$index]" :extensions="[python()]" v-model="scope.row.paramValue" :value="scope.row.paramValue" @input="dataChanged"/>
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

.codemirror {

}

</style>