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

