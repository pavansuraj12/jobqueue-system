class Config:
    def __init__(self, storage):
        self.storage = storage
    
    def get(self, key, default=None):
        return self.storage.get_config(key, default)
    
    def set(self, key, value):
        self.storage.set_config(key, value)
    
    @property
    def max_retries(self):
        return int(self.get("max_retries", 3))
    
    @property
    def base_delay(self):
        return int(self.get("base_delay", 2))