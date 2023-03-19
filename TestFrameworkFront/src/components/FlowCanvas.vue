<script setup lang="ts">

import { h, getCurrentInstance, render, onMounted } from 'vue'
import Drawflow from 'drawflow'
// 两个都要引入
import 'drawflow/dist/drawflow.min.css'
import '@/assets/custom-drawflow.css'
import * as tn from  '@/TestNode'

var editor: Drawflow;
var graph:tn.TestGraph;

onMounted(()=>{
  const Vue = { version: 3, h, render };
  var id = document.getElementById("drawflow");
  // const internalInstance = getCurrentInstance()
  // editor = new Drawflow(id, Vue, internalInstance.appContext.app._context);
  editor = new Drawflow(id, Vue);
  editor.start();

  // const data = {
  //   name: 'haha',
  //   age:'2'
  // };
  // editor.zoom_min=0.3;
  // editor.addNode('foo', 1, 2, 100, 200, 'foo', data, 'Foo');
  // editor.addNode('bar', 1, 1, 400, 100, 'bar', data, 'Bar A');
  // editor.addNode('bar', 1, 1, 400, 300, 'bar', data, 'Bar B');

  // editor.addConnection(1, 2, "output_1", "input_1");
  // editor.addConnection(1, 3, "output_1", "input_1");
  initTestGraph();

})

const initTestGraph = ()=>{
  graph = tn.TestGraphFactory.buildTestGraph("test")
  tn.NodeFactory.addTestNode(graph,tn.BeginNode.typeName,100,100);
  tn.NodeFactory.addTestNode(graph,tn.BeginNode.typeName,100,200);
  for(let node of graph.nameNodeMap.values()){
    editor.addNode(node.name
      ,node.inputs.length
      ,node.outputs.length
      ,node.pos_x
      ,node.pos_y
      ,node.className
      ,node.data
      ,node.html)
  }
  console.log(graph.nameNodeMap)
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
  }
}

</script>

<template>
  <div id="drawflow" @keydown="drawflowKeyDown"></div>
</template>

<style scoped>
#drawflow{
  height: 100%;
  overflow: hidden;
}
</style>