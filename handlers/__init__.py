from .commands import router as commands_router
from .callbacks import router as callbacks_router
from .registration import router as registration_router

routers = [commands_router, callbacks_router, registration_router]

__all__ = ['routers']
