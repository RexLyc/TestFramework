import axios from 'axios';
export class HttpUtil {
    private static sendPost(url:string,body:any,onResp:any,onError:any){
        return axios.post(import.meta.env.VITE_APP_BASE+url,JSON.stringify(body)).then(onResp).catch(onError);
    }
    // static runTestGraph(address:string,graphJson:string,onResp:any,onError:any){
    //     return this.sendPost(address+'/runTestGraph'
    //         , graphJson
    //         , onResp
    //         , onError);
    // }
    // static linkTest(address:string,graphJson:string,onResp:any,onError:any){
    //     return this.sendPost(address+'/linkTest'
    //         , graphJson
    //         , onResp
    //         , onError);
    // }
    static getSave(body:any,onResp:any,onError:any){
        return this.sendPost('/serverSave',body,onResp,onError)
    }

    static getSaveTypeCategory(onResp:any,onError:any){
        return this.sendPost('/saveCategory',{},onResp,onError);
    }

    static uploadSave(body:any,onResp:any,onError:any){
        return this.sendPost('/uploadSave',body,onResp,onError);
    }

    static deleteSave(body:any,onResp:any,onError:any){
        return this.sendPost('/deleteSave',body,onResp,onError);
    }
}

import { io,Manager } from "socket.io-client";

export enum CommonMessageType {
    // 测试图提交测试
    SUBMIT           = "submit",
    // 心跳
    PING             = "ping",
    // 测试执行结果
    TEST_RESULT      = "test_result",
    // 测试执行状态
    TEST_STATE       = "test_state",
    // 测试控制
    TEST_COMMAND     = "test_command",
}

export enum TestCommandType {
    // 杀死当前测试
    KILL        = "kill",
    // 暂停当前测试
    PAUSE       = "pause",
    // 继续当前测试
    CONTINUE    = "continue",
    // 步进
    STEP        = "step",
}

export class TestCommand {
    testUUID        :string;
    command     :TestCommandType;
    constructor(testUUID:string,command:TestCommandType){
        this.testUUID=testUUID;
        this.command=command
    }
}
  
export class CommonMessage {
    // 时间戳
    msgTime      :number;
    // 消息类型
    msgType      :CommonMessageType;
    msgData      :any;
    constructor(type:CommonMessageType,data:any){
        this.msgTime=Date.now()
        this.msgType=type;
        this.msgData=data;
    }
}

// 提交状态
export enum SubmitResultType{
    SUCCESS      = 0,
    INCOMPATIBLE = 1,
    EXCEPTION    = 2,
}

// 测试结束状态
export enum ExitStateEnum {
    // # 正常结束
    SUCCESS     = 0,
    // # 整体超时
    TIMEOUT     = 1,
    // # 测试异常
    TESTERROR   = 2,
    // # 其他异常
    EXCEPTION   = 3,
    // # 被杀死
    KILLED      = 4,
    // # 断言未通过
    ASSERTERROR = 5,
    // # 无效
    INVALID     = 6,
}

export class SocketIOUtil {
    private static ioMap:Map<string,any> = new Map()
    static open(url:string,onOpen:any,onClose:any,onError:any,onMessages:Map<string,any>){
        if(this.ioMap.has(url)&&this.ioMap.get(url)?.readyState==WebSocket.OPEN){
            // 提示该url已被占用，不能创建
            return false;
        }
        // 创建新的
        if(this.ioMap.has(url)){
            this.ioMap.get(url)?.close();
        }
        // const manager = new Manager("ws://"+url);
        // const tempWS = manager.socket("/websocket");
        const tempWS = io("ws://"+url+"/websocket",{reconnection:false})
        tempWS.on("connect",onOpen);
        tempWS.on("disconnect",onClose);
        tempWS.on("error",onError);
        for(let listener of onMessages){
            tempWS.on(listener[0],listener[1])
        }
        this.ioMap.set(url,tempWS);
        return true
    }

    static send(url:string,message:CommonMessage){
        if(!this.ioMap.has(url)){
            return false;
        }
        console.log('%o',message)
        this.ioMap.get(url).emit(message.msgType,message)
        return true;
    }

    static close(url:string){
        if(this.ioMap.has(url)){
            this.ioMap.get(url)?.close();
            this.ioMap.delete(url);
        }
    }
}