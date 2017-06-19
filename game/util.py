
import os
import environ


class Env(environ.Env):
    """A django-environ variant for docker secrets."""

    def __init__(self, secrets_path, *args, **kwargs):
        self.secrets_path = secrets_path
        super().__init__(*args, **kwargs)

    def get_value(self, value, **kwargs):
        """Return value for a given environment variable.
        
        Allow files in `secrets_path` to take priority over environment variables.
        """
        path = os.path.join(self.secrets_path, value)
        if os.path.exists(path):
            return open(path).read().rstrip()
        return super().get_value(value, **kwargs)
