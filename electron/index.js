// 导入模块
const { app, BrowserWindow } = require("electron")
// const { path } = require("path")
// 从 python-shell 导入一个 PythonShell 对象 (注意大小写)
const {PythonShell}  = require("python-shell")
// Declaring tree-kill
var kill = require('tree-kill');


// 创建窗口
function createWindow() {
    let win = new BrowserWindow({
        // 设置一个宽为800, 高为600的窗口
        width: 800,
        height: 600,
        icon: './logo.png'
    })
    
    
    // PythonShell.run("./dep/backend/server.py", {mode:'text'})
    // 加载本地的 index.html
    win.loadFile("./dep/frontend/index.html");
    win.setMenuBarVisibility(false)

}

// 启动后端
const pyShell = new PythonShell("./dep/backend/server.py",{mode:'text'});

// 启动
app.on("ready", createWindow)
app.on('window-all-closed', () => {
    // pyShell.kill('SIGINT')
    kill(pyShell.childProcess.pid)
    app.quit()
})