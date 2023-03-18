<script setup lang="ts">

import { h, getCurrentInstance, render, onMounted } from 'vue'
import Drawflow from 'drawflow'
import 'drawflow/dist/drawflow.min.css'
import { ref } from 'vue'

defineProps<{
  msg: string
}>()

onMounted(()=>{
  const Vue = { version: 3, h, render };
var id = document.getElementById("drawflow");
console.log(id)
const editor = new Drawflow(id, Vue);
editor.start();

const data = {
      name: ''
    };

    editor.addNode('foo', 1, 1, 100, 200, 'foo', data, 'Foo');
    editor.addNode('bar', 1, 1, 400, 100, 'bar', data, 'Bar A');
    editor.addNode('bar', 1, 1, 400, 300, 'bar', data, 'Bar B');

    editor.addConnection(1, 2, "output_1", "input_1");
    editor.addConnection(1, 3, "output_1", "input_1");

})


// export default {
//   setup() {
//     const count = ref(0)
//     // const Vue = { version: 3, h, render };
//     // var id = document.getElementById("drawflow");
//     // const editor = new Drawflow(id, Vue);
//     // editor.start();
//     // 返回值会暴露给模板和其他的选项式 API 钩子
//     return {
//       count
//     }
//   },

//   mounted() {
//     console.log(this.count) // 0
//   }
// }


// this.editor = new Drawflow(id, Vue);
// // Pass render Vue 3 Instance
// const internalInstance = getCurrentInstance()
// editor.value = new Drawflow(id, Vue, internalInstance.appContext.app._context);
</script>

<template>
  <div class="greetings">
    <h1 class="green">{{ msg }}</h1>
    <h3>
      You’ve successfully created a project with
      <a href="https://vitejs.dev/" target="_blank" rel="noopener">Vite</a> +
      <a href="https://vuejs.org/" target="_blank" rel="noopener">Vue 3</a>. What's next?
    </h3>
    <div id="drawflow" class="parent-drawflow" tabindex="0" style="width:500px;height:500px;"></div>
  </div>
</template>

<style scoped>
h1 {
  font-weight: 500;
  font-size: 2.6rem;
  top: -10px;
}

h3 {
  font-size: 1.2rem;
}

.greetings h1,
.greetings h3 {
  text-align: center;
}

@media (min-width: 1024px) {
  .greetings h1,
  .greetings h3 {
    text-align: left;
  }
}
</style>
