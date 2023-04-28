// 导入模块
const { app, BrowserWindow, utilityProcess } = require("electron")
const path  = require("path");
const treeKill = require("tree-kill");
// // 从 python-shell 导入一个 PythonShell 对象 (注意大小写)
// const {PythonShell}  = require("python-shell")
// // Declaring tree-kill
const kill = require('tree-kill');
const psTree = require('ps-tree');

// 创建窗口
function createWindow() {
    let win = new BrowserWindow({
        // 设置一个宽为800, 高为600的窗口
        width: 800,
        height: 600,
        icon: path.join(__dirname,'/logo.png')
    })
    
    
    // PythonShell.run("./dep/backend/server.py", {mode:'text'})
    // 加载本地的 index.html
    win.loadFile("./dep/frontend/index.html");
    win.setMenuBarVisibility(false)


}

// 启动后端（废弃，PythonShell处理依赖困难）
// const pyShell = new PythonShell("./dep/backend/server.py",{mode:'text',args:["no-reloader",'no-debug']});
// pyShell.end((err,exitCode,exitSignal)=>{
//     console.log('py server close ',err,exitCode,exitSignal)
// })

serverPath = ''
if(process.platform == 'win32'){
    serverPath=path.join(__dirname,'/dep/backend/server.exe')
}
else if(process.platform == 'linux'){
    serverPath=path.join(__dirname,'/dep/backend/server')
}

const pyProcess = require('child_process').execFile(serverPath,['no-reloader','no-debug'],{cwd:process.cwd(),windowsHide:true})
pyProcess.on('spawn',()=>{
    console.log('spawn one: ',pyProcess.pid)
})
pyProcess.on('exit',()=>{
    console.log('server exit: ',pyProcess.pid)
})

// 启动
app.on("ready", createWindow)
app.on('window-all-closed', () => {
    // 杀死后端（废弃）
    // pyShell.kill('SIGKILL')
    // pyProcess.kill('SIGKILL');
    console.log(pyProcess.pid)
    psTree(pyProcess.pid,(error,childs)=>{
        for(const child of childs){
            console.log('to kill child pid: ',child.PID);
            process.kill(child.PID);
        }
        process.kill(pyProcess.pid)
        app.quit()
    })
    // kill(-pyProcess.pid)
})