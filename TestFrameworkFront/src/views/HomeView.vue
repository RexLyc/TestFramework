<script setup lang="ts">
import FlowCanvas from '../components/FlowCanvas.vue'
import HeadMenu from '../components/HeadMenu.vue'
import TestNodeMenu from '../components/TestNodeMenu.vue'

document.onmousedown=(event)=>{
  console.log("hello from document")
}

document.onmouseup=(event)=>{

}

document.onmousemove=(event)=>{

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
          <FlowCanvas/>
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