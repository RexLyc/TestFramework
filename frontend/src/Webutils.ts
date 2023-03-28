import axios from 'axios';

export class HttpUtil {
    private static sendPost(url:string,body:string,onResp:any,onError:any){
        console.log(url)
        return axios.post(url,{body:"?"}).then(onResp).catch(onError);
    }
    static runTestGraph(address:string,graphJson:string,onResp:any,onError:any){
        return this.sendPost(address+'/runTestGraph'
            , graphJson
            , onResp
            , onError);
    }
}

