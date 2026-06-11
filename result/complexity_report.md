# 源码复杂度报告

## 1. 计算说明

本报告使用文件级圈复杂度估算：

`1 + if + when + for + while + catch + && + || + ?:`

计算前移除了块注释和行注释。该结果适合快速定位高风险文件，但不等同于编译器或专业静态分析工具计算的精确圈复杂度。

## 2. 汇总

- 全部源码估算复杂度：125。
- 生产源码估算复杂度：93。
- Android 集成测试源码估算复杂度：7。
- 单元测试源码估算复杂度：10。
- 共享测试支持代码估算复杂度：15。

## 3. 高复杂度文件

| 排名 | 文件 | 源码集 | SLOC | 类数量 | 函数数量 | 估算复杂度 |
|---:|---|---|---:|---:|---:|---:|
| 1 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/tasks/TasksViewModel.kt` | 生产代码 | 154 | 3 | 9 | 11 |
| 2 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/addedittask/AddEditTaskViewModel.kt` | 生产代码 | 108 | 2 | 7 | 7 |
| 3 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/taskdetail/TaskDetailViewModel.kt` | 生产代码 | 99 | 2 | 6 | 7 |
| 4 | `shared-test/src/main/java/com/example/android/architecture/blueprints/todoapp/data/FakeTaskRepository.kt` | 共享测试支持 | 109 | 1 | 17 | 6 |
| 5 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/data/DefaultTaskRepository.kt` | 生产代码 | 109 | 1 | 14 | 5 |
| 6 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/statistics/StatisticsViewModel.kt` | 生产代码 | 59 | 2 | 2 | 4 |
| 7 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/taskdetail/TaskDetailScreen.kt` | 生产代码 | 173 | 0 | 5 | 4 |
| 8 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/tasks/TasksScreen.kt` | 生产代码 | 316 | 0 | 9 | 4 |
| 9 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/TodoListManager.kt` | 生产代码 | 35 | 1 | 7 | 4 |
| 10 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/addedittask/AddEditTaskScreen.kt` | 生产代码 | 139 | 0 | 2 | 3 |
| 11 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/data/Task.kt` | 生产代码 | 14 | 1 | 0 | 3 |
| 12 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/TodoNavGraph.kt` | 生产代码 | 98 | 0 | 1 | 3 |
| 13 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/TodoNavigation.kt` | 生产代码 | 63 | 4 | 4 | 3 |
| 14 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/TodoService.kt` | 生产代码 | 18 | 1 | 3 | 3 |
| 15 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/util/SimpleCountingIdlingResource.kt` | 生产代码 | 24 | 1 | 5 | 3 |
| 16 | `shared-test/src/main/java/com/example/android/architecture/blueprints/todoapp/data/source/local/FakeTaskDao.kt` | 共享测试支持 | 48 | 1 | 10 | 3 |
| 17 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/data/ModelMappingExt.kt` | 生产代码 | 40 | 0 | 12 | 2 |
| 18 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/statistics/StatisticsScreen.kt` | 生产代码 | 108 | 0 | 4 | 2 |
| 19 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/statistics/StatisticsUtils.kt` | 生产代码 | 15 | 1 | 1 | 2 |
| 20 | `app/src/main/java/com/example/android/architecture/blueprints/todoapp/TodoApplication.kt` | 生产代码 | 12 | 1 | 1 | 2 |

完整逐文件数据见 `source_metrics_by_file.csv`。
