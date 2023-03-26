<script setup lang="ts">

import { h, getCurrentInstance, render, onMounted, watch } from 'vue'
// import Drawflow from 'drawflow'
// import 'drawflow/dist/drawflow.min.css'
// 两个都要引入
import '@/../Drawflow/src/drawflow.css'
import Drawflow from '@/../Drawflow/src/drawflow.js'
import '@/assets/custom-drawflow.css'
import NodeDetail from './NodeDetail.vue'

import * as tn from  '@/TestNode'
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

// 绘制节点id和数据节点id映射(双向)
const drawDataIdMap = new Map<string,string>();
const dataDrawIdMap = new Map<string,string>();

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

function addClassFor(className:string,classAdd:string){
  for(const element of document.querySelectorAll("[class*="+className+"]")){
    (element as Element).classList.add(classAdd);
  }
}

function removeClassFor(className:string,classRemove:string){
  for(const element of document.querySelectorAll("[class*="+className+"]")){
    (element as Element).classList.remove(classRemove);
  }
}

function removeAllClass(className:string){
  removeClassFor(className,className);
}

const HiddenCSS = "incompatible_param";
const currentNode = ref();

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
    const drawId = editor.addNode(node.name
      ,node.inputs
      ,node.outputs
      ,node.pos_x
      ,node.pos_y
      ,node.typeName
      ,node.data
      ,node.html);
    drawDataIdMap.set(String(drawId),node.name);
    dataDrawIdMap.set(node.name,String(drawId));
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
      // build menu
      outputData.value=tn.TestGraphFactory.exportNode(graph.graphName,nodeName);
      drawer.value=true;
      detailGraphName.value = graph.graphName;
      detailNodeName.value = nodeName;
    }
  })

  editor.on('connectionStart',(detail)=>{
    const outputIndex:number =detail.output_class.slice(7) - 1;
    addClassFor(tn.ParamCategoryEnums.All,HiddenCSS);
    // for(const element of document.querySelectorAll("[class*="+tn.ParamCategoryEnums.All+"]")){
    //   (element as Element).classList.add('incompatible_param');
    // }
    const paramCategoryName = graph.nameNodeMap.get(drawDataIdMap.get(detail.output_id))?.outputs.params[outputIndex].categoryNames;
    for(const categoryName of paramCategoryName){
      removeClassFor(categoryName,HiddenCSS);
    }
  });

  editor.on('connectionCreated',(detail)=>{
    removeAllClass('incompatible_param');
    // 更新数据节点
    graph.addConnection(drawDataIdMap.get(detail.output_id)!
      ,detail.output_class.slice(7)-1
      ,drawDataIdMap.get(detail.input_id)!
      ,detail.input_class.slice(6)-1);
  });

  editor.on('connectionCancel',(isCancel)=>{
    removeAllClass('incompatible_param');
  })

  editor.on('connectionRemoved',(detail)=>{
    console.log('connection %o removing',detail);
    graph.removeConnection(drawDataIdMap.get(detail.output_id)!
      ,detail.output_class.slice(7)-1
      ,drawDataIdMap.get(detail.input_id)!
      ,detail.input_class.slice(6)-1);
    console.log('connection %o removed',detail);
  });

  editor.on('nodeRemoved',(id:string)=>{
    console.log('node %o removing',id);
    const dataId = drawDataIdMap.get(id);
    drawDataIdMap.delete(id);
    graph.removeNode(dataId);
    dataDrawIdMap.delete(dataId);
    console.log('node %o removed',id);
  })

  editor.on('nodeMoved',(id:string)=>{
    const element = document.getElementById('node-'+id);
    graph.nameNodeMap.get(drawDataIdMap.get(id)!)!.pos_x=Number(element?.style.left.slice(0,-2));
    graph.nameNodeMap.get(drawDataIdMap.get(id)!)!.pos_y=Number(element?.style.top.slice(0,-2));
  });
  
  initTestGraph();

  addEventListener('importTestGraph',importGraph);
  addEventListener('exportTestGraph',exportGraph);


  editor.on('keydown',(event)=>{
    if(event.key=='*'){
      resetView();
    }
  })
})

const clearAll=()=>{
  editor.clear();
  resetView();
  drawDataIdMap.clear();
  dataDrawIdMap.clear();
}

const initTestGraph = ()=>{
  graph = tn.TestGraphFactory.buildTestGraph("test")
  tn.NodeFactory.addTestNode(graph,tn.BeginNode.typeName,100,100);
  tn.NodeFactory.addTestNode(graph,tn.EndNode.typeName,500,100);
}

//TODO: 对导入的节点进行绘制
const initNode = ()=>{
  for(let node of graph.nameNodeMap.values()){
    const drawId = editor.addNode(node.name
      ,node.inputs
      ,node.outputs
      ,node.pos_x
      ,node.pos_y
      ,node.typeName
      ,node.data
      ,node.html);
    drawDataIdMap.set(String(drawId),node.name);
    dataDrawIdMap.set(node.name,String(drawId));
  }
}

//TODO: 对导入的连接进行绘制
const initConnections = ()=>{
  for(let node of graph.nameNodeMap.values()){
    for(let outputParam in node.outputs.params){
      // console.log(outputParam);
      for(let otherParam of node.outputs.params[outputParam].paramRef){
        editor.addConnection(
          dataDrawIdMap.get(node.name)
          ,dataDrawIdMap.get(otherParam.substring(0,otherParam.indexOf('$')))
          ,'output_'+(Number(outputParam)+1)
          ,'input_'+(Number(otherParam.substring(otherParam.indexOf('$')+1))+1)
        );
      }
    }
  }
}


const outputData = ref(new String);

//TODO: 导出测试图
const exportGraph = ()=>{
  var exportJson = tn.TestGraphFactory.exportGraph(graph.graphName);
  // console.log(exportJson)
  outputData.value=exportJson;
  drawer.value=true;
  download('test.json',exportJson);
}

const waitGraph = ref();

//TODO: 导入测试图
const importGraph = (event)=>{
  // 重建测试图
  waitGraph.value = tn.TestGraphFactory.importGraph(event.detail);
  if(waitGraph.value != null){
    dialogVisible.value=true;
  }
}

const cleanAndDraw = (event)=>{
  dialogVisible.value=false;
  // 清空当前
  clearAll();
  tn.TestGraphFactory.removeTestGraph(graph.graphName);
  tn.TestGraphFactory.addTestGraph(waitGraph.value);
  graph = waitGraph.value;
  console.log(graph);
  // 绘制节点
  initNode();
  // 绘制连接
  initConnections();
}

const resetView=()=>{
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


function download(filename, content) {
  const arraybuffer = new TextEncoder().encode(content).buffer;
  const blob = new Blob([arraybuffer], { type: 'text/plain;base64' });
  const reader = new FileReader();
  reader.readAsDataURL(blob);
  reader.onload = (event) => {
    const element = document.createElement('a');
    element.href = event.target.result;
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };
}

const dialogVisible = ref(false);

// document.onkeydown=(event:KeyboardEvent)=>{
//   if(event.key=='*'){
//     resetView();
//   }
//   console.log("???");
//   return true;
// }


const detailGraphName = ref("");
const detailNodeName = ref("");
</script>

<template>
  <div id="container">
    <div id="drawflow"></div>
  
      <el-drawer v-model="drawer" title="I am the title" :with-header="false">
        <span>JsonData</span>
        <el-text class="mx-1" size="large">{{ outputData }}</el-text>
        <NodeDetail :graph-name="detailGraphName" :node-name="detailNodeName"/>
      </el-drawer>
      
      <el-dialog
        v-model="dialogVisible"
        title="注意"
        width="20%"
      >
        <span>将会清空当前测试图，并导入新测试图。请确认当前测试图已保存。</span>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="cleanAndDraw">
              确认
            </el-button>
          </span>
        </template>
      </el-dialog>
  </div>
</template>

<style scoped>
#container {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
}

#drawflow{
  height: 100%;
  overflow: hidden;
}
.el-text {
  word-break:normal; 
  width:auto; 
  display:block; 
  white-space:pre-wrap;
  word-wrap : break-word ;
  overflow: hidden ;
  size:large;
  background-color: #EBEEF5;
  color: #000000;
}
</style>