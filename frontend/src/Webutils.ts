import axios from 'axios';

export class HttpUtil {
    private static sendPost(url:string,body:string,onResp:any,onError:any){
        return axios.post("http://"+url,body).then(onResp).catch(onError);
    }
    static runTestGraph(address:string,graphJson:string,onResp:any,onError:any){
        return this.sendPost(address+'/runTestGraph'
            , graphJson
            , onResp
            , onError);
    }
    static linkTest(address:string,graphJson:string,onResp:any,onError:any){
        return this.sendPost(address+'/linkTest'
            , graphJson
            , onResp
            , onError);
    }
}

import { io,Manager } from "socket.io-client";

export enum CommonMessageType {
    // 测试图提交测试
    SUBMIT           = "submit",
    // 心跳
    PING             = "ping",
    // 测试执行结果
    TEST_RESULT      = "result",
    // 测试执行状态
    TEST_STATE       = "test_state",
}
  
export class CommonMessage {
    // 时间戳
    msgTime      :number;
    // 消息类型
    msgType      :CommonMessageType;
    msgData      :object;
    constructor(type:CommonMessageType,data:object){
        this.msgTime=Date.now()
        this.msgType=type;
        this.msgData=data;
    }
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