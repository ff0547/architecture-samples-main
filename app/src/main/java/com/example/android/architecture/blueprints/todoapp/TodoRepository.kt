package com.example.android.architecture.blueprints.todoapp

interface TodoRepository {
    fun getAllTasks(): List<String>
    fun addTask(task: String): Boolean
    fun deleteTask(task: String): Boolean
}