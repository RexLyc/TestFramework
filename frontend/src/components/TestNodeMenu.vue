  
<script lang="ts" setup>
import * as tn from '@/TestNode';
import {ref, onMounted } from 'vue';
import {usePressElementStore} from '@/stores/counter'

const menuData = ref(new Array());
const pressedElementStore = usePressElementStore();

class NodeMenuItem {
    index:String;
    children:Array<NodeMenuItem>;
    constructor(index:String,children:Array<NodeMenuItem>){
        this.index=index;
        this.children=children;
    }
}

onMounted(()=>{
    // 加载全部的节点
    const categorySet = new Map<string,Array<tn.NodeInterface>>();
    for(let type of tn.NodeFactory.nodeTypeMap.values()){
        if(!categorySet.get(type.categoryName))
            categorySet.set(type.categoryName,new Array());
        categorySet.get(type.categoryName)?.push(type)
    }
    for(let categoryName of categorySet.keys()){
        const typeArray = new Array<NodeMenuItem>();
        for(let type of categorySet.get(categoryName)!.values()){
            typeArray.push(new NodeMenuItem(type.typeName,[]));
        }
        const tempItem = new NodeMenuItem(categoryName,typeArray);
        menuData.value.push(tempItem)
    }
})

function mousedown(event) {
    pressedElementStore.setCurrent(event.target);
}

</script>

<template>
    <el-scrollbar >
    <el-menu
        default-active="2"
        class="el-menu-vertical-demo"
    >

        <template v-for="item in menuData">
            <el-menu-item v-bind:key="item" :index="item.index" v-if="item.children==undefined || item.children.length==0">
                <template #title>
                    <span>{{ item.title }}</span>
                </template>
            </el-menu-item>

            <el-sub-menu v-bind:key="item" :index="item.index" v-if="item.children!=undefined && item.children.length!=0">
                <template #title>
                    <el-icon v-if="item.index==tn.CategoryEnums.CommonType"><Star/></el-icon>
                    <el-icon v-else-if="item.index==tn.CategoryEnums.WebType"><MostlyCloudy/></el-icon>
                    <el-icon v-else-if="item.index==tn.CategoryEnums.FlowType"><Switch/></el-icon>
                    <el-icon v-else-if="item.index==tn.CategoryEnums.SerialType"><Link/></el-icon>
                    <el-icon v-else-if="item.index==tn.CategoryEnums.CalculateType"><EditPen/></el-icon>
                    <span>{{tn.NodeTranslator.translate(item.index)}}</span>
                    <!-- <span>{{ item.index }}</span> -->
                </template>
                <template v-for="item2 in item.children">
                    <el-menu-item :index="item2.index" v-bind:key="item2" v-if="true" @mousedown="mousedown">
                        <el-icon v-if="item2.index==tn.BeginNode.typeName||item2.index==tn.ModuleBeginNode.typeName"><Position  /></el-icon>
                        <el-icon v-else-if="item2.index==tn.EndNode.typeName||item2.index==tn.ModuleEndNode.typeName"><SwitchButton /></el-icon>
                        <el-icon v-else-if="item2.index==tn.LogNode.typeName"><Document /></el-icon>
                        <el-icon v-else-if="item2.index==tn.ExtractNode.typeName"><Scissor /></el-icon>
                        <el-icon v-else-if="item2.index==tn.MergeNode.typeName"><Paperclip /></el-icon>
                        <!-- Setting 图标在windows下有可能卡顿，换掉 -->
                        <!-- <el-icon v-else-if="item2.index==tn.GlobalNode.typeName"><Setting /></el-icon> -->
                        <el-icon v-else-if="item2.index==tn.GlobalNode.typeName"><Van /></el-icon>
                        <el-icon v-else-if="item2.index==tn.SendNode.typeName"><Ship /></el-icon>
                        <el-icon v-else-if="item2.index==tn.RecvNode.typeName"><Box /></el-icon>
                        <el-icon v-else-if="item2.index==tn.ConstantNode.typeName"><Lock /></el-icon>
                        <el-icon v-else-if="item2.index==tn.HttpNode.typeName"><ChromeFilled /></el-icon>
                        <el-icon v-else-if="item2.index==tn.TCPNode.typeName"><PhoneFilled /></el-icon>
                        <el-icon v-else-if="item2.index==tn.UDPNode.typeName"><PhoneFilled /></el-icon>
                        <el-icon v-else-if="item2.index==tn.WebSocketNode.typeName"><PhoneFilled /></el-icon>
                        <el-icon v-else-if="item2.index==tn.SerialNode.typeName"><MagicStick /></el-icon>
                        <el-icon v-else-if="item2.index==tn.IfNode.typeName"><Guide /></el-icon>
                        <el-icon v-else-if="item2.index==tn.SwitchNode.typeName"><List /></el-icon>

                        <el-icon v-else-if="item2.index==tn.AddMinusNode.typeName"><Plus /></el-icon>
                        <el-icon v-else-if="item2.index==tn.MultiDivNode.typeName"><Close /></el-icon>
                        <el-icon v-else-if="item2.index==tn.BiggerNode.typeName"><ArrowRight /></el-icon>
                        <el-icon v-else-if="item2.index==tn.EqualNode.typeName"><ScaleToOriginal /></el-icon>
                        <el-icon v-else-if="item2.index==tn.AndNode.typeName"><Finished /></el-icon>
                        <el-icon v-else-if="item2.index==tn.OrNode.typeName"><More /></el-icon>
                        <el-icon v-else-if="item2.index==tn.NotNode.typeName"><Warning /></el-icon>
                        <el-icon v-else-if="item2.index==tn.BarrierNode.typeName"><Aim /></el-icon>
                        <el-icon v-else-if="item2.index==tn.VariableNode.typeName"><Flag /></el-icon>
                        <el-icon v-else-if="item2.index==tn.SleepNode.typeName"><Moon /></el-icon>
                        <span :id="item2.index">{{tn.NodeTranslator.translate(item2.index)}}</span>
                        <!-- <span>{{ item2.index }}</span> -->
                    </el-menu-item>
                </template>
            </el-sub-menu>
        </template>
        
    </el-menu>
</el-scrollbar>
</template>

<style scoped>
.el-menu-item>span {
    cursor: move;
    /* 避免鼠标选中高亮 */
    user-select: none;
}
</style>