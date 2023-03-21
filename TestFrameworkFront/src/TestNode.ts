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

export interface InputInterface {
    name: String;
    value?: String;
}

export interface OutputInterface {
    name: String;
    value?: String;
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
        ,inputs:Array<InputInterface>
        ,outputs:Array<OutputInterface>
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
// 这种特殊写法是为了检查categoryName/typeName/build作为静态成员
export interface TypeToken {
    readonly categoryName: string;
    readonly typeName: string;
    build(nodeName:string, pos_x:number, pos_y:number): BaseNode
}

export enum CategoryEnums {
    CommonType = "CommonType",          // 通用节点
    WebType = "WebType",                // 网络测试节点
    SerialType = "SerialType",          // 串口测试节点
    FlowType = "FlowType"               // 流程控制节点
}

export const basicTranslate:Map<string,string> = new Map();
basicTranslate.set("CommonType","通用节点");
basicTranslate.set("WebType","网络测试节点");
basicTranslate.set("SerialType","串口测试节点");
basicTranslate.set("FlowType","流程控制节点");

basicTranslate.set("BeginNode","测试起始节点");
basicTranslate.set("EndNode","测试终止节点");
basicTranslate.set("LogNode","日志节点");
basicTranslate.set("ExtractNode","数据提取节点");
basicTranslate.set("MergeNode","数据合并节点");
basicTranslate.set("GlobalNode","全局配置节点");
basicTranslate.set("SendNode","数据发送节点");
basicTranslate.set("RecvNode","数据接收节点");
basicTranslate.set("HttpNode","HTTP连接节点");
basicTranslate.set("TCPNode","TCP连接节点");
basicTranslate.set("UDPNode","UDP准备节点");
basicTranslate.set("WebSocketNode","WebSocket连接节点");
basicTranslate.set("SerialNode","串口连接节点");
basicTranslate.set("IfNode","条件跳转节点");
basicTranslate.set("SwitchNode","Switch跳转节点");


export class NodeTranslator {
    static lib:Map<string,string> = basicTranslate;

    static loadTransLib(lib:Map<string,string>){
        this.lib=lib;
    }
    static translate(english:string):string{
        if(NodeTranslator.lib.get(english)==undefined){
            return english;
        } else {
            return NodeTranslator.lib.get(english)!;
        }
    }
}

// 测试起点
export class BeginNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "BeginNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[]
            ,[{name:"next"}]
            ,pos_x
            ,pos_y
            ,BeginNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 测试终点
export class EndNode{
    static categoryName = CategoryEnums.CommonType;
    static typeName = "EndNode";
    static build(nodeName:string, pos_x:number,pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"}]
            ,[]
            ,pos_x
            ,pos_y
            ,EndNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 日志节点
export class LogNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "LogNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"data"}]
            ,[]
            ,pos_x
            ,pos_y
            ,LogNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 数据提取节点
export class ExtractNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "ExtractNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"},{name:"data"},{name:"begin"},{name:"end"}]
            ,[{name:"next"},{name:"data"}]
            ,pos_x
            ,pos_y
            ,ExtractNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 数据合并节点
export class MergeNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "MergeNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"},{name:"data_1"},{name:"data_2"}]
            ,[{name:"next"},{name:"data"}]
            ,pos_x
            ,pos_y
            ,MergeNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 全局配置
export class GlobalNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "GlobalNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[]
            ,[]
            ,pos_x
            ,pos_y
            ,GlobalNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 数据发送
export class SendNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "SendNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"},{name:"data"}]
            ,[{name:"next"},{name:"data"}]
            ,pos_x
            ,pos_y
            ,SendNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 数据接收
export class RecvNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "RecvNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"},{name:"data"}]
            ,[{name:"next"},{name:"data"}]
            ,pos_x
            ,pos_y
            ,RecvNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// HTTP连接创建
export class HttpNode {
    static categoryName = CategoryEnums.WebType;
    static typeName = "HttpNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"},{name:"data"}]
            ,[{name:"next"},{name:"data"}]
            ,pos_x
            ,pos_y
            ,HttpNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// TCP连接创建
export class TCPNode {
    static categoryName = CategoryEnums.WebType;
    static typeName = "TCPNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"},{name:"data"}]
            ,[{name:"next"},{name:"data"}]
            ,pos_x
            ,pos_y
            ,TCPNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// UDP发送准备
export class UDPNode {
    static categoryName = CategoryEnums.WebType;
    static typeName = "UDPNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"},{name:"data"}]
            ,[{name:"next"},{name:"data"}]
            ,pos_x
            ,pos_y
            ,UDPNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// WebSocket连接创建
export class WebSocketNode {
    static categoryName = CategoryEnums.WebType;
    static typeName = "WebSocketNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"},{name:"data"}]
            ,[{name:"next"},{name:"data"}]
            ,pos_x
            ,pos_y
            ,WebSocketNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 串口连接创建
export class SerialNode {
    static categoryName = CategoryEnums.SerialType;
    static typeName = "SerialNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"},{name:"data"}]
            ,[{name:"next"},{name:"data"}]
            ,pos_x
            ,pos_y
            ,SerialNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 判断和跳转
export class IfNode {
    static categoryName = CategoryEnums.FlowType;
    static typeName = "IfNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"},{name:"data"}]
            ,[{name:"next"},{name:"data"}]
            ,pos_x
            ,pos_y
            ,IfNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// Switch
export class SwitchNode {
    static categoryName = CategoryEnums.FlowType;
    static typeName = "SwitchNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const temp = new BaseNode(nodeName
            ,[{name:"prev"},{name:"data"}]
            ,[{name:"next"},{name:"data"}]
            ,pos_x
            ,pos_y
            ,SwitchNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 测试节点工厂，负责存储节点类型，创建节点实例
export class NodeFactory {
    private constructor(){}

    static nodeTypeMap = new Map<string,TypeToken>;

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
        } else {
            console.log('unknown nodetype: %o',typeName);
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
NodeFactory.loadNodeLibrary(EndNode)
NodeFactory.loadNodeLibrary(LogNode)
NodeFactory.loadNodeLibrary(ExtractNode)
NodeFactory.loadNodeLibrary(MergeNode)
NodeFactory.loadNodeLibrary(GlobalNode)
NodeFactory.loadNodeLibrary(SendNode)
NodeFactory.loadNodeLibrary(RecvNode)
NodeFactory.loadNodeLibrary(HttpNode)
NodeFactory.loadNodeLibrary(TCPNode)
NodeFactory.loadNodeLibrary(UDPNode)
NodeFactory.loadNodeLibrary(WebSocketNode)
NodeFactory.loadNodeLibrary(SerialNode)
NodeFactory.loadNodeLibrary(IfNode)
NodeFactory.loadNodeLibrary(SwitchNode)