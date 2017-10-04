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

    def allow_relation(self, obj1, obj2, **hints):
        return True
