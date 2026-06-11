# APK 静态分析报告

## 1. 分析对象

- APK 文件：`app/build/outputs/apk/debug/app-debug.apk`
- 报告目录：`result/apk_static_report_todoapp`
- 分析时间：2026-06-08
- applicationId：`com.example.android.architecture.blueprints.main`
- 项目源码包前缀：`com.example.android.architecture.blueprints.todoapp`
- DEX 文件数量：12

## 2. APK 基本信息

| 属性 | 数值 |
|---|---|
| versionCode | 1 |
| versionName | 1.0 |
| minSdkVersion | 21 |
| targetSdkVersion | 35 |
| 主 Activity | `com.example.android.architecture.blueprints.todoapp.TodoActivity` |

## 3. 静态分析统计

| 指标 | 数值 |
|---|---:|
| 项目类，包含编译生成类 | 786 |
| 项目方法 | 2,567 |
| 项目方法之间的调用记录 | 3,391 |
| 项目方法调用外部 API 的记录 | 4,835 |
| Manifest 入口静态可达方法 | 34 |
| 核心逻辑子图节点 | 180 |
| 核心逻辑子图边 | 251 |

## 4. Manifest 组件

### Activity

- `com.example.android.architecture.blueprints.todoapp.TodoActivity`
- `com.example.android.architecture.blueprints.todoapp.HiltTestActivity`
- `androidx.compose.ui.tooling.PreviewActivity`
- `androidx.activity.ComponentActivity`

### Service

- `androidx.room.MultiInstanceInvalidationService`

### BroadcastReceiver

- `androidx.profileinstaller.ProfileInstallReceiver`

### ContentProvider

- `androidx.startup.InitializationProvider`

## 5. 核心方法

核心分数综合考虑项目内部调用入度、出度、外部 API 调用次数、方法体大小、Manifest 静态可达性和常见业务方法名称。该分数用于定位重点逻辑，不等同于人工确认后的业务优先级。

| 排名 | 方法 | 核心分数 | 项目入调用 | 项目出调用 | 外部调用 |
|---:|---|---:|---:|---:|---:|
| 1 | `TasksScreen` 的 Compose 内容 lambda | 121 | 1 | 22 | 53 |
| 2 | `TaskDetailScreen` 的 Compose 内容 lambda | 112 | 1 | 19 | 51 |
| 3 | `AddEditTaskScreen` 的 Compose 内容 lambda | 106 | 1 | 17 | 48 |
| 4 | `TasksScreen` 单例 Compose lambda | 79 | 1 | 10 | 26 |
| 5 | `StatisticsScreen` 的 Compose 内容 lambda | 78 | 1 | 12 | 18 |
| 6 | `TopAppBars` 单例 Compose lambda | 75 | 1 | 8 | 43 |
| 7 | `TasksScreen` Compose lambda | 73 | 1 | 7 | 42 |
| 8 | `TodoDrawer.AppDrawer` Compose lambda | 73 | 1 | 6 | 70 |
| 9 | `TopAppBarDropdownMenu` | 72 | 3 | 7 | 79 |
| 10 | `FilterTasksMenu` Compose lambda | 72 | 1 | 7 | 34 |
| 11 | `AddEditTaskContent` | 70 | 2 | 7 | 98 |
| 12 | `TodoNavGraph` 页面内容 lambda | 69 | 1 | 6 | 41 |
| 13 | `TopAppBars` 编译生成访问方法 | 69 | 30 | 1 | 0 |
| 14 | `TasksScreen` | 67 | 2 | 6 | 52 |
| 15 | `TaskItem` | 67 | 2 | 6 | 71 |
| 16 | `TaskDetailScreen` | 67 | 2 | 6 | 49 |
| 17 | `AddEditTaskScreen` | 67 | 2 | 6 | 48 |
| 18 | `EditTaskContent` Compose lambda | 67 | 1 | 4 | 141 |
| 19 | `StatisticsScreen` | 66 | 3 | 5 | 44 |
| 20 | `TodoNavGraph` | 64 | 2 | 5 | 55 |

完整方法签名和评分见 `07_core_methods.csv`。

## 6. 调用图文件

- `02_project_classes.csv`：项目类清单。
- `03_project_methods.csv`：项目方法及复杂度相关属性。
- `04_method_calls_all.csv`：全部调用记录。
- `05_method_calls_project_only.csv`：项目内部调用记录。
- `06_static_reachable_methods.csv`：Manifest 入口静态可达方法。
- `07_core_methods.csv`：核心方法评分。
- `08_core_logic_subgraph.gml`：核心逻辑 GML 图。
- `09_core_logic_subgraph.graphml`：核心逻辑 GraphML 图。
- `10_core_logic_subgraph.mmd`：核心逻辑 Mermaid 图。
- `11_project_callgraph.gml`：完整项目调用 GML 图。
- `12_project_callgraph.graphml`：完整项目调用 GraphML 图。
- `13_class_method_tree.txt`：类和方法树。
- `16_core_logic_metadata.json`：核心子图元数据。

## 7. 与集成测试的关系

APK 静态分析可以展示潜在调用关系和 Manifest 入口可达方法，但不能证明某个方法已被集成测试实际执行。

本轮 Android 集成测试没有完成设备端运行，原因是：

1. 当前没有连接 Android 真机或模拟器。
2. Gradle UTP 依赖下载发生 TLS 握手失败。

因此，本报告没有设备端动态覆盖率。集成测试状态见：

`../tests/integration_test_report.md`

已有 Frida 动态调用图位于：

`../dynamic_callgraph_frida/`
