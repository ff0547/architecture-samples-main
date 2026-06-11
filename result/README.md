# 应用分析与集成测试结果

生成时间：2026-06-08

## 1. 应用基本信息

- 应用名称：Android Architecture Samples TODO 应用
- 工程模块：`:app`、`:shared-test`
- applicationId：`com.example.android.architecture.blueprints.main`
- 源码包名：`com.example.android.architecture.blueprints.todoapp`
- 开发语言：Kotlin
- UI 技术：Jetpack Compose
- 架构组件：Navigation Compose、ViewModel、Flow、协程、Room、Hilt
- 最低 Android 版本：API 21
- 目标 Android 版本：API 35
- 编译 Android 版本：API 36
- Debug APK：`app/build/outputs/apk/debug/app-debug.apk`
- APK 大小：24,440,637 字节

## 2. 应用功能

- 查看任务列表。
- 按全部、未完成、已完成状态筛选任务。
- 新增任务和编辑任务。
- 查看任务详情。
- 删除任务。
- 将任务标记为完成或重新激活。
- 统计未完成任务和已完成任务。
- 使用 Room 保存本地任务数据。
- 使用假网络数据源模拟远程数据。
- 使用 Hilt 管理依赖注入。
- 使用 Navigation Compose 实现单 Activity 页面导航。

## 3. 工程规模

| 指标 | 数值 |
|---|---:|
| Kotlin/Java 源文件 | 60 |
| 生产源码文件 | 37 |
| 单元测试源码文件 | 9 |
| Android 集成测试源码文件 | 7 |
| 共享测试支持源码文件 | 7 |
| 生产代码 SLOC | 2,229 |
| 全部代码 SLOC，包含测试 | 4,107 |
| 源码声明的类、接口、对象和枚举 | 67 |
| 源码函数 | 302 |
| APK 内项目类，包含编译生成类 | 786 |
| APK 内项目方法 | 2,567 |
| APK 内项目方法调用 | 3,391 |
| APK 方法调用外部 API 的记录 | 4,835 |
| Manifest 入口静态可达方法 | 34 |

## 4. 工程量与复杂度

- 文件级估算复杂度总计：125。
- 生产源码估算复杂度：93。
- 基础 COCOMO 估算工程量：5.57 人月。
- 工程量估算只用于规模参考，不代表真实开发排期。
- 复杂度计算方式和高复杂度文件见 `complexity_report.md`。

## 5. 调用图

### 源码调用图

- 函数节点：302。
- 启发式调用边：174。
- 文件目录：`source_callgraph/`。
- `nodes.csv`：函数节点。
- `edges.csv`：函数调用边。
- `package_edges.csv`：包级调用关系。
- `package_callgraph.mmd`：Mermaid 包级调用图。
- `method_callgraph_top200.dot`：主要方法调用 DOT 图。

### APK 静态调用图

- 项目类：786。
- 项目方法：2,567。
- 项目内部调用：3,391。
- 核心子图：180 个节点、251 条边。
- 文件目录：`apk_static_report_todoapp/`。
- 完整调用关系见 `04_method_calls_all.csv` 和 `05_method_calls_project_only.csv`。
- GraphML 图见 `12_project_callgraph.graphml`。

### Frida 动态调用图

- 动态节点：166。
- 动态调用边：165。
- 文件目录：`dynamic_callgraph_frida/`。
- 可视化入口：`dynamic_callgraph_frida/callgraph.html`。

## 6. 集成测试

本次工作的目标是 Android 集成测试。工程中共有：

- 7 个 `androidTest` 测试文件。
- 38 个声明的 `@Test` 集成测试用例。

已执行 `connectedDebugAndroidTest`，但没有进入设备端测试阶段，原因如下：

1. `adb devices` 没有发现已连接设备或已启动模拟器。
2. Gradle 下载 UTP 依赖时发生 TLS 握手失败：
   `com.android.tools.utp:android-test-plugin-host-additional-test-output:31.13.2`。

因此，本轮没有设备端集成测试通过率。测试清单、阻塞原因和执行状态见：

- `tests/integration_test_report.md`
- `tests/android_integration_test_inventory.csv`
- `logs/connectedDebugAndroidTest_observed.log`

## 7. 辅助验证

- `assembleDebug`：通过。
- `testDebugUnitTest`：通过。
- 本地单元测试和 Robolectric 测试：59 个。
- 失败：0。
- 错误：0。
- 跳过：0。

本地测试结果仅作为构建和基础功能验证，不替代 Android 设备端集成测试。

## 8. 文件索引

- `project_metrics.json`：完整机器可读指标。
- `source_summary_by_set.csv`：各源码集汇总。
- `source_metrics_by_file.csv`：逐文件代码量和复杂度。
- `file_inventory.csv`：工程文件清单。
- `complexity_report.md`：复杂度分析。
- `source_callgraph/`：源码调用图。
- `apk_static_report_todoapp/`：有效的 APK 静态分析。
- `apk_static_report/`：使用 applicationId 作为过滤前缀的对照分析。
- `dynamic_callgraph_frida/`：Frida 动态调用图。
- `tests/`：测试清单、JUnit XML、HTML 报告和集成测试说明。
- `logs/`：构建与测试执行日志。
