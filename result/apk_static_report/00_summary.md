# APK 静态分析对照报告

## 1. 报告说明

本目录是第一次使用 APK 的 applicationId 作为项目包过滤前缀生成的对照报告。

- APK：`app/build/outputs/apk/debug/app-debug.apk`
- applicationId：`com.example.android.architecture.blueprints.main`
- 本次过滤前缀：`com.example.android.architecture.blueprints.main`
- 实际源码包：`com.example.android.architecture.blueprints.todoapp`

由于 applicationId 和源码包名不同，本次分析没有匹配到应用源码类。因此结果中的项目类、项目方法和项目调用均为 0。

## 2. 对照结果

| 指标 | 数值 |
|---|---:|
| 项目类 | 0 |
| 项目方法 | 0 |
| 项目内部调用 | 0 |
| Manifest 入口静态可达方法 | 0 |
| 核心子图节点 | 0 |
| 核心子图边 | 0 |

## 3. 正确报告

有效的 APK 静态分析位于：

`../apk_static_report_todoapp/`

该报告使用正确源码包前缀：

`com.example.android.architecture.blueprints.todoapp`

正确结果为 786 个项目类、2,567 个项目方法和 3,391 条项目内部调用。

本目录保留用于说明过滤条件差异，不应作为最终应用规模或调用图结果。
