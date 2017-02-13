
import logging
import plugin_support as plugins

log = logging.getLogger("lib.meta")


class _Singleton(type):
    """
    The first instance created will load the plugins, if
    provided some paths.  see Proctor.__init__
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            inst = super(_Singleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = inst
            inst.load_plugins()
        return cls._instances[cls]


class HandlerRegistry(object):
    """
    Hold the collection of registered handlers
    """
    __metaclass__ = _Singleton

    def __init__(self, plugin_paths, client, bot_name, bot_id):
        self.plugin_dirs = plugin_paths if plugin_paths else []
        self.__handlers = {}
        self.__slack_client = client
        self.__bot_name = bot_name
        self.__bot_id = bot_id
        
    """
    Methods that deal with Chomps Plugins
    """
    def load_plugins(self):
        """Load all the directories"""
        for path in self.plugin_dirs:
            self.load_plugins_from(path)

    def load_plugins_from(self, dirname):
        """Loads plugins from a directory"""
        try:
            if plugins.load(dirname):
                log.info(u"Successfully loaded plugins from {}".format(dirname))
        except Exception as e:
            log.exception(u"Failed to load extensions at {}. {}".format(dirname, e.message))

    def add_module(self, name):
        """Load a module that contains conditions and detectors"""
        log.debug(u"Adding module {}".format(name))
        plugins.load_module(name)

    def add_paths(self, paths):
        """Appends the plugin path after loading"""
        for path in paths:
            if path not in self.plugin_dirs:
                self.load_plugins_from(path)
            self.plugin_dirs.append(path)

    """
    Interactions with the registry to add handlers
    """
    def add(self, handler, name):
        log.debug("Adding {} - {}".format(handler, name))
        if name not in self.__handlers:
            try:
                self.__handlers[name] = {
                    "klass": handler,
                    "obj": handler(self.__slack_client, self.__bot_name, self.__bot_id)
                }
            except:
                log.exception("Plugin {} not loaded - SKIPPING".format(name))

    def __iter__(self):
        for name, handler in self.__handlers.iteritems():
            yield handler['obj']


class ChompsHandlerMeta(type):
    """
    Performs the registration with HandlerRegistry
    """
    def __init__(cls, name, bases, attrs):
        if name != "ChompsHandler":
            HandlerRegistry().add(cls, name)


class ChompsHandler(object):
    __metaclass__ = ChompsHandlerMeta

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
            log.debug("Handler call_limit is 0 {}".format(self.__class__.__name__))
        return self._call_limit

    def process_message(self, match, msg):
        raise NotImplementedError("No processor defined")

