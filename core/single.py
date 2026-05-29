from threading import Lock


# 线程安全的单例模式元类实现
class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """
    _instances = {}  # 类级别的字典，用于存储每个类的唯一实例
    _lock: Lock = Lock()  # 类级别的锁，用于确保线程安全

    # __call__ 方法：当类实例化时调用，用于创建新的实例
    def __call__(cls, *args, **kwargs):
        """
        使用 with cls._lock: 确保线程安全
        检查该类是否已经存在实例（cls not in cls._instances）
        如果不存在，则通过 super().__call__() 创建新实例并存储
        返回已存在的实例（确保始终只返回同一个实例）
        """
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]
