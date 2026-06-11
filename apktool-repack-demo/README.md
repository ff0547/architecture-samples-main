# Android APKTool 解包、修改、重打包与验证脚本

本项目用于课程练习：对 Android Studio 构建出的 APK 进行 APKTool 解包、修改、重打包、签名、安装和验证。

## 适用对象

默认使用 Android Studio 项目：

```text
C:\Users\fsqfs\Desktop\architecture-samples-main
```

默认 APK：

```text
app\build\outputs\apk\debug\app-debug.apk
```

脚本会把应用名称修改为：

```text
TODO APKTool Modified
```

安装后可以直接通过桌面图标名称或应用界面截图验证修改结果。

## 目录结构

```text
apktool-repack-demo
├─ README.md
├─ config.ps1
├─ run_all.ps1
├─ .gitignore
└─ scripts
   ├─ 01_build_original_apk.ps1
   ├─ 02_decode_patch_rebuild.ps1
   └─ 03_sign_install_verify.ps1
```

## 前置条件

1. 已安装 Android Studio 和 Android SDK。
2. 已安装 JDK，`java` 和 `keytool` 可在终端运行。
3. 已下载 APKTool：
   - `apktool.jar`
   - Windows 包装脚本 `apktool.bat`
4. 已连接模拟器或 Android 手机，并开启 USB 调试。

建议将 APKTool 文件放在：

```text
C:\tools\apktool\apktool.jar
C:\tools\apktool\apktool.bat
```

如路径不同，请修改 `config.ps1`。

## 执行方法

在 PowerShell 中进入本项目目录：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run_all.ps1
```

脚本将依次完成：

```text
Android Studio 工程构建 APK
        ↓
APKTool 解包
        ↓
修改 AndroidManifest.xml 中的应用名称
        ↓
同步修改 res\values\strings.xml 中的 app_name（若存在）
        ↓
APKTool 重打包
        ↓
zipalign 对齐
        ↓
apksigner 签名并校验
        ↓
adb 卸载旧版本、安装新版本
        ↓
adb 启动应用
```

## 关键输出文件

```text
work\original.apk
work\decoded\
work\rebuilt-unsigned.apk
work\rebuilt-aligned.apk
work\rebuilt-signed.apk
work\verify.txt
```

## 验证截图建议

报告中保留以下截图：

1. Android Studio 原项目运行界面。
2. `apktool d` 解包成功的 PowerShell 输出。
3. `work\decoded\AndroidManifest.xml` 修改后的应用名称。
4. `apktool b` 重打包成功的 PowerShell 输出。
5. `apksigner verify --verbose --print-certs` 校验成功输出。
6. `adb install` 显示 `Success`。
7. 手机或模拟器中重打包应用的名称或运行界面。

## GitHub 上传

在项目目录执行：

```powershell
git init
git add .
git commit -m "Add APKTool unpack patch rebuild and verification scripts"
git branch -M main
git remote add origin https://github.com/<你的用户名>/apktool-repack-demo.git
git push -u origin main
```

上传后，在报告中附上仓库链接：

```text
https://github.com/<你的用户名>/apktool-repack-demo
```

## 注意事项

- 不要提交 `work` 目录，避免将 APK、反编译文件和签名产物上传到仓库。
- 不要提交 `demo.keystore`，签名文件仅保存在本地。
- APK 重新打包后原签名会失效，因此必须重新签名。
- 原 APK 与重打包 APK 若使用不同签名，不能直接覆盖安装。脚本会先卸载旧版本，再安装新版本。
