# Frida 动态方法调用图实验进度记录

## 1. 项目目录

本实验基于 Android 项目：

```text
C:\Users\fsqfs\Desktop\architecture-samples-main
```

GitHub 仓库：

```text
ff0547/architecture-samples-main
```

应用包名：

```text
com.example.android.architecture.blueprints.main
```

项目代码包名前缀：

```text
com.example.android.architecture.blueprints
```

---

## 2. 实验目标

基于 Frida 动态插桩框架实现 Android 应用运行时方法调用追踪，并构建动态方法调用图。

目标功能：

1. Hook 项目包内的 Java / Kotlin 方法；
2. 记录运行期间真实发生的方法调用关系；
3. 聚合得到 `caller -> callee` 有向调用边；
4. 输出 JSON、CSV 和 HTML 文件；
5. 使用浏览器直接查看可交互的方法调用图。

与 Androguard 静态分析不同，Frida 动态分析只记录本次操作期间实际执行的方法。

---

## 3. 已完成内容

### 3.1 Android 项目已恢复正常同步

此前 `app/build.gradle.kts` 中存在：

```kotlin
compileSdkMinor = 1
buildToolsVersion = "34.0.0"
```

其中：

```kotlin
compileSdkMinor = 1
```

会导致：

```text
Unresolved reference: compileSdkMinor
```

已删除上述两行。

当前 `compileSdk` 已正确解析为：

```text
36 (API 36.0)
```

`Build Tools Version` 保持为空，由 Android Gradle Plugin 自动选择。

---

### 3.2 Python Community 插件问题已确认

Android Studio 中出现：

```text
No Python interpreter configured for the module
```

该提示只影响 `.py` 文件的代码检查和在 Android Studio 内直接运行 Python 脚本。

不影响：

```text
Gradle Sync
Kotlin / Java 编译
Android App 正常运行
APK 构建
Robolectric 测试
Espresso 测试
Appium 测试
```

Python 脚本可以继续使用 PowerShell、cmd 或 PyCharm 运行。

---

### 3.3 adb 已配置成功

Android SDK Platform Tools 路径：

```text
C:\Users\fsqfs\AppData\Local\Android\Sdk\platform-tools
```

已验证：

```powershell
adb version
```

输出：

```text
Android Debug Bridge version 1.0.41
Version 37.0.0-14910828
Installed as C:\Users\fsqfs\AppData\Local\Android\Sdk\platform-tools\adb.exe
```

已验证模拟器连接：

```powershell
adb devices
```

输出：

```text
List of devices attached
emulator-5554    device
```

已验证模拟器 CPU 架构：

```powershell
adb shell getprop ro.product.cpu.abi
```

输出：

```text
x86_64
```

---

### 3.4 Frida Python 客户端已安装

已执行：

```powershell
pip install frida frida-tools pyvis
```

已验证：

```powershell
frida --version
```

当前版本：

```text
17.10.0
```

后续下载的 `frida-server` 必须与本地客户端版本完全一致：

```text
frida-server-17.10.0-android-x86_64
```

---

## 4. 当前遇到的问题

执行：

```powershell
adb root
```

输出：

```text
adbd cannot run as root in production builds
```

原因：

当前模拟器使用的是 production build 系统镜像，默认禁止将 `adbd` 切换为 root。

这不影响普通 Android App 测试，但会影响直接部署 `frida-server`。

当前模拟器仍然可以正常用于：

```text
安装 APK
运行 App
执行 Espresso 测试
执行 Appium 测试
查看日志
使用 adb shell
```

但不适合直接运行需要 root 权限的 `frida-server`。

---

## 5. 当前进度

当前正在 Android Studio 中下载新的 SDK / 系统镜像，用于新建可 root 的模拟器。

建议使用：

```text
Android 14 / API 34 / x86_64 / Google APIs
```

或者：

```text
Android 15 / API 35 / x86_64 / Google APIs
```

不要选择：

```text
Google Play
```

因为带 Google Play 的系统镜像通常属于 production build，默认无法使用：

```powershell
adb root
```

---

## 6. 下一步操作

### 6.1 新建可 root 模拟器

在 Android Studio 中进入：

```text
Tools
→ Device Manager
→ Create Virtual Device
```

选择普通 Pixel 设备，例如：

```text
Pixel 6
```

然后选择：

```text
Google APIs
x86_64
```

不要选择：

```text
Google Play
```

---

### 6.2 启动新模拟器后验证 root

关闭旧模拟器，只保留新模拟器运行。

执行：

```powershell
adb devices
adb root
adb shell id
adb shell getprop ro.product.cpu.abi
```

预期结果：

```text
uid=0(root)
x86_64
```

---

### 6.3 下载 Frida Server

需要下载：

```text
frida-server-17.10.0-android-x86_64.xz
```

解压后重命名为：

```text
frida-server
```

放入项目根目录：

```text
C:\Users\fsqfs\Desktop\architecture-samples-main
```

---

### 6.4 推送并启动 Frida Server

在 PowerShell 中进入项目目录：

```powershell
cd C:\Users\fsqfs\Desktop\architecture-samples-main
```

执行：

```powershell
adb push .\frida-server /data/local/tmp/frida-server
adb shell chmod 755 /data/local/tmp/frida-server
adb shell "/data/local/tmp/frida-server >/dev/null 2>&1 &"
Start-Sleep -Seconds 2
frida-ps -U
```

如果 `frida-ps -U` 能够列出模拟器进程，说明 Frida Server 已成功启动。

---

### 6.5 构建并安装 APK

构建 Debug APK：

```powershell
.\gradlew.bat assembleDebug
```

安装：

```powershell
adb install -r .\app\build\outputs\apk\debug\app-debug.apk
```

确认包名：

```powershell
adb shell pm list packages | Select-String architecture
```

预期输出：

```text
package:com.example.android.architecture.blueprints.main
```

---

### 6.6 运行动态方法调用图分析

项目根目录中需要放置：

```text
trace_java_calls.js
frida_callgraph.py
```

运行：

```powershell
python .\frida_callgraph.py --duration 180
```

在 180 秒内操作 App：

```text
打开任务列表
→ 新建任务
→ 保存任务
→ 查看任务详情
→ 编辑任务
→ 标记完成
→ 删除任务
→ 打开统计页面
```

分析结束后生成：

```text
frida_callgraph_output
├── callgraph.html
├── callgraph.json
├── nodes.csv
└── edges.csv
```

其中：

```text
callgraph.html
```

可以使用浏览器直接打开。

---

## 7. GitHub 上传命令

将本文件保存到项目根目录，文件名：

```text
FRIDA_DYNAMIC_CALLGRAPH_PROGRESS.md
```

然后在 PowerShell 中执行：

```powershell
cd C:\Users\fsqfs\Desktop\architecture-samples-main

git status
git add .\FRIDA_DYNAMIC_CALLGRAPH_PROGRESS.md
git commit -m "docs: add Frida dynamic call graph progress notes"
git push origin main
```

如果同时已经新建 Frida 脚本，可以使用：

```powershell
git add .\FRIDA_DYNAMIC_CALLGRAPH_PROGRESS.md .\trace_java_calls.js .\frida_callgraph.py .\run_frida_callgraph.bat
git commit -m "feat: add Frida dynamic call graph tracer"
git push origin main
```

不要上传：

```text
frida-server
frida-server-*.xz
```

这些二进制文件体积较大，也不适合提交到仓库。

建议在 `.gitignore` 中增加：

```gitignore
frida-server
frida-server-*.xz
frida_callgraph_output/
frida_callgraph_clean/
```

---

## 8. 当前结论

当前 Android 项目已经可以正常同步，`adb` 和 Frida Python 客户端也已经配置成功。

当前阻塞点不是代码问题，而是旧模拟器使用 production build 系统镜像，无法执行：

```powershell
adb root
```

当前正在下载新的 Google APIs SDK / 系统镜像。下载完成后，需要新建可 root 模拟器，再继续部署：

```text
frida-server-17.10.0-android-x86_64
```

完成 Frida Server 部署后，即可运行动态方法调用图脚本并生成浏览器可直接访问的 HTML 调用图。
