<script setup lang="ts">

import { h, getCurrentInstance, render, onMounted, watch } from 'vue'
// import Drawflow from 'drawflow'
// import 'drawflow/dist/drawflow.min.css'
// 两个都要引入
import '@/../Drawflow/src/drawflow.css'
import Drawflow from '@/../Drawflow/src/drawflow.js'
import '@/assets/custom-drawflow.css'

import * as tn from  '@/TestNode'
import { transform } from 'lodash'
import { ref } from 'vue'
const drawer = ref(false)

let editor: Drawflow;
let graph:tn.TestGraph;
let transformX:number=0,transformY: number=0;

const props = defineProps({
  newNode: String,
  pos_x:Number,
  pos_y:Number
})

watch(props,()=>{
  // 需要计算canvas 左上角、transform、scale
  const drawflowParent:HTMLElement = document.getElementById('drawflow')!;
  const drawflowCanvas:Element = drawflowParent.firstElementChild!;
  let left =  props.pos_x! - drawflowParent.offsetLeft ;
  let top = props.pos_y! - drawflowParent.offsetTop;
  const canvasWidth = drawflowCanvas.clientWidth;
  const canvasHeight = drawflowCanvas.clientHeight;
  // console.log(left,top,canvasWidth,canvasHeight,editor.zoom,transformX,transformY)
  // 插入时需要还原成未缩放、未平移之前的坐标
  left -= transformX;
  top -= transformY;
  var distX = canvasWidth/2 - left;
  var distY = canvasHeight/2 - top;
  distX/=editor.zoom;
  distY/=editor.zoom;
  left=canvasWidth/2-distX;
  top=canvasHeight/2-distY;
  tn.NodeFactory.addTestNode(graph,props.newNode!,left,top);
})

onMounted(()=>{
  const Vue = { version: 3, h, render };
  var id = document.getElementById("drawflow");
  editor = new Drawflow(id, Vue);
  editor.start();

  addEventListener('TGAddNewNode',(event:Event)=>{
    const newNode:tn.TGAddNewNode = event.detail;
    const node:tn.BaseNode = tn.TestGraphFactory
      .getTestGraph(newNode.testGraph)
      .nameNodeMap
      .get(newNode.nodeName)!;
    editor.addNode(node.name
      ,node.inputs
      ,node.outputs
      ,node.pos_x
      ,node.pos_y
      ,node.className
      ,node.data
      ,node.html)
  });

  editor.on('translate',(pos:{x:number,y:number})=>{
    transformX = pos.x;
    transformY = pos.y;
    // console.log(transformX,transformY)
  })
  editor.on('dblclick',(e:Event)=>{
    if(e.target==null || e.target.classList==null || e.target.classList[0] ==null)
      return;
    let nodeName = null;
    if (e.target!.classList[0] == 'drawflow-node') { 
      nodeName = (e.target as HTMLElement).getElementsByClassName('drawflow_content_node')[0].innerHTML;
    } else if(e.target!.classList[0] == 'drawflow_content_node') {
      nodeName = (e.target as HTMLElement).innerHTML;
    }
    if(nodeName){
      drawer.value=true;
    }
  })
  
  initTestGraph();

})

const initTestGraph = ()=>{
  graph = tn.TestGraphFactory.buildTestGraph("test")
  tn.NodeFactory.addTestNode(graph,tn.BeginNode.typeName,100,100);
  tn.NodeFactory.addTestNode(graph,tn.EndNode.typeName,500,100);
}

const drawflowKeyDown = (event:KeyboardEvent)=>{
  if(event.key=='*'){
    // reset position and scale
    editor.zoom=1.0;
    editor.zoom_value = 0.1;
    editor.zoom_last_value = 1;
    editor.precanvas.style.transform = "translate("+0+"px, "+0+"px) scale(1.0)";
    editor.canvas_x = 0;
    editor.canvas_y = 0;
    editor.pos_x = 0;
    editor.pos_x_start = 0;
    editor.pos_y = 0;
    editor.pos_y_start = 0;
    editor.mouse_x = 0;
    editor.mouse_y = 0;
    transformX=0;
    transformY=0;
  }
}

</script>

<template>
  <div id="drawflow" @keydown="drawflowKeyDown"></div>
  <el-drawer v-model="drawer" title="I am the title" :with-header="false">
    <span>Hi there!</span>
  </el-drawer>
</template>

<style scoped>
#drawflow{
  height: 100%;
  overflow: hidden;
}
</style>