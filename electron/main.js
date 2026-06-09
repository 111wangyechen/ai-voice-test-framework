// Electron主进程
const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

// Python后端进程
let backendProcess = null
let mainWindow = null

const isDev = process.env.NODE_ENV === 'development'

// 启动Python后端
function startBackend() {
  const backendPath = isDev
    ? path.join(__dirname, '../backend/main.py')
    : path.join(process.resourcesPath, 'backend', 'main.exe')  // 打包后的exe路径

  console.log('启动后端:', backendPath)

  if (isDev) {
    // 开发模式：直接运行Python脚本
    backendProcess = spawn('python', [backendPath])
  } else {
    // 生产模式：运行打包的exe
    backendProcess = spawn(backendPath)
  }

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data}`)
  })

  backendProcess.stderr.on('data', (data) => {
    console.error(`[Backend Error] ${data}`)
  })

  backendProcess.on('close', (code) => {
    console.log(`后端进程退出，代码: ${code}`)
  })

  // 等待后端启动
  return new Promise((resolve) => {
    setTimeout(resolve, 3000)  // 给后端3秒启动时间
  })
}

// 停止Python后端
function stopBackend() {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
}

// 创建主窗口
async function createWindow() {
  // 先启动后端
  await startBackend()

  // 创建浏览器窗口
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    title: 'AI辅助语音自动化测试框架',
    icon: path.join(__dirname, '../assets/icon.png')  // 应用图标
  })

  // 加载应用
  if (isDev) {
    // 开发模式：加载Vite开发服务器
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    // 生产模式：加载打包后的HTML
    mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// 应用准备就绪
app.whenReady().then(createWindow)

// 所有窗口关闭
app.on('window-all-closed', () => {
  stopBackend()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

// 应用退出前清理
app.on('before-quit', () => {
  stopBackend()
})

// IPC通信（如果需要）
ipcMain.handle('get-backend-url', () => {
  return 'http://localhost:8000'
})
