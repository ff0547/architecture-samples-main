package com.example.android.architecture.blueprints.todoapp

class TodoService(private val repository: TodoRepository) {

    fun loadTasks(): List<String> {
        return repository.getAllTasks()
    }

    fun addNewTask(task: String): Boolean {
        if (task.isBlank()) {
            return false
        }
        return repository.addTask(task)
    }

    fun deleteExistingTask(task: String): Boolean {
        if (task.isBlank()) {
            return false
        }
        return repository.deleteTask(task)
    }
}