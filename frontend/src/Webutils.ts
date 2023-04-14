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

export class SocketIOUtil {
    private static ioMap:Map<string,any> = new Map()
    static open(url:string,onOpen:any,onClose:any,onMessage:any,onError:any){
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
        tempWS.on("response",onMessage);
        tempWS.on("error",onError);
        tempWS.emit("message","hello world");
        this.ioMap.set(url,tempWS);
        return true
    }

    static close(url:string){
        if(this.ioMap.has(url)){
            this.ioMap.get(url)?.close();
            this.ioMap.delete(url);
        }
    }
}