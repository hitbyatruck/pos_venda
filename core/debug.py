"""
Enhanced debugging utilities
"""
import logging
import time
import functools

logger = logging.getLogger('pos_venda.debug')

def trace_function(func):
    """Decorator to trace function calls and execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.debug(f"TRACE: Entering {func.__name__}")
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.debug(f"TRACE: Exiting {func.__name__} (took {elapsed:.4f}s)")
        return result
    return wrapper

def log_db_queries():
    """Enable logging of database queries"""
    from django.db import connection

    queries = connection.queries
    total_time = sum(float(q['time']) for q in queries)

    for i, query in enumerate(queries):
        logger.debug(f"Query {i}: {query['sql']} ({query['time']}s)")

    logger.debug(f"Total queries: {len(queries)}, Total time: {total_time}s")
