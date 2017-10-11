class Database(object):
    def __init__(self,database,**connect_kwargs):
        self.connect_kwargs = {}
        self.init(database,**connect_kwargs)

    def init(self, database, **connect_kwargs):
        self.deferred = database is None
        self.database = database
        self.connect_kwargs.update(connect_kwargs)
        # print self.deferred
        print self.database

