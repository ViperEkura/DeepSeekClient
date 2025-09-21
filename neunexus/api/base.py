from flask import Flask, jsonify
from functools import wraps
from typing import Any, Callable



def handle_errors(func: Callable) -> Callable:
    """处理控制器方法错误的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if args and hasattr(args[0], 'app') and isinstance(args[0].app, Flask):
                args[0].app.logger.error(f"Error in {func.__name__}: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    return wrapper