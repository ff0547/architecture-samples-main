package com.example.android.architecture.blueprints.todoapp

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class TodoListManagerTest {

    @Test
    fun addTask_validTask_shouldAddSuccessfully() {
        val manager = TodoListManager()

        val result = manager.addTask("Finish homework")

        assertTrue(result)
        assertEquals(1, manager.getTaskCount())
        assertTrue(manager.containsTask("Finish homework"))
    }

    @Test
    fun addTask_blankTask_shouldNotAdd() {
        val manager = TodoListManager()

        val result = manager.addTask("")

        assertFalse(result)
        assertEquals(0, manager.getTaskCount())
    }

    @Test
    fun removeTask_existingTask_shouldRemoveSuccessfully() {
        val manager = TodoListManager()
        manager.addTask("Task A")
        manager.addTask("Task B")

        val result = manager.removeTask("Task A")

        assertTrue(result)
        assertEquals(1, manager.getTaskCount())
        assertFalse(manager.containsTask("Task A"))
        assertTrue(manager.containsTask("Task B"))
    }

    @Test
    fun removeTask_nonExistingTask_shouldReturnFalse() {
        val manager = TodoListManager()
        manager.addTask("Task A")

        val result = manager.removeTask("Task B")

        assertFalse(result)
        assertEquals(1, manager.getTaskCount())
    }

    @Test
    fun updateTask_existingTask_shouldUpdateSuccessfully() {
        val manager = TodoListManager()
        manager.addTask("Old Task")

        val result = manager.updateTask("Old Task", "New Task")

        assertTrue(result)
        assertFalse(manager.containsTask("Old Task"))
        assertTrue(manager.containsTask("New Task"))
    }

    @Test
    fun updateTask_nonExistingTask_shouldReturnFalse() {
        val manager = TodoListManager()
        manager.addTask("Task A")

        val result = manager.updateTask("Task B", "Task C")

        assertFalse(result)
        assertEquals(1, manager.getTaskCount())
        assertTrue(manager.containsTask("Task A"))
    }

    @Test
    fun clearTasks_shouldRemoveAllTasks() {
        val manager = TodoListManager()
        manager.addTask("Task A")
        manager.addTask("Task B")

        manager.clearTasks()

        assertEquals(0, manager.getTaskCount())
        assertTrue(manager.getTasks().isEmpty())
    }
}