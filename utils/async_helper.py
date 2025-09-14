"""
Centralized async utility module to handle async operations 
in both sync and async contexts without event loop conflicts.
"""
import asyncio
from typing import Any, Coroutine, TypeVar
import sys

T = TypeVar('T')

def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async function from a synchronous context.
    NOTE: This will fail if called from within an already running event loop.
    Use await directly in async contexts instead.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        # Check if an event loop is already running
        asyncio.get_running_loop()
        # If we reach here, we're in an async context
        raise RuntimeError(
            "Cannot use run_async() from within an async context. "
            "Use 'await' directly instead."
        )
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