class Singleton(type):
    def __init__(cls, name, bases, dictionary):
        super(Singleton, cls).__init__(name, bases, dictionary)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args)

        return cls.instance
