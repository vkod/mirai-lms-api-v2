"""
Centralized async utility module to handle async operations 
in both sync and async contexts without event loop conflicts.
"""
import asyncio
import nest_asyncio
from typing import Any, Coroutine, TypeVar
import sys

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

T = TypeVar('T')

def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async function from a synchronous context.
    Handles the case where an event loop is already running (e.g., in FastAPI/Jupyter).
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're in an async context (loop is running), use nest_asyncio
        # Create a new task and run it
        return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop is running, we can use asyncio.run()
        return asyncio.run(coro)

async def run_async_from_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async function from an async context.
    This is a simple wrapper that just awaits the coroutine.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    return await coro

def is_async_context() -> bool:
    """
    Check if we're currently in an async context (event loop is running).
    
    Returns:
        True if an event loop is running, False otherwise
    """
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False