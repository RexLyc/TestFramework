  
<script lang="ts" setup>
import * as tn from '@/TestNode';
import {
    Document,
    Menu as IconMenu,
    Location,
    Setting,
} from '@element-plus/icons-vue'
import { onMounted } from 'vue';

const menuData = [
    {
        index:'/',
        icon:'el-icon-menu',
        title:'通用类型',
        id:1,
        children:[
            {
                index:'/one',
                title:'起始',
                id:2-1,
            },
            {
                index:'/two',
                title:'结束',
                id:2-2,
            },
        ]
    },
    {
        index:'/one',
        icon:'el-icon-menu',
        title:'串口类型',
        id:2,
        children:[
            {
                index:'/one',
                title:'串口1',
                id:2-1,
            },
            {
                index:'/two',
                title:'串口2',
                id:2-2,
            },
        ]
    }
];

const handleOpen = (key: string, keyPath: string[]) => {
    console.log(key, keyPath)
}
const handleClose = (key: string, keyPath: string[]) => {
    console.log(key, keyPath)
}

onMounted(()=>{
    // 加载全部的节点
    for(let type of tn.NodeFactory.nodeTypeMap.entries()){
        menuData.push
    }
})
</script>

<template>
    <el-menu
        default-active="2"
        class="el-menu-vertical-demo"
        @open="handleOpen"
        @close="handleClose"
    >
        
        <template v-for="item in menuData">
            <el-menu-item v-bind:key="item" :index="item.index" v-if="item.children==undefined">
                <template #title>
                    <!--<i :class="item.icon"></i> -->
                    <span>{{ item.title }}</span>
                </template>
            </el-menu-item>

            <el-sub-menu v-bind:key="item" :index="item.index" v-if="item.children!=undefined">
                <template #title>
                    <!--<i :class="item.icon"></i> -->
                    <span>{{ item.title }}</span>
                </template>
                <template v-for="item2 in item.children" >
                    <el-menu-item :index="item2.index" v-bind:key="item2" v-if="true">
                        {{ item2.title }}
                    </el-menu-item>
                </template>
            </el-sub-menu>
        </template>
        
    </el-menu>
</template>

