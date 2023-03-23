// 编写全部和测试节点相关的内容

// ====================== 事件相关数据结构 ====================== 
export interface TGAddNewNode {
    testGraph:string,
    nodeName:string,
}


// ====================== 节点参数相关数据结构 ====================== 
// 类类型
export interface Type<T = any> extends Function {
    new (...args: any[]):T;
}

// 允许自定义新的Param种类
export interface ParamInterface {
    readonly paramName: string;
    readonly paramType: Type;
    paramValue: Array<any>;
    // 分组可以默认
    paramCategory: Array<ParamCategoryEnums>;
}

export class NextParam implements ParamInterface{
    paramName: string;
    paramType: Type;
    paramValue: Array<any>;
    paramCategory: Array<ParamCategoryEnums>;
    constructor(value:Array<InstanceType<Type>>){
        this.paramName='next';
        this.paramType=String;
        this.paramValue=value;
        this.paramCategory=[ParamCategoryEnums.Flow];
    }
}

export enum ParamCategoryEnums {
    All  = "group",
    Flow = "groupFlow",
    Data = "groupData",
}

export class PrevParam implements ParamInterface{
    paramName: string;
    paramType: Type;
    paramValue: Array<any>;
    paramCategory: Array<ParamCategoryEnums>;
    constructor(value:Array<InstanceType<Type>>){
        this.paramName='prev';
        this.paramType=String;
        this.paramValue=value;
        this.paramCategory=[ParamCategoryEnums.Flow];
    }
}

export class Param implements ParamInterface{
    paramName: string;
    paramType: Type;
    paramValue: Array<Type>;
    paramCategory: Array<ParamCategoryEnums>;
    constructor(name:string,type:Type,value:Array<InstanceType<Type>>){
        this.paramName=name;
        this.paramType=type;
        this.paramValue=value;
        this.paramCategory=[ParamCategoryEnums.Data];
    }
}

// 必须满足的InOut参数要求
export interface InOutParamsInterface {
    params: Array<ParamInterface>;
}

export class InOutParams {
    params: Array<ParamInterface>;
    paramNameSet: Set<String>;
    constructor(){
        this.params=new Array();
        this.paramNameSet=new Set();
    }
    addParam(param:ParamInterface):InOutParams{
        if(this.paramNameSet.has(param.paramName))    
            throw Error('param name duplicate');
        this.paramNameSet.add(param.paramName);
        this.params.push(param);
        return this;
    }
}

// ====================== 图和节点相关数据结构 ====================== 
// 测试图对象，管理所有测试节点
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
        this.nameNodeMap.set(node.name,node);
    }

    removeNode(nodeName:string){
        this.nameNodeMap.delete(nodeName);
    }

    addConnection(fromNode:string,fromParam:number,toNode:string,toParam:number){
        // 名字 + 参数在参数列表中的序号
        this.nameNodeMap.get(fromNode)?.outputs.params[fromParam].paramValue.push(toNode + ' ' + toParam);
        this.nameNodeMap.get(toNode)?.inputs.params[toParam].paramValue.push(fromNode + ' ' + fromParam);
    }

    removeConnection(fromNode:string,fromParam:number,toNode:string,toParam:number){
        // 查找该记录位置

        // this.nameNodeMap.get(fromNode)?.outputs.params[fromParam].paramValue
        //     = this.nameNodeMap.get(fromNode)?.outputs.params[fromParam].paramValue.splice()
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
        ,inputs:InOutParamsInterface
        ,outputs:InOutParamsInterface
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


// ====================== Node类型体系 ====================== 
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
    FlowType = "FlowType",              // 流程控制节点
    MathType = "MathType",              // 数理运算节点
}


// 常量
export class ConstantNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "ConstantNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const outputs = new InOutParams();
        outputs.addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,new InOutParams()
            ,outputs
            ,pos_x
            ,pos_y
            ,BeginNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 测试起点
export class BeginNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "BeginNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]));
        const temp = new BaseNode(nodeName
            ,new InOutParams()
            ,outputs
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
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,new InOutParams()
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
        const inputs = new InOutParams();
        inputs.addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,new InOutParams()
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
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]))
            .addParam(new Param("data",String,[""]))
            .addParam(new Param("begin",Number,[0]))
            .addParam(new Param("end",Number,[0]));
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]))
            .addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
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
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]))
            .addParam(new Param("data_1",String,[""]))
            .addParam(new Param("data_2",String,[""]));
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]))
            .addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
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
        const inputs = new InOutParams();
        inputs.addParam(new Param("data",String,[""]));
        const outputs = new InOutParams();
        outputs.addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
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
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]))
            .addParam(new Param("file",String,[""])) 
            .addParam(new Param("data",String,[""]))
            .addParam(new Param("timeout",Number,[5000]));
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]))
            .addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
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
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]))
            .addParam(new Param("file",String,[""])) 
            .addParam(new Param("data",String,[""]))
            .addParam(new Param("timeout",Number,[5000]));
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]))
            .addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
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
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]))
            .addParam(new Param("data",String,[""]));
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]))
            .addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
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
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]))
            .addParam(new Param("data",String,[""]));
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]))
            .addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
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
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]))
            .addParam(new Param("data",String,[""]));
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]))
            .addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
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
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]))
            .addParam(new Param("data",String,[""]));
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]))
            .addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
            ,pos_x
            ,pos_y
            ,WebSocketNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

export interface SerialOptionType {
    baudrate:number,
    port:string
}

// 串口连接创建
export class SerialNode {
    static categoryName = CategoryEnums.SerialType;
    static typeName = "SerialNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]))
            .addParam(new Param("baudrate",Number,[9000]))
            .addParam(new Param("port",String,["COM0"]));
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]))
            .addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
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
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]))
            .addParam(new Param("data",String,[""]));
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]))
            .addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
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
        const inputs = new InOutParams();
        inputs.addParam(new PrevParam([""]))
            .addParam(new Param("data",String,[""]));
        const outputs = new InOutParams();
        outputs.addParam(new NextParam([""]))
            .addParam(new Param("data",String,[""]));
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
            ,pos_x
            ,pos_y
            ,SwitchNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}



// ====================== 实用工具 ====================== 
// 默认翻译
export const basicTranslate:Map<string,string> = new Map();
// 翻译器
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
        const newNodeEvent = new CustomEvent('TGAddNewNode',{'detail': {
            testGraph:testGraph.graphName,
            nodeName:nodeName,
        }});
        dispatchEvent(newNodeEvent);
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

// 测试图工厂，负责创建测试图
export class TestGraphFactory {
    private constructor(){}
    static testGraphMap:Map<string,TestGraph>=new Map();
    static getTestGraph(graphName:string): TestGraph {
        return this.testGraphMap.get(graphName);
    }

    // graphName 图名称
    static buildTestGraph(graphName:string): TestGraph{
        this.testGraphMap.set(graphName,new TestGraph(graphName))
        return this.testGraphMap.get(graphName)!;
    }

    static removeTestGraph(graphName:string){
        this.testGraphMap.delete(graphName);
    }
}


// ====================== 加载时执行 ====================== 
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
basicTranslate.set("ConstantNode","常量节点");
basicTranslate.set("AddMinusNode","加减法节点");
basicTranslate.set("MultiDivNode","乘除法节点");
basicTranslate.set("AddNode","加法节点");

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
NodeFactory.loadNodeLibrary(ConstantNode);