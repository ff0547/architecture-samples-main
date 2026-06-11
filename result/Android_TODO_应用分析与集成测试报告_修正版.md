# Android TODO 应用分析与集成测试报告

生成时间：2026-06-08

## 1. 实验目的

本实验选取 Android Architecture Samples 中的 TODO 应用作为分析对象，完成应用特性分析、工程规模统计、复杂度评估、调用图构建以及自动化测试验证。报告同时使用图表展示关键数据，便于直观比较不同源码集、调用图和测试结果。

## 2. 应用基本信息

选中的应用为 Android Architecture Samples TODO 应用，用于记录和管理待办任务。

### 表 1  应用原始信息

应用名称：Android Architecture Samples TODO 应用  
工程模块：`:app`、`:shared-test`  
applicationId：`com.example.android.architecture.blueprints.main`  
源码包名：`com.example.android.architecture.blueprints.todoapp`  
开发语言：Kotlin  
UI 技术：Jetpack Compose  
架构模式：单 Activity  
导航组件：Navigation Compose  
状态管理：ViewModel、Flow、协程  
数据访问：Repository  
本地持久化：Room  
依赖注入：Hilt  
最低 Android 版本：API 21  
目标 Android 版本：API 35  
编译 Android 版本：API 36  
Debug APK：`app/build/outputs/apk/debug/app-debug.apk`  
APK 大小：24,440,637 字节  
主 Activity：`com.example.android.architecture.blueprints.todoapp.TodoActivity`

【插入图片：图 11  TodoApp 应用首页】  
源文件名：`11_todoapp_home.png`

## 3. 应用功能特性

TODO 应用具有以下功能：

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

### 应用核心业务流程

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

【插入图片：图 12  TodoApp 新增任务页面】  
源文件名：`12_todoapp_add_task.png`

【插入图片：图 13  TodoApp 任务列表页面】  
源文件名：`13_todoapp_task_list.png`

## 4. 工程规模统计

### 4.1 仓库文件规模

仓库中共统计到 102 个文件，统计时排除了 `build`、`node_modules` 和 `result` 等生成目录。

### 表 2  仓库文件扩展名统计

`.kt`：61  
`.xml`：26  
`.kts`：6  
`.py`：3  
`.md`：3  
`.js`：1  
`.ts`：1  
`.toml`：1  

【插入图片：图 5  仓库文件扩展名统计】  
源文件名：`05_repository_files_by_extension.png`

### 4.2 源码规模

### 表 3  各源码集规模

生产源码：37 个文件，2,229 SLOC。  
单元测试源码：9 个文件，742 SLOC。  
Android 集成测试源码：7 个文件，893 SLOC。  
共享测试支持源码：7 个文件，243 SLOC。  
全部 Kotlin / Java 源文件：60 个。  
全部源码 SLOC：4,107。  
源码声明的类、接口、对象和枚举：67。  
源码函数：302。  

【插入图片：图 1  各源码集文件数量】  
源文件名：`01_source_files_by_set.png`

【插入图片：图 2  各源码集 SLOC】  
源文件名：`02_sloc_by_set.png`

### 4.3 APK 编译后规模

通过解析 `app-debug.apk` 中的 DEX 字节码，得到以下结果。

### 表 4  APK 编译后规模

DEX 文件数量：12。  
APK 内项目类数量：786。  
APK 内项目方法数量：2,567。  
项目内部调用记录：3,391。  
项目调用外部 API 记录：4,835。  
Manifest 入口静态可达方法数量：34。  
核心逻辑子图节点数量：180。  
核心逻辑子图边数量：251。  

源码中手工声明的类、接口、对象和枚举共 67 个，而 APK 中识别到的项目类数量为 786。差异主要来自 Kotlin、Jetpack Compose、Hilt 和 Room 在编译过程中生成的辅助类、Lambda 类和实现类。

【插入图片：图 7  APK 静态分析指标】  
源文件名：`07_apk_static_metrics.png`

## 5. 工程量与复杂度分析

### 5.1 复杂度计算方法

本实验使用文件级圈复杂度估算：

文件复杂度 = 1 + `if` 数量 + `when` 数量 + `for` 数量 + `while` 数量 + `catch` 数量 + `&&` 数量 + `||` 数量 + `?:` 数量。

计算前移除了块注释和行注释。该结果适合快速定位高风险文件，但不等同于编译器或专业静态分析工具计算的精确圈复杂度。

### 5.2 复杂度汇总

### 表 5  各源码集复杂度

全部源码估算复杂度：125。  
生产源码估算复杂度：93。  
Android 集成测试源码估算复杂度：7。  
单元测试源码估算复杂度：10。  
共享测试支持代码估算复杂度：15。  

【插入图片：图 3  各源码集估算复杂度】  
源文件名：`03_complexity_by_set.png`

### 5.3 高复杂度文件

### 表 6  高复杂度文件

1. `TasksViewModel.kt`：154 SLOC，9 个函数，复杂度 11。  
2. `AddEditTaskViewModel.kt`：108 SLOC，7 个函数，复杂度 7。  
3. `TaskDetailViewModel.kt`：99 SLOC，6 个函数，复杂度 7。  
4. `FakeTaskRepository.kt`：109 SLOC，17 个函数，复杂度 6。  
5. `DefaultTaskRepository.kt`：109 SLOC，14 个函数，复杂度 5。  
6. `StatisticsViewModel.kt`：59 SLOC，2 个函数，复杂度 4。  
7. `TaskDetailScreen.kt`：173 SLOC，5 个函数，复杂度 4。  
8. `TasksScreen.kt`：316 SLOC，9 个函数，复杂度 4。  
9. `TodoListManager.kt`：35 SLOC，7 个函数，复杂度 4。  
10. `AddEditTaskScreen.kt`：139 SLOC，2 个函数，复杂度 3。  

其中，`TasksViewModel.kt` 负责任务列表加载、筛选、刷新、状态更新和用户交互处理，因此复杂度最高。

【插入图片：图 4  高复杂度文件前十名】  
源文件名：`04_top10_complex_files.png`

### 5.4 COCOMO 工程量估算

采用基础 COCOMO organic 模型进行估算。

### 表 7  工程量估算结果

生产代码 SLOC：2,229。  
估算工程量：5.57 人月。  
估算开发周期：4.80 个月。  
估算平均人员数量：1.16 人。  

该结果仅用于描述项目规模，不代表真实开发排期。

## 6. 调用图分析

本实验构建了源码调用图、APK 静态调用图和 Frida 动态调用图。

### 6.1 源码调用图

源码调用图基于 Kotlin 源文件构建。

### 表 8  源码调用图规模

函数节点数量：302。  
启发式调用边数量：174。  
包级调用边数量：21。  

输出文件：

- `result/source_callgraph/nodes.csv`
- `result/source_callgraph/edges.csv`
- `result/source_callgraph/package_edges.csv`
- `result/source_callgraph/package_callgraph.mmd`
- `result/source_callgraph/method_callgraph_top200.dot`

【插入图片：图 14  源码调用图】  
源文件名：`14_source_callgraph.png`

### 6.2 APK 静态调用图

APK 静态调用图通过解析 `app-debug.apk` 中的 DEX 字节码构建。

### 表 9  APK 静态调用图规模

项目类数量：786。  
项目方法数量：2,567。  
项目内部调用数量：3,391。  
外部 API 调用数量：4,835。  
核心逻辑子图节点数量：180。  
核心逻辑子图边数量：251。  

核心方法主要分布在任务列表页面、任务详情页面、新增和编辑页面、统计页面、导航逻辑和 Room 数据库访问实现中。

输出文件：

- `result/apk_static_report_todoapp/00_summary.md`
- `result/apk_static_report_todoapp/04_method_calls_all.csv`
- `result/apk_static_report_todoapp/05_method_calls_project_only.csv`
- `result/apk_static_report_todoapp/07_core_methods.csv`
- `result/apk_static_report_todoapp/09_core_logic_subgraph.graphml`
- `result/apk_static_report_todoapp/12_project_callgraph.graphml`

【插入图片：图 15  APK 核心逻辑调用图】  
源文件名：`15_apk_core_callgraph.png`

### 6.3 Frida 动态调用图

Frida 动态调用图基于运行时插桩结果构建。

### 表 10  Frida 动态调用图规模

动态节点数量：166。  
动态调用边数量：165。  

APK 静态调用图反映代码中可能存在的调用关系；Frida 动态调用图反映应用运行过程中实际发生的调用关系。

输出文件：

- `result/dynamic_callgraph_frida/callgraph.html`
- `result/dynamic_callgraph_frida/callgraph.json`
- `result/dynamic_callgraph_frida/edges.csv`
- `result/dynamic_callgraph_frida/nodes.csv`

【插入图片：图 6  三类调用图规模比较】  
源文件名：`06_callgraph_size_comparison.png`

【插入图片：图 16  Frida 动态调用图】  
源文件名：`16_frida_dynamic_callgraph.png`

### 6.4 测试覆盖边界

APK 静态分析展示的是潜在调用关系和 Manifest 入口静态可达方法。Frida 动态调用图展示的是当前运行场景中实际捕获到的调用关系。

当前未提供 JaCoCo XML，因此无法进一步列出集成测试运行时真正覆盖的全部方法。该边界不影响集成测试通过率统计。

## 7. 自动化测试

### 7.1 本地单元测试与 Robolectric 测试

执行命令：`.\gradlew testDebugUnitTest`

### 表 11  本地测试结果

测试用例数量：59。  
失败数量：0。  
忽略数量：0。  
成功率：100%。  
总耗时：4.780 秒。  

### 表 12  本地测试类与用例数量

`MainActivityRobolectricTest`：1 个。  
`TodoListManagerTest`：7 个。  
`TodoServiceMockKTest`：5 个。  
`AddEditTaskViewModelTest`：6 个。  
`DefaultTaskRepositoryTest`：16 个。  
`StatisticsUtilsTest`：4 个。  
`StatisticsViewModelTest`：3 个。  
`TaskDetailViewModelTest`：7 个。  
`TasksViewModelTest`：10 个。  

【插入图片：图 8  本地测试类用例数量】  
源文件名：`08_local_tests_by_class.png`

【插入图片：图 17  本地测试 HTML 报告】  
源文件名：`17_unit_test_report.png`

### 7.2 Android 设备端集成测试

测试设备：Pixel_6 Android 虚拟设备。  
设备类型：Android Studio Emulator。  
设备状态：`emulator-5554 device`。  
测试类型：Android Instrumented Integration Test。  

执行命令：`.\gradlew.bat :app:connectedDebugAndroidTest --no-configuration-cache --stacktrace`

### 表 13  Android 设备端集成测试结果

测试用例数量：38。  
失败数量：0。  
跳过数量：0。  
成功率：100%。  
测试耗时：57.918 秒。  
构建状态：`BUILD SUCCESSFUL`。  

### 表 14  Android 设备端集成测试清单

`AddEditTaskScreenTest`：2 个，覆盖新增和编辑任务页面。  
`TaskDaoTest`：8 个，覆盖 Room 数据库和 DAO 操作。  
`StatisticsScreenTest`：1 个，覆盖统计页面。  
`TaskDetailScreenTest`：2 个，覆盖任务详情页面。  
`AppNavigationTest`：5 个，覆盖页面导航流程。  
`TasksScreenTest`：12 个，覆盖任务列表 Compose 页面。  
`TasksTest`：8 个，覆盖任务端到端操作流程。  

合计：38 个测试用例。

【插入图片：图 9  Android 集成测试类用例数量】  
源文件名：`09_integration_tests_by_class.png`

【插入图片：图 10  自动化测试结果比较】  
源文件名：`10_test_suite_results.png`

【插入图片：图 18  ADB 模拟器连接结果】  
源文件名：`18_adb_emulator_device.png`

【插入图片：图 19  Android 集成测试 BUILD SUCCESSFUL】  
源文件名：`19_integration_test_build_successful.png`

【插入图片：图 20  Android 集成测试 HTML 报告】  
源文件名：`20_integration_test_html_report.png`

## 8. 结果文件索引

### 8.1 工程规模与复杂度

- `result/project_metrics.json`
- `result/source_summary_by_set.csv`
- `result/source_metrics_by_file.csv`
- `result/file_inventory.csv`
- `result/complexity_report.md`

### 8.2 源码调用图

- `result/source_callgraph/nodes.csv`
- `result/source_callgraph/edges.csv`
- `result/source_callgraph/package_edges.csv`
- `result/source_callgraph/package_callgraph.mmd`
- `result/source_callgraph/method_callgraph_top200.dot`

### 8.3 APK 静态调用图

- `result/apk_static_report_todoapp/00_summary.md`
- `result/apk_static_report_todoapp/01_apk_info.json`
- `result/apk_static_report_todoapp/02_project_classes.csv`
- `result/apk_static_report_todoapp/03_project_methods.csv`
- `result/apk_static_report_todoapp/04_method_calls_all.csv`
- `result/apk_static_report_todoapp/05_method_calls_project_only.csv`
- `result/apk_static_report_todoapp/06_static_reachable_methods.csv`
- `result/apk_static_report_todoapp/07_core_methods.csv`
- `result/apk_static_report_todoapp/08_core_logic_subgraph.gml`
- `result/apk_static_report_todoapp/09_core_logic_subgraph.graphml`
- `result/apk_static_report_todoapp/10_core_logic_subgraph.mmd`
- `result/apk_static_report_todoapp/11_project_callgraph.gml`
- `result/apk_static_report_todoapp/12_project_callgraph.graphml`
- `result/apk_static_report_todoapp/13_class_method_tree.txt`
- `result/apk_static_report_todoapp/14_test_coverage_notice.txt`
- `result/apk_static_report_todoapp/16_core_logic_metadata.json`

### 8.4 Frida 动态调用图

- `result/dynamic_callgraph_frida/callgraph.html`
- `result/dynamic_callgraph_frida/callgraph.json`
- `result/dynamic_callgraph_frida/edges.csv`
- `result/dynamic_callgraph_frida/nodes.csv`

### 8.5 测试文件

- `result/tests/unit_test_summary.csv`
- `result/tests/unit_html/index.html`
- `result/tests/unit_xml/`
- `result/tests/android_integration_test_inventory.csv`
- `app/build/reports/androidTests/connected/index.html`

## 9. 图表生成说明

运行图表生成脚本：

`python generate_todo_report_charts.py`

脚本将读取：

- `source_summary_by_set(3).csv`
- `source_metrics_by_file(3).csv`
- `file_inventory(3).csv`

并在 `todo_report_charts/` 目录中生成 10 张图表。
