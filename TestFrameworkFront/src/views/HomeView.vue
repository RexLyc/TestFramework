<script setup lang="ts">
import FlowCanvas from '../components/FlowCanvas.vue'
import HeadMenu from '../components/HeadMenu.vue'
import TestNodeMenu from '../components/TestNodeMenu.vue'
import {usePressElementStore} from '@/stores/counter'
import * as tn from '@/TestNode';
import {ref, onMounted } from 'vue';



onMounted(()=>{
  // pass
})

const newNode = ref()
const posX = ref()
const posY = ref()

const pressedElementStore = usePressElementStore();
const beginDrag = ref(new Boolean(false));
const beginPressed = ref(new Boolean(false));
const dragDiv = ref(null)
document.onmousedown=(event:MouseEvent)=>{
  if(event.button==2) // 不处理右键
    return true;
  const element:HTMLElement = pressedElementStore.currentPressedElement;
  if(element && element.id && tn.NodeFactory.nodeTypeMap.get(element.id)){
    beginPressed.value=true;
  }
  return false; //避免选中文本
}

document.onmouseup=(event)=>{
  if(event.button==2) // 不处理右键
    return true;
  if(beginPressed.value==true&&beginDrag.value==true){
    //
    // console.log('create node: ',beginPressed,beginDrag);
    newNode.value=pressedElementStore.currentPressedElement.id;
    posX.value=event.x;
    posY.value=event.y;
  }
  beginDrag.value=beginPressed.value=false;
  pressedElementStore.setCurrent(null);
  if(dragDiv.value!==null){
    dragDiv.value.remove();
  }
  dragDiv.value=null;
  return false; //避免选中文本
}

document.onmousemove=(event)=>{
  if(event.button==2) // 不处理右键
    return true;
  if(beginPressed.value==true){
    beginDrag.value=true;
    if(dragDiv.value===null){
      dragDiv.value = document.createElement('div');
      dragDiv.value.innerHTML=pressedElementStore.currentPressedElement.innerHTML
      dragDiv.value.style.position='fixed';
      // 随便挂在某个节点下面
      pressedElementStore.currentPressedElement.appendChild(dragDiv.value);
      // console.log('create div: %o %o',pressedElementStore.currentPressedElement.innerHTML,dragDiv.value);
    }
    dragDiv.value.style.top=event.clientY+'px';
    dragDiv.value.style.left=event.clientX+'px';
  }
  return false; //避免选中文本
}

</script>

<template>
    <el-container>
      <el-header>
        <!--  标题  !-->
        <HeadMenu />
      </el-header>
      <el-main>
        <el-container>
          <el-aside >
            <!--  左侧节点  !-->
           <TestNodeMenu />
          </el-aside>
          <el-main>
            <!--  主画板  !-->
          <FlowCanvas :new-node="newNode" :pos_x="posX" :pos_y="posY"/>
          </el-main>
        </el-container>
      </el-main>
    </el-container>
  
</template>

<style scoped>
.el-container {
  height: 100%;
}
.el-main {
  padding: 0;
}
.el-header {
  padding: 0;
}
</style>