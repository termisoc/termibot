class Test():
    def __init__(self, factory, config):
        factory.register_command('hello', self.hello_world)
        factory.register_filter(r'hello', self.hello_world)

    def hello_world(self, args):
        return 'hello, world'
