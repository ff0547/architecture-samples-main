下面是去掉所有黑色代码块后的 `summary.md` 内容。保留原有内容、顺序、表注、图片占位名称和源文件名。

# Android TODO 应用分析与集成测试报告

生成时间：2026-06-08

---

## 1. 实验目的

本实验选取 Android Architecture Samples 中的 TODO 应用作为分析对象，完成应用特性分析、工程规模统计、复杂度评估、调用图构建以及自动化测试验证。

实验内容包括：

1. 分析应用基本信息和核心功能。
2. 统计源码规模和 APK 编译后规模。
3. 评估项目工程量和源码复杂度。
4. 构建源码调用图、APK 静态调用图和 Frida 动态调用图。
5. 运行本地单元测试、Robolectric 测试和 Android 设备端集成测试。

---

## 2. 应用基本信息

选中的应用为 Android Architecture Samples TODO 应用。该应用用于记录和管理待办任务，采用 Kotlin 和 Jetpack Compose 开发。

**表 1  应用基本信息**

应用名称：Android Architecture Samples TODO 应用
工程模块：`:app`、`:shared-test`
applicationId：`com.example.android.architecture.blueprints.main`
源码包名：`com.example.android.architecture.blueprints.todoapp`
开发语言：Kotlin
UI 技术：Jetpack Compose
架构模式：单 Activity
导航组件：Navigation Compose
状态管理：ViewModel、Flow、协程
本地持久化：Room
依赖注入：Hilt
最低版本：API 21
目标版本：API 35
编译版本：API 36
Debug APK：`app/build/outputs/apk/debug/app-debug.apk`
APK 大小：24,440,637 字节
主 Activity：`com.example.android.architecture.blueprints.todoapp.TodoActivity`

【插入图片：图 1  TodoApp 应用首页】
源文件名：`01_todoapp_home.png`

---

## 3. 应用功能

TODO 应用提供以下核心功能：

1. 查看任务列表。
2. 按全部任务、未完成任务和已完成任务筛选。
3. 新增任务。
4. 编辑任务。
5. 查看任务详情。
6. 删除任务。
7. 将任务标记为已完成。
8. 将已完成任务重新激活。
9. 统计未完成任务和已完成任务数量。
10. 使用 Room 保存本地任务数据。
11. 使用假网络数据源模拟远程数据源。
12. 使用 Navigation Compose 实现单 Activity 页面导航。
13. 使用 Hilt 管理依赖注入。

**图 2  应用核心业务流程**

用户操作
↓
Jetpack Compose 页面
↓
ViewModel
↓
Repository
↓
Room 本地数据库
↓
数据更新
↓
界面刷新

【插入图片：图 3  TodoApp 新增任务页面】
源文件名：`03_todoapp_add_task.png`

【插入图片：图 4  TodoApp 任务列表页面】
源文件名：`04_todoapp_task_list.png`

---

## 4. 工程规模统计

### 4.1 源码规模

**表 2  源码规模统计**

Kotlin / Java 源文件：60
生产源码文件：37
单元测试源码文件：9
Android 集成测试源码文件：7
共享测试支持源码文件：7
生产代码 SLOC：2,229
全部代码 SLOC：4,107
源码声明的类、接口、对象和枚举：67
源码函数：302

不同源码集的作用如下：

**表 3  源码集说明**

生产源码：应用核心功能代码。

单元测试源码：本地 JVM 测试和 Robolectric 测试代码。

Android 集成测试源码：在 Android 模拟器或真实设备中执行的测试代码。

共享测试支持源码：Fake Repository、Fake DAO 等测试辅助代码。

数据来源：

* `result/project_metrics.json`
* `result/source_summary_by_set.csv`
* `result/source_metrics_by_file.csv`
* `result/file_inventory.csv`

【插入图片：图 5  工程规模统计结果】
源文件名：`05_project_metrics.png`

---

### 4.2 APK 编译后规模

通过解析 `app-debug.apk` 中的 DEX 字节码，得到编译后的项目规模。

**表 4  APK 编译后规模统计**

DEX 文件数量：12
APK 内项目类数量：786
APK 内项目方法数量：2,567
项目内部调用记录：3,391
项目调用外部 API 记录：4,835
Manifest 入口静态可达方法数量：34
核心逻辑子图节点数量：180
核心逻辑子图边数量：251

源码中手工声明的类数量为 67，而 APK 中识别到的项目类数量为 786。差异主要来自 Kotlin、Jetpack Compose、Hilt 和 Room 在编译过程中生成的辅助类、Lambda 类和实现类。

数据来源：

* `result/apk_static_report_todoapp/00_summary.md`
* `result/apk_static_report_todoapp/02_project_classes.csv`
* `result/apk_static_report_todoapp/03_project_methods.csv`

【插入图片：图 6  APK 静态分析统计结果】
源文件名：`06_apk_static_metrics.png`

---

## 5. 工程量与复杂度分析

### 5.1 复杂度计算方式

本实验采用文件级复杂度估算：

文件复杂度
= 1

* `if` 数量
* `when` 数量
* `for` 数量
* `while` 数量
* `catch` 数量
* `&&` 数量
* `||` 数量
* `?:` 数量

计算前移除了块注释和行注释。该结果用于快速定位复杂度较高的文件，不等同于专业静态分析工具生成的精确圈复杂度。

---

### 5.2 复杂度统计

**表 5  源码复杂度统计**

全部源码估算复杂度：125
生产源码估算复杂度：93
Android 集成测试源码估算复杂度：7
单元测试源码估算复杂度：10
共享测试支持代码估算复杂度：15

**表 6  高复杂度核心文件**

`TasksViewModel.kt`
SLOC：154
函数数量：9
估算复杂度：11

`AddEditTaskViewModel.kt`
SLOC：108
函数数量：7
估算复杂度：7

`TaskDetailViewModel.kt`
SLOC：99
函数数量：6
估算复杂度：7

`DefaultTaskRepository.kt`
SLOC：109
函数数量：14
估算复杂度：5

`StatisticsViewModel.kt`
SLOC：59
函数数量：2
估算复杂度：4

`TasksViewModel.kt` 负责任务列表加载、筛选、刷新、状态更新和用户交互处理，因此复杂度最高。

数据来源：

* `result/complexity_report.md`
* `result/source_metrics_by_file.csv`

【插入图片：图 7  源码复杂度报告】
源文件名：`07_complexity_report.png`

---

### 5.3 工程量估算

采用基础 COCOMO organic 模型估算：

**表 7  COCOMO 工程量估算**

生产代码 SLOC：2,229
估算工程量：5.57 人月
估算开发周期：4.80 个月
估算平均人员数量：1.16 人

该结果用于描述项目规模，不代表真实开发排期。

数据来源：

* `result/project_metrics.json`

---

## 6. 调用图分析

本实验构建了源码调用图、APK 静态调用图和 Frida 动态调用图。

### 6.1 源码调用图

源码调用图基于 Kotlin 源文件构建。

**表 8  源码调用图规模**

函数节点数量：302
启发式调用边数量：174

输出文件：

* `result/source_callgraph/nodes.csv`
* `result/source_callgraph/edges.csv`
* `result/source_callgraph/package_edges.csv`
* `result/source_callgraph/package_callgraph.mmd`
* `result/source_callgraph/method_callgraph_top200.dot`

【插入图片：图 8  源码调用图】
源文件名：`08_source_callgraph.png`

---

### 6.2 APK 静态调用图

APK 静态调用图通过解析 `app-debug.apk` 中的 DEX 字节码构建。

**表 9  APK 静态调用图规模**

项目类数量：786
项目方法数量：2,567
项目内部调用数量：3,391
外部 API 调用数量：4,835
核心逻辑子图节点数量：180
核心逻辑子图边数量：251

核心方法主要分布在以下模块：

**表 10  APK 核心逻辑模块**

`TasksScreen`：任务列表页面。

`TaskDetailScreen`：任务详情页面。

`AddEditTaskScreen`：新增和编辑任务页面。

`StatisticsScreen`：任务统计页面。

`TodoNavGraph`：页面导航逻辑。

`TaskDao_Impl`：Room 数据库访问实现。

输出文件：

* `result/apk_static_report_todoapp/00_summary.md`
* `result/apk_static_report_todoapp/04_method_calls_all.csv`
* `result/apk_static_report_todoapp/05_method_calls_project_only.csv`
* `result/apk_static_report_todoapp/07_core_methods.csv`
* `result/apk_static_report_todoapp/09_core_logic_subgraph.graphml`
* `result/apk_static_report_todoapp/12_project_callgraph.graphml`

【插入图片：图 9  APK 核心逻辑调用图】
源文件名：`09_apk_core_callgraph.png`

---

### 6.3 Frida 动态调用图

Frida 动态调用图基于运行时插桩结果构建。

**表 11  Frida 动态调用图规模**

动态节点数量：166
动态调用边数量：165

APK 静态调用图反映代码中可能存在的调用关系，Frida 动态调用图反映应用运行过程中实际发生的调用关系。

输出文件：

* `result/dynamic_callgraph_frida/callgraph.html`
* `result/dynamic_callgraph_frida/edges.csv`

【插入图片：图 10  Frida 动态调用图】
源文件名：`10_frida_dynamic_callgraph.png`

---

## 7. 自动化测试

### 7.1 本地单元测试与 Robolectric 测试

执行命令：

`.\gradlew testDebugUnitTest`

**表 12  本地单元测试与 Robolectric 测试结果**

测试用例数量：59
失败数量：0
忽略数量：0
成功率：100%
总耗时：4.780 秒

主要测试类：

* `MainActivityRobolectricTest`
* `TodoListManagerTest`
* `TodoServiceMockKTest`
* `AddEditTaskViewModelTest`
* `DefaultTaskRepositoryTest`
* `StatisticsUtilsTest`
* `StatisticsViewModelTest`
* `TaskDetailViewModelTest`
* `TasksViewModelTest`

输出文件：

* `result/tests/unit_html/index.html`
* `result/tests/unit_test_summary.csv`
* `result/tests/unit_xml/`

【插入图片：图 11  本地单元测试与 Robolectric 测试报告】
源文件名：`11_unit_test_report.png`

---

### 7.2 Android 设备端集成测试

测试运行环境：

**表 13  Android 设备端集成测试环境**

测试设备：Pixel_6 Android 虚拟设备
设备类型：Android Studio Emulator
设备状态：`emulator-5554 device`
测试类型：Android Instrumented Integration Test

执行命令：

`.\gradlew.bat :app:connectedDebugAndroidTest --no-configuration-cache --stacktrace`

**表 14  Android 设备端集成测试结果**

测试用例数量：38
失败数量：0
跳过数量：0
成功率：100%
测试耗时：57.918 秒
构建状态：`BUILD SUCCESSFUL`

测试类及覆盖范围：

**表 15  Android 设备端集成测试清单**

`AddEditTaskScreenTest`
用例数：2
测试范围：新增和编辑任务页面

`TaskDaoTest`
用例数：8
测试范围：Room 数据库和 DAO 操作

`StatisticsScreenTest`
用例数：1
测试范围：统计页面

`TaskDetailScreenTest`
用例数：2
测试范围：任务详情页面

`AppNavigationTest`
用例数：5
测试范围：页面导航流程

`TasksScreenTest`
用例数：12
测试范围：任务列表 Compose 页面

`TasksTest`
用例数：8
测试范围：任务端到端操作流程

合计：38 个用例。

输出文件：

* `result/tests/integration_test_report.md`
* `result/tests/android_integration_test_inventory.csv`
* `app/build/reports/androidTests/connected/index.html`

【插入图片：图 12  ADB 模拟器连接结果】
源文件名：`12_adb_emulator_device.png`

【插入图片：图 13  设备端集成测试 BUILD SUCCESSFUL】
源文件名：`13_integration_test_build_successful.png`

【插入图片：图 14  设备端集成测试 HTML 报告】
源文件名：`14_integration_test_html_report.png`

---

## 8. 结果文件索引

`result/`

* `README.md`
* `project_metrics.json`
* `source_summary_by_set.csv`
* `source_metrics_by_file.csv`
* `file_inventory.csv`
* `complexity_report.md`

`result/source_callgraph/`

* `nodes.csv`
* `edges.csv`
* `package_edges.csv`
* `package_callgraph.mmd`
* `method_callgraph_top200.dot`

`result/apk_static_report_todoapp/`

* `00_summary.md`
* `01_apk_info.json`
* `02_project_classes.csv`
* `03_project_methods.csv`
* `04_method_calls_all.csv`
* `05_method_calls_project_only.csv`
* `06_static_reachable_methods.csv`
* `07_core_methods.csv`
* `09_core_logic_subgraph.graphml`
* `12_project_callgraph.graphml`

`result/dynamic_callgraph_frida/`

* `callgraph.html`
* `edges.csv`

`result/tests/`

* `integration_test_report.md`
* `android_integration_test_inventory.csv`
* `unit_test_summary.csv`
* `unit_html/index.html`
* `unit_xml/`
* `integration_html/`

`result/logs/`

* `connectedDebugAndroidTest_observed.log`
* `connectedDebugAndroidTest_success.log`
