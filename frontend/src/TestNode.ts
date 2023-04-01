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

export class BaseParam {
    paramName: string;
    readonly paramType: ParamRuntimeTypeEnums;
    paramValue: string;
    paramRef: Array<string>
    readonly typeName:string;
    readonly categoryNames: Array<ParamCategoryEnums>;

    constructor(typeName: string
        ,categoryNames:Array<ParamCategoryEnums>
        ,paramName:string
        ,paramType:ParamRuntimeTypeEnums
        ,paramRef:Array<string>
        ,paramValue:string) {
        this.paramName=paramName;
        this.paramType=paramType;
        this.paramValue=paramValue;
        this.paramRef=paramRef;
        this.typeName=typeName;
        this.categoryNames=categoryNames;
    }

    toJSON():object{
        return {
            "typeName":this.typeName
            ,"paramName":this.paramName
            ,"paramType":this.paramType
            ,"paramRef":this.paramRef
            ,"paramValue":this.paramValue
        };
    }
}

export interface ParamBuilder {
    readonly typeName: string;
    readonly categoryNames: Array<ParamCategoryEnums>;
    build(paramName:string,paramType:ParamRuntimeTypeEnums,paramRef:Array<string>,paramValue:string):BaseParam;
}

// 参数值内容永远是string存储
// 其参数值类型（如何使用参数值），是其运行时类型
// 将用于提示连接两侧是否完全匹配，不匹配的情况下会进行类型转换，但不保证成功
export enum ParamRuntimeTypeEnums {
    // 参数值是变量名
    VarNameValue    = "VarNameValue",
    // 参数值是字面字符串
    StringValue     = "StringValue",
    // 参数值是整型字面值
    IntegerValue    = "IntegerValue",
    // 参数值是浮点字面值
    FloatValue      = "FloatValue",
    // 参数值是python脚本
    PythonValue     = "PythonValue",
    // 参数值是bool类型值
    BoolValue       = "BoolValue",
}

// 分组用于表明是否可以连接
export enum ParamCategoryEnums {
    All  = "group",
    Flow = "groupFlow",
    Data = "groupData",
}

export class FlowParam {
    static readonly typeName: string="FlowParam";
    static readonly categoryNames: Array<ParamCategoryEnums>=[ParamCategoryEnums.Flow];
    static build(paramName:string
        ,paramType:ParamRuntimeTypeEnums
        ,paramRef:Array<string>
        ,paramValue:string):BaseParam {
        return new BaseParam(FlowParam.typeName
            ,FlowParam.categoryNames
            ,paramName
            ,paramType
            ,paramRef
            ,paramValue);
    }
}

export class VariableParam {
    static readonly typeName: string="VariableParam";
    static readonly categoryNames: Array<ParamCategoryEnums>=[ParamCategoryEnums.Data];
    static build(paramName:string
        ,paramType:ParamRuntimeTypeEnums
        ,paramRef:Array<string>
        ,paramValue:string):BaseParam {
        return new BaseParam(VariableParam.typeName
            ,VariableParam.categoryNames
            ,paramName
            ,paramType
            ,paramRef
            ,paramValue);
    }
}

export class ConstantParam {
    static readonly typeName: string="ConstantParam";
    static readonly categoryNames: Array<ParamCategoryEnums>=[ParamCategoryEnums.Data];
    static build(paramName:string
        ,paramType:ParamRuntimeTypeEnums
        ,paramRef:Array<string>
        ,paramValue:string):BaseParam {
        return new BaseParam(ConstantParam.typeName
            ,ConstantParam.categoryNames
            ,paramName
            ,paramType
            ,paramRef
            ,paramValue);
    }
}

export class ParamLibrary {
    private constructor(){}

    static paramBuilderMap:Map<string,ParamBuilder> = new Map();

    static addParamBuilder(paramBuilder:ParamBuilder):boolean{
        if(this.paramBuilderMap.has(paramBuilder.typeName))
            return false;
        this.paramBuilderMap.set(paramBuilder.typeName,paramBuilder);
        return true;
    }
    
    static getBuilder(builderName:string):ParamBuilder|undefined{
        return this.paramBuilderMap.get(builderName);
    }
}

ParamLibrary.addParamBuilder(FlowParam);
ParamLibrary.addParamBuilder(VariableParam);
ParamLibrary.addParamBuilder(ConstantParam);

// 必须满足的InOut参数要求
export class InOutParams {
    params: Array<BaseParam>;
    paramNameIndexMap: Map<String,number>;
    constructor(){
        this.params=new Array();
        this.paramNameIndexMap=new Map();
    }

    addParam(paramBuilder:ParamBuilder | string
            ,paramName:string
            ,paramType:ParamRuntimeTypeEnums=ParamRuntimeTypeEnums.VarNameValue
            ,paramRef:Array<string>=[]
            ,paramValue:string=''): InOutParams {
        if(this.paramNameIndexMap.has(paramName))
            throw Error('param name duplicate');
        this.paramNameIndexMap.set(paramName,this.params.length);
        if(typeof paramBuilder ==='string') {

            this.params.push(ParamLibrary.getBuilder(paramBuilder)?.build(paramName,paramType,paramRef,paramValue)!);
        }
        else{
            this.params.push(paramBuilder.build(paramName,paramType,paramRef,paramValue));
        }
        return this;
    }

    removeParam(paramName:string){
        const index = this.paramNameIndexMap.get(paramName);
        if(index!=undefined){
            this.paramNameIndexMap.delete(paramName);
            this.params.splice(index,1);
        }
    }

    pop(){
        if(this.params.length>0){
            const paramName = this.params[this.params.length-1].paramName;
            this.removeParam(paramName);
        }
    }

    toJSON():object{
        // 去掉不必要的内容
        return {"params":this.params};
    }

    static fromJSON(jsonObject:any): InOutParams{
        const inOutParams = new InOutParams();
        for(let p of jsonObject.params) {
            inOutParams.addParam(p.typeName,p.paramName,p.paramType,p.paramRef,p.paramValue);
        }
        return inOutParams;
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
        this.nameNodeMap.get(fromNode)?.outputs.params[fromParam].paramRef!.push(toNode + '$' + toParam);
        this.nameNodeMap.get(toNode)?.inputs.params[toParam].paramRef!.push(fromNode + '$' + fromParam);
    }

    removeConnection(fromNode:string,fromParam:number,toNode:string,toParam:number){
        // 查找在output中该记录位置
        const fromIndex = this.nameNodeMap.get(fromNode)?.outputs.params[fromParam].paramRef!.indexOf(toNode +'$'+toParam);
        this.nameNodeMap.get(fromNode)!.outputs.params[fromParam].paramRef!.splice(fromIndex!,1);
        // 查找在input中该记录位置
        const toIndex = this.nameNodeMap.get(toNode)?.inputs.params[toParam].paramRef!.indexOf(fromNode + '$' + fromParam);
        this.nameNodeMap.get(toNode)!.inputs.params[toParam].paramRef!.splice(toIndex!,1);
    }

    toJSON():object{
        return {
            "graphName":this.graphName,
            "nameCountMap":Array.from(this.nameCountMap),
            "nameNodeMap":Array.from(this.nameNodeMap)
        };
    }

    static fromJSON(jsonObject:any):TestGraph{
        const graph = new TestGraph(jsonObject.graphName);
        graph.nameCountMap=new Map(jsonObject.nameCountMap);
        const tempNameNodeMap = new Map(jsonObject.nameNodeMap);
        for(let node of tempNameNodeMap.entries()){
            graph.nameNodeMap.set(node[0] as string,BaseNode.fromJSON(node[1]));
        }
        return graph;
    }
}

export class BaseNode {
    // for render
    // 内部唯一名(id)
    public name;
    // 输入参数
    public inputs;
    // 输出参数
    public outputs;
    // 坐标位置
    public pos_x;
    public pos_y;
    // 节点类类型名称
    public typeName;
    // 保留数据（暂未使用）
    public data;
    // 展示名称
    public html;
    // for test graph


    constructor(name: string
        ,inputs:InOutParams
        ,outputs:InOutParams
        ,pos_x:number
        ,pos_y:number
        ,typeName:string
        ,data:object
        ,html:string){
        this.name = name
        this.inputs=inputs
        this.outputs=outputs
        this.pos_x=pos_x;
        this.pos_y=pos_y;
        this.typeName=typeName;
        this.data=data;
        this.html=html;
    }

    static fromJSON(jsonObject:any):BaseNode{
        return new BaseNode(jsonObject.name
            ,InOutParams.fromJSON(jsonObject.inputs)
            ,InOutParams.fromJSON(jsonObject.outputs)
            ,jsonObject.pos_x
            ,jsonObject.pos_y
            ,jsonObject.typeName
            ,jsonObject.data
            ,jsonObject.html);
    }
}


// ====================== Node类型体系 ====================== 
// 这种特殊写法是为了检查categoryName/typeName/build作为静态成员
export interface NodeBuilder {
    readonly categoryName: string;
    readonly typeName: string;
    build(nodeName:string, pos_x:number, pos_y:number): BaseNode;
}

export enum CategoryEnums {
    CommonType = "CommonType",          // 通用节点
    WebType = "WebType",                // 网络测试节点
    SerialType = "SerialType",          // 串口测试节点
    FlowType = "FlowType",              // 流程控制节点
    CalculateType = "CalculateType",              // 数理运算节点
}


// 常量
export class ConstantNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "ConstantNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const outputs = new InOutParams();
        outputs.addParam(ConstantParam,"data",ParamRuntimeTypeEnums.StringValue);
        const temp = new BaseNode(nodeName
            ,new InOutParams()
            ,outputs
            ,pos_x
            ,pos_y
            ,ConstantNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}


// 变量
export class VariableNode {
    static categoryName = CategoryEnums.CommonType;
    static typeName = "VariableNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(VariableParam,"updateData",ParamRuntimeTypeEnums.VarNameValue);
        const outputs = new InOutParams();
        outputs.addParam(ConstantParam,"initData",ParamRuntimeTypeEnums.StringValue);
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
            ,pos_x
            ,pos_y
            ,VariableNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 测试起点
export class BeginNode {
    static categoryName = CategoryEnums.FlowType;
    static typeName = "BeginNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next");
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
    static categoryName = CategoryEnums.FlowType;
    static typeName = "EndNode";
    static build(nodeName:string, pos_x:number,pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(FlowParam,"prev");
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
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"data");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next");
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
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
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"data")
            .addParam(VariableParam,"begin")
            .addParam(VariableParam,"end");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"data");
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
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"data_1")
            .addParam(VariableParam,"data_2");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"data");
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
        inputs.addParam(VariableParam,"data");
        const outputs = new InOutParams();
        outputs.addParam(VariableParam,"data");
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
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"file")
            .addParam(VariableParam,"data")
            .addParam(VariableParam,"timeout");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"data");
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
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"file")
            .addParam(VariableParam,"timeout");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"data");
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
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"url")
            .addParam(VariableParam,"method");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"httpFile");
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
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"addr")
            .addParam(VariableParam,"port");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"tcpFile");
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
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"addr");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"udpFile");
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
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"url");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"wsFile");
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

// 串口连接创建
export class SerialNode {
    static categoryName = CategoryEnums.SerialType;
    static typeName = "SerialNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"baudrate")
            .addParam(VariableParam,"port");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"serialFile");
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
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"condition");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"trueNext")
            .addParam(FlowParam,"falseNext");
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
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"data");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"defaultNext");
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

// 加减法：1 + 2 - 3，默认值 0
export class AddMinusNode {
    static categoryName = CategoryEnums.CalculateType;
    static typeName = "AddMinusNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"data_plus")
            .addParam(VariableParam,"data_minus");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"data");
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
            ,pos_x
            ,pos_y
            ,AddMinusNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 乘除法： 1 * 2 / 3，默认值 1
export class MultiDivNode {
    static categoryName = CategoryEnums.CalculateType;
    static typeName = "MultiDivNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"data_mul")
            .addParam(VariableParam,"data_div");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"data");
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
            ,pos_x
            ,pos_y
            ,MultiDivNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 是否大于的判断
export class BiggerNode {
    static categoryName = CategoryEnums.CalculateType;
    static typeName = "BiggerNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"data_1")
            .addParam(VariableParam,"data_2");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"condition");
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
            ,pos_x
            ,pos_y
            ,BiggerNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 是否相等的判断
export class EqualNode {
    static categoryName = CategoryEnums.CalculateType;
    static typeName = "EqualNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"data_1")
            .addParam(VariableParam,"data_2");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"condition");
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
            ,pos_x
            ,pos_y
            ,EqualNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 逻辑与
export class AndNode {
    static categoryName = CategoryEnums.CalculateType;
    static typeName = "AndNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"condition_1")
            .addParam(VariableParam,"condition_2");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"condition");
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
            ,pos_x
            ,pos_y
            ,AndNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 逻辑或
export class OrNode {
    static categoryName = CategoryEnums.CalculateType;
    static typeName = "OrNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"condition_1")
            .addParam(VariableParam,"condition_2");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"condition");
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
            ,pos_x
            ,pos_y
            ,OrNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 逻辑非
export class NotNode {
    static categoryName = CategoryEnums.CalculateType;
    static typeName = "NotNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(FlowParam,"prev")
            .addParam(VariableParam,"condition");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next")
            .addParam(VariableParam,"condition");
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
            ,pos_x
            ,pos_y
            ,NotNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// 栅栏节点，用于等待所有prev
export class BarrierNode {
    static categoryName = CategoryEnums.FlowType;
    static typeName = "BarrierNode";
    static build(nodeName:string, pos_x:number, pos_y:number):BaseNode {
        const inputs = new InOutParams();
        inputs.addParam(FlowParam,"prev");
        const outputs = new InOutParams();
        outputs.addParam(FlowParam,"next");
        const temp = new BaseNode(nodeName
            ,inputs
            ,outputs
            ,pos_x
            ,pos_y
            ,BarrierNode.typeName
            ,{}
            ,nodeName);
        return temp;
    }
}

// ====================== 实用工具 ====================== 
// 默认翻译
export const basicNodeTranslate:Map<string,string> = new Map();
// 翻译器
export class NodeTranslator {
    static lib:Map<string,string> = basicNodeTranslate;

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

export const basicParamTranslator:Map<string,string> = new Map();
basicParamTranslator.set(ParamRuntimeTypeEnums.VarNameValue,'引用变量');
basicParamTranslator.set(ParamRuntimeTypeEnums.StringValue,'字符串字面值');
basicParamTranslator.set(ParamRuntimeTypeEnums.IntegerValue,'整型数字面值');
basicParamTranslator.set(ParamRuntimeTypeEnums.FloatValue,'浮点数字面值');
basicParamTranslator.set(ParamRuntimeTypeEnums.PythonValue,'Python脚本')
basicParamTranslator.set(ParamRuntimeTypeEnums.BoolValue,'逻辑真值Bool')


export class ParamTranslator {
    static lib:Map<string,string> = basicParamTranslator;
    static loadTransLib(lib:Map<string,string>){
        this.lib=lib;
    }

    static translate(english:string):string{
        if(this.lib.get(english)==undefined){
            return english;
        } else {
            return this.lib.get(english)!;
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

    static nodeTypeMap = new Map<string,NodeBuilder>;

    // 加载自定义节点
    static loadNodeLibrary(type: NodeBuilder): boolean{
        this.nodeTypeMap.set(type.typeName,type)
        return true
    }

    private static buildTestNode(testGraph:TestGraph
        ,nodeType: NodeBuilder
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
        return this.testGraphMap.get(graphName)!;
    }

    // graphName 图名称
    static buildTestGraph(graphName:string): TestGraph{
        this.testGraphMap.set(graphName,new TestGraph(graphName))
        return this.testGraphMap.get(graphName)!;
    }

    static removeTestGraph(graphName:string){
        this.testGraphMap.delete(graphName);
    }

    
    static exportGraph(graphName:string):string{
        // 输入图名，输出json
        return ImportExportProtocol.exportGraph(this.testGraphMap.get(graphName)!);
    }

    static addTestGraph(graph:TestGraph):boolean{
        if(this.testGraphMap.has(graph.graphName))
            return false;
        this.testGraphMap.set(graph.graphName,graph);
        return true;
    }

    static importGraph(graphJson:string):TestGraph | null{
        // 输入json，输出图名
        try {
            return ImportExportProtocol.importGraph(graphJson);
        } catch (error) {
            console.log(error);
            return null;
        }
    }

    static exportNode(graphName:string,nodeName:string):string{
        return ImportExportProtocol.exportNode(this.testGraphMap.get(graphName)!,nodeName);
    }
}

export class ImportExportProtocol {
    /*
        {
            "meta":
            {
                "version:"0.1"
            },
            "graph":
            {
                ...
            }
        }
    */
    static version:number=1;
    static importGraph(graphJson:string):TestGraph{
        const jsonObject = JSON.parse(graphJson);
        if(jsonObject.meta.version > this.version){
            throw Error("incompable data version");
        }
        return TestGraph.fromJSON(jsonObject.graph);
    }

    static exportGraph(graph:TestGraph):string{
        return JSON.stringify({"meta":{"version":this.version},"graph":graph},null,4);
    }

    static exportNode(graph:TestGraph,nodeName:string):string{
        return JSON.stringify(graph.nameNodeMap.get(nodeName),null,4);
    }
}


// ====================== 加载时执行 ====================== 
basicNodeTranslate.set("CommonType","通用节点");
basicNodeTranslate.set("WebType","网络测试节点");
basicNodeTranslate.set("SerialType","串口测试节点");
basicNodeTranslate.set("FlowType","流程控制节点");
basicNodeTranslate.set("CalculateType","数理逻辑运算节点");

basicNodeTranslate.set("BeginNode","测试起始节点");
basicNodeTranslate.set("EndNode","测试终止节点");
basicNodeTranslate.set("LogNode","日志节点");
basicNodeTranslate.set("ExtractNode","数据提取节点");
basicNodeTranslate.set("MergeNode","数据合并节点");

basicNodeTranslate.set("GlobalNode","全局配置节点");
basicNodeTranslate.set("SendNode","数据发送节点");
basicNodeTranslate.set("RecvNode","数据接收节点");
basicNodeTranslate.set("HttpNode","HTTP连接节点");
basicNodeTranslate.set("TCPNode","TCP连接节点");
basicNodeTranslate.set("UDPNode","UDP准备节点");
basicNodeTranslate.set("WebSocketNode","WebSocket连接节点");
basicNodeTranslate.set("SerialNode","串口连接节点");
basicNodeTranslate.set("IfNode","条件跳转节点");
basicNodeTranslate.set("SwitchNode","Switch跳转节点");
basicNodeTranslate.set("ConstantNode","常量节点");
basicNodeTranslate.set("VariableNode","变量节点");

// 运算节点
basicNodeTranslate.set("AddMinusNode","加减法节点");
basicNodeTranslate.set("MultiDivNode","乘除法节点");
basicNodeTranslate.set("BiggerNode","大于节点");
basicNodeTranslate.set("EqualNode","等于节点");
basicNodeTranslate.set("AndNode","逻辑与节点");
basicNodeTranslate.set("OrNode","逻辑或节点");
basicNodeTranslate.set("NotNode","逻辑非节点");

// 其他流程控制
basicNodeTranslate.set("BarrierNode","栅栏节点")


NodeFactory.loadNodeLibrary(BeginNode);
NodeFactory.loadNodeLibrary(EndNode);
NodeFactory.loadNodeLibrary(LogNode);
NodeFactory.loadNodeLibrary(ExtractNode);
NodeFactory.loadNodeLibrary(MergeNode);
// 暂时废弃
// NodeFactory.loadNodeLibrary(GlobalNode)
NodeFactory.loadNodeLibrary(SendNode);
NodeFactory.loadNodeLibrary(RecvNode);
NodeFactory.loadNodeLibrary(HttpNode);
NodeFactory.loadNodeLibrary(TCPNode);
// 暂不实装
// NodeFactory.loadNodeLibrary(UDPNode)
NodeFactory.loadNodeLibrary(WebSocketNode);
NodeFactory.loadNodeLibrary(SerialNode);
NodeFactory.loadNodeLibrary(IfNode);
NodeFactory.loadNodeLibrary(SwitchNode);
NodeFactory.loadNodeLibrary(ConstantNode);
NodeFactory.loadNodeLibrary(AddMinusNode)
NodeFactory.loadNodeLibrary(MultiDivNode);
NodeFactory.loadNodeLibrary(BiggerNode);
NodeFactory.loadNodeLibrary(EqualNode);
NodeFactory.loadNodeLibrary(AndNode);
NodeFactory.loadNodeLibrary(OrNode);
NodeFactory.loadNodeLibrary(NotNode);
NodeFactory.loadNodeLibrary(BarrierNode);

NodeFactory.loadNodeLibrary(VariableNode);