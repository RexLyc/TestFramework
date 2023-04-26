import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubleCount = computed(() => count.value * 2)
  function increment() {
    count.value++
  }

  return { count, doubleCount, increment }
})


export const usePressElementStore = defineStore('currentPressedElement',()=>{
  const currentPressedElement = ref()
  function setCurrent(element:HTMLElement|null) {
    currentPressedElement.value = element;
  }

  return {currentPressedElement,setCurrent}
})

export const useGraphNameStore = defineStore('currentGraphName',()=>{
  const currentGraphName = ref()
  function setCurrent(name:string) {
    currentGraphName.value = name;
  }

  return {currentGraphName,setCurrent}
})

export const useFlowModeStore = defineStore('currentFlowMode',()=>{
  const currentFlowMode = ref()
  function setCurrent(name:string) {
    if(name!=='graph'&&name!=='module'){
      throw Error('invalid mode');
    }
    currentFlowMode.value = name;
  }

  return {currentFlowMode,setCurrent}
})