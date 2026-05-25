package com.example.android.architecture.blueprints.todoapp

import android.app.Application
import android.os.Build
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(
    sdk = [23],
    manifest = Config.NONE,
    application = Application::class
)
class MainActivityRobolectricTest {

    @Test
    fun robolectricEnvironment_isAvailable() {
        assertEquals(23, Build.VERSION.SDK_INT)
    }
}