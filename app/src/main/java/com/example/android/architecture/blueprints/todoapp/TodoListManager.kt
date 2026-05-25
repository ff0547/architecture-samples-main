package com.example.android.architecture.blueprints.todoapp

class TodoListManager {

    private val tasks = mutableListOf<String>()

    fun addTask(task: String): Boolean {
        if (task.isBlank()) {
            return false
        }
        tasks.add(task)
        return true
    }

    fun removeTask(task: String): Boolean {
        return tasks.remove(task)
    }

    fun updateTask(oldTask: String, newTask: String): Boolean {
        val index = tasks.indexOf(oldTask)
        return if (index != -1 && newTask.isNotBlank()) {
            tasks[index] = newTask
            true
        } else {
            false
        }
    }

    fun clearTasks() {
        tasks.clear()
    }

    fun getTasks(): List<String> {
        return tasks
    }

    fun getTaskCount(): Int {
        return tasks.size
    }

    fun containsTask(task: String): Boolean {
        return tasks.contains(task)
    }
}