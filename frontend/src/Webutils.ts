import axios from 'axios';

export class HttpUtil {
    private static sendPost(url:string,body:string,onResp:any,onError:any){
        return axios.post(url,body).then(onResp).catch(onError);
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

export class WebSocketUtil {
    private static wsMap:Map<string,WebSocket> = new Map()
    static open(url:string,onOpen:any,onClose:any,onMessage:any,onError:any){
        if(this.wsMap.has(url)&&this.wsMap.get(url)?.readyState==WebSocket.OPEN){
            // 提示该url已被占用，不能创建
            return false;
        }
        // 创建新的
        if(this.wsMap.has(url)){
            this.wsMap.get(url)?.close();
        }
        const tempWS=new WebSocket(url);
        tempWS.onopen = onOpen;
        tempWS.onclose=onClose;
        tempWS.onmessage=onMessage;
        tempWS.onerror=onError;
        this.wsMap.set(url,tempWS);
        return true
    }

    static close(url:string){
        if(this.wsMap.has(url)){
            this.wsMap.get(url)?.close();
            this.wsMap.delete(url);
        }
    }
}