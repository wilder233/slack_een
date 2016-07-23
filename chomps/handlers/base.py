class BotHandler(object):

    def __init__(self, client, bot_name, bot_id):
        self.client = client
        self.bot_name = bot_name
        self.bot_id = bot_id
        self._call_limit = 1

    @property
    def pattern(self):
        raise NotImplementedError("No pattern defined")

    @property
    def call_limit(self):
        """Limit per slack message"""
        if not self._call_limit:
            print "Handler call_limit is 0 {}".format(self.__class__.__name__)
        return self._call_limit

    def process_message(self, match, msg):
        raise NotImplementedError("No processor defined")