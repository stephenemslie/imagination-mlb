
import os
import environ


class Env(environ.Env):

    def __init__(self, secrets_path, *args, **kwargs):
        self.secrets_path = secrets_path
        super().__init__(*args, **kwargs)

    def get_value(self, value, **kwargs):
        path = os.path.join(self.secrets_path, value)
        if os.path.exists(path):
            return open(path).read()
        return super().get_value(value, **kwargs)
