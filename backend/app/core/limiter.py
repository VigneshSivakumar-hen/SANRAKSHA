"""Shared slowapi Limiter instance.

Kept in its own module (rather than defined in main.py) so route modules
can import it without creating a circular import with app.main, which in
turn imports the route modules.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
