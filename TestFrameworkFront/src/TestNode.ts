// 编写全部和测试节点相关的内容

export class TestGraph {
    public graphName;
    public nameCountMap; 
    public nameNodeMap;

    constructor(graphName: string){
        this.graphName = graphName;
        this.nameCountMap = new Map<string,number>();
        this.nameNodeMap = new Map<string,BaseNode>();
    }

    newNodeName(typeName: string){
        let cur = this.nameCountMap.get(typeName)
        if(cur == undefined){
            cur = 0
        }
        cur = cur + 1
        this.nameCountMap.set(typeName,cur);
        return typeName + "_" + cur;
    }

    addNode(node:BaseNode){
        this.nameNodeMap.set(node.name,node)
    }
}

export class BaseNode {
    // for render
    public name;
    public inputs;
    public outputs;
    public pos_x;
    public pos_y;
    public className;
    public data;
    public html;
    // for test graph


    constructor(name: string
        ,inputs:Array<string>
        ,outputs:Array<string>
        ,pos_x:number
        ,pos_y:number
        ,className:string
        ,data:object
        ,html:string){
        this.name = name
        this.inputs=inputs
        this.outputs=outputs
        this.pos_x=pos_x;
        this.pos_y=pos_y;
        this.className=className;
        this.data=data;
        this.html=html;
    }


}


// Node类型体系
export interface TypeToken {
    readonly categoryName: string;
    readonly typeName: string;
    build(nodeName:string, pos_x:number, pos_y:number): BaseNode
}

export enum CategoryEnums {
    CommonType="CommonType",
}


export class BeginNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "BeginNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        let temp = new BaseNode(nodeName
            ,[]
            ,["next"]
            ,pos_x
            ,pos_y
            ,BeginNode.typeName
            ,new Object()
            ,nodeName);
        return temp;
    }
}
// 通用类型
// 这种特殊写法是为了检查categoryName作为静态成员变量
// export const CommonType: CategoryName = class CommonType {
//     static categoryName = "CommonType"; 
// }
// // 网络测试节点
// export const WebType: CategoryName = class {
//     static categoryName = "WebType"; 
// }
// // 串口测试节点
// export const SerialType: CategoryName = class {
//     static categoryName = "SerialType"; 
// }
// // 流程控制节点
// export const FlowType: CategoryName = class {
//     static categoryName = "FlowType"; 
// }

// 测试起点
// export const BeginNodeT: BuildFunc = class BeginNode implements TypeName {
//     typeName = "BeginNode";
//     static build():BaseNode{
//         let a;
        
//         return null;
//     }
// }

// export class BeginNode extends CommonType implements TypeName, BuildFunc {
//     typeName = "BeginNode";
//     static build():BaseNode{
//         return new BaseNode();
//     }
// }

// // 测试终点
// export class EndNode extends CommonType implements TypeName, BuildFunc {
//     typeName = "EndNode";
// }
// // 日志节点
// export class LogNode extends CommonType implements TypeName, BuildFunc {
//     typeName = "LogNode";
// }
// // 数据提取节点
// export class ExtractNode extends CommonType implements TypeName, BuildFunc {
//     typeName = "ExtractNode";
// }
// // 数据合并节点
// export class MergeNode extends CommonType implements TypeName, BuildFunc {
//     typeName = "MergeNode";
// }
// // 全局配置
// export class GlobalNode extends CommonType implements TypeName, BuildFunc {
//     typeName = "GlobalNode";
// }
// // 数据发送
// export class SendNode extends CommonType implements TypeName, BuildFunc {
//     typeName = "SendNode";
// }
// // 数据接收
// export class RecvNode extends CommonType implements TypeName, BuildFunc {
//     typeName = "RecvNode";
// }

// // 测试起点
// export class HttpNode extends WebType implements TypeName, BuildFunc {
//     typeName = "HttpNode";
// }
// // 测试终点
// export class TCPNode extends WebType implements TypeName, BuildFunc {
//     typeName = "TCPNode";
// }
// // 日志节点
// export class UDPNode extends WebType implements TypeName, BuildFunc {
//     typeName = "UDPNode";
// }
// // 数据提取节点
// export class WebSocketNode extends WebType implements TypeName, BuildFunc {
//     typeName = "WebSocketNode";
// }

// // 串口
// export class SerialNode extends SerialType implements TypeName, BuildFunc {
//     typeName = "SerialNode";
// }

// // 判断和跳转
// export class IfNode extends FlowType implements TypeName, BuildFunc {
//     typeName = "IfNode";
// }
// // Switch
// export class SwitchNode extends FlowType implements TypeName, BuildFunc {
//     typeName = "SwitchNode";
// }


// 测试节点工厂，负责存储节点类型，创建节点实例
export class NodeFactory {
    private constructor(){}

    static nodeTypeMap = new Map<string,any>;

    // 加载自定义节点
    static loadNodeLibrary(type: TypeToken): boolean{
        this.nodeTypeMap.set(type.typeName,type)
        return true
    }

    static buildTestNode(testGraph:TestGraph
        ,nodeType: TypeToken
        ,pos_x:number
        ,pos_y:number){
        const nodeName = testGraph.newNodeName(nodeType.typeName)
        testGraph.addNode(nodeType.build(nodeName,pos_x,pos_y))
    }

    static addTestNode(testGraph:TestGraph
        ,typeName:string
        ,pos_x:number
        ,pos_y:number){
        let nodeType = this.nodeTypeMap.get(typeName);
        if(nodeType != undefined){
            this.buildTestNode(testGraph,nodeType,pos_x,pos_y)
        }        
    }
}

// 实用类型工具
export class TypeTool {
    private constructor(){}

    static isParent(child:any,parent:any):boolean{
        let current=child;
        while(current){
            if(current===parent){
                return true;
            }
            current=current.__proto__;
        }
        return false;
    }
}

// 测试图工厂，负责创建测试图
export class TestGraphFactory {
    private constructor(){}

    // graphName 图名称
    static buildTestGraph(graphName:string): TestGraph{
        return new TestGraph(graphName)
    }
}


NodeFactory.loadNodeLibrary(BeginNode)