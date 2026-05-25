package com.example.android.architecture.blueprints.todoapp

import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class TodoServiceMockKTest {

    @Test
    fun loadTasks_repositoryReturnsTasks_shouldReturnTaskList() {
        val repository = mockk<TodoRepository>()

        every { repository.getAllTasks() } returns listOf("Task A", "Task B", "Task C")

        val service = TodoService(repository)
        val result = service.loadTasks()

        assertEquals(3, result.size)
        assertEquals("Task A", result[0])
        assertEquals("Task B", result[1])
        assertEquals("Task C", result[2])

        verify { repository.getAllTasks() }
    }

    @Test
    fun addNewTask_validTask_shouldCallRepository() {
        val repository = mockk<TodoRepository>()

        every { repository.addTask("New Task") } returns true

        val service = TodoService(repository)
        val result = service.addNewTask("New Task")

        assertTrue(result)

        verify { repository.addTask("New Task") }
    }

    @Test
    fun addNewTask_blankTask_shouldNotCallRepository() {
        val repository = mockk<TodoRepository>(relaxed = true)

        val service = TodoService(repository)
        val result = service.addNewTask("")

        assertFalse(result)

        verify(exactly = 0) { repository.addTask(any()) }
    }

    @Test
    fun deleteExistingTask_validTask_shouldCallRepository() {
        val repository = mockk<TodoRepository>()

        every { repository.deleteTask("Task A") } returns true

        val service = TodoService(repository)
        val result = service.deleteExistingTask("Task A")

        assertTrue(result)

        verify { repository.deleteTask("Task A") }
    }

    @Test
    fun deleteExistingTask_blankTask_shouldNotCallRepository() {
        val repository = mockk<TodoRepository>(relaxed = true)

        val service = TodoService(repository)
        val result = service.deleteExistingTask("")

        assertFalse(result)

        verify(exactly = 0) { repository.deleteTask(any()) }
    }
}