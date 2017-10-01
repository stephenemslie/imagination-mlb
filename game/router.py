class GameRouter:
    """
    A router to control all database operations on models in the
    Game application.
    """

    def db_for_read(self, model, **hints):
        """
        Reads go to the default db, which should be local.
        """
        return None

    def db_for_write(self, model, **hints):
        """
        Writes go to the nuc.
        """
        return 'nuc'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure migrations only occur on the nuc.
        """
        return db == 'nuc'
