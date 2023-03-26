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
  console.log('event');
}
</script>

<template>
  <div id="container">
    <el-form :v-model="shown" :model="form">
      <el-form-item label="节点名称">
        <el-input  v-model="form.html" @change="dataChanged" @formchange="dataChanged"/>
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