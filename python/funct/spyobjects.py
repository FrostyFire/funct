import copy

def create_function_spy(return_values=[], reverse=True):
    """Creates a function that is capable of tracking how it is used"""
    
    class MethodRecorder(object):
        def __init__(self, output):
            self.__output = output
            self.__args = []
            self.__kwargs = []
            self.__count = 0

        def __get_called(self):
            return len(self.__args) > 0
        called = property(fget=__get_called, 
                doc="""Returns True if method was called, False if not""")

        def __get_args(self):
            return tuple(self.__args)
        args = property(fget=__get_args, 
                doc="""Returns tuple of all args method called with""")

        def __get_kwargs(self):
            return tuple(self.__kwargs)
        kwargs = property(fget=__get_kwargs, 
                doc="""Returns tuple of all kwargs method called with""")

        def __count(self):
            return self.__count
        count = property(fget=__count, 
                doc="""Returns number of times method was called""")

        def __call__(self, *args, **kwargs):
            self.__args.append(args)
            self.__kwargs.append(kwargs)
            self.__count += 1
            if len(self.__output) > 0:
                return_value = self.__output.pop()
                if callable(return_value):
                    return return_value(*args, **kwargs)
                return return_value
    
    if reverse:
        return_values.reverse()
    function_spy = MethodRecorder(return_values)
    return function_spy

def create_call_spy(return_values=[]):
    """
    Sets up a spy object that tracks any calls and args/kwargs
    made against it.

    To test whether a method was called use 
    the 'called' property on the method you're testing. 

    >>> spy.method_under_testing.called
    True

    args and kwargs are accessible as properties on the 
    methods as well.

    >>> spy.method_under_testing.args
    ((arg1, arg2), (arg1, arg2), (arg1, arg2))
    >>> spy.method_under_testing.kwargs
    ({'kwarg1': 'value1'}, {'kwarg1': 'value1'})
    
    @return_values (optional): list of objects to return with each call
        >>> spy = create_call_spy(['some data', 'some more data'])
        >>> spy.test_a_method('some args')
        'some data'
        >>> spy.test_another_method('some args')
        'some more data'

    """
    class CallSpy(object):
        def __init__(self, *args, **kwargs):
            self.__called = []
            self.__output = return_values
            self.__output.reverse()
            self.__items = {}

            init = create_function_spy([])
            setattr(self, '__init__', init)

        def __dir__(self):
            return self.__called

        def __getattr__(self, name):
            if name not in self.__called:
                self.__called.append(name)
                function_spy = create_function_spy(self.__output, reverse=False)
                setattr(self, name, function_spy)
            return getattr(self, name)

        def __call__(self, *args, **kwargs):
            if '__init__' not in self.__called:
                self.__called.append('__init__')
            self.__init__(*args, **kwargs)
            return self
        
        #FIXME: Everything from here down needs to be removed
        #as it strays from the intended purpose of a call spy
        def __setitem__(self, name, value):
            self.__items[name] = value

        def __getitem__(self, name):
            return self.__items[name]

        def __iter__(self):
            for key in self.__items.keys():
                yield key

    return CallSpy()

class WebServiceSpy(object):
    def __init__(self, cherrypy, json):
        self.__cherrypy = cherrypy
        self.__json = json
        self.__requested = {}
        self.__responses = []

    def __handle_requested(self, path):
        self.__cherrypy.response.headers['Content-Type'] = 'application/json'

        if path == '/requested/':
            return self.__json.dumps(self.__requested)

        requested = path[10:]
        try:
            return self.__json.dumps(self.__requested[requested])
        except KeyError:
            self.__cherrypy.response.status = 404
            return '%s was never accessed' % requested

    def __handle_responses(self, path):
        responses = self.__json.load(self.__cherrypy.request.body)
        self.__responses.extend(responses)

    def __store_current_request(self, path):
        body = None
        if self.__cherrypy.request.method != 'GET':
            body = self.__cherrypy.request.body.read()

        request_info = {
            'headers': self.__cherrypy.request.headers, 
            'method': self.__cherrypy.request.method, 
            'body': body, 
        }

        if path in self.__requested:
            self.__requested[path].append(request_info)
        else:
            self.__requested[path] = [request_info]

    def default(self, *args, **kwargs):
        path = self.__cherrypy.request.path_info

        #FIXME: should only respond to GETs
        if path[:11] == '/requested/':
            return self.__handle_requested(path)
        #FIXME: should only respond to POSTs
        elif path[:11] == '/responses/':
            self.__handle_responses(path)
        else:
            self.__store_current_request(path)

            if len(self.__responses) > 0:
                response = self.__responses.pop(0)

                #special case for headers
                if 'headers' in response:
                    self.__cherrypy.response.headers.update(response['headers'])
                    del response['headers']

                for attr in response:
                    if hasattr(self.__cherrypy.response, attr):
                        setattr(self.__cherrypy.response, attr, response[attr])
                return self.__cherrypy.response.body

    default.exposed = True

class LoggerSpy(object):
    SPY_METHODS = ['warn', 'debug', 'info', 'error', 'critical', 'fatal']

    def __init__(self):
        """
        Records log messages for verification during testing
        messages will be added to self.messages[method_name] as a list of messages logged
        """
        self.messages = {}

        def method_spy(spying_on):
            def log_method(message):
                self.messages[spying_on].append(message)
            return log_method

        for method in LoggerSpy.SPY_METHODS:
            self.messages[method] = []
            setattr(self, method, method_spy(method))

    def contains_log(self, log_method_name, message):
        """
        Returns True is ''message'' is contained in one of the log messages sent to ''log_method_name''
        """
        for log_message in self.messages.get(log_method_name, []):
            if message in log_message:
                return True

        return False

class MQClientSpy(object):
    """
    Builds a spy class of the messagequeueclient.Client class. Use
    MQClientSpy.get_mqclient_class to get the test double class.

    ''preload_messages'' is a list of messagequeueclient.Message instances,
        these will be returned by the test doubles fetch() in the order 
        passed in

    If an item in ''preload_messages'' is callable then it will be called 
    and return the results of the call. This is useful for generating
    exceptions.

    All arguments passed in are recorded and assigned to matching attributes on
    the MQClientSpy instance
    """

    def __init__(self, preload_messages={}):
        self.messages = preload_messages
        self.position = {}

        self.url = None
        self.connection_factory = None
        self.username = None
        self.password = None
        self.send_channel = []
        self.fetch_channel = []

        self._create_mqclient_class()
        self.__instantiated = False

    def _create_mqclient_class(self):
        parent = self
        class MQClient(object):
            def __init__(self, url, connection_factory, username=None, password=None):
                parent.url = url
                parent.connection_factory = connection_factory
                parent.username = username
                parent.password = password

            def __build_copy(self, message):
                message_copy = copy.deepcopy(message)
                message_copy.headers = message_copy.headers.copy()
                message_copy.body = message_copy.body.copy()
                return message_copy

            def send(self, channel, message):
                parent.send_channel.append(channel)

                if not parent.messages.has_key(channel):
                    parent.messages[channel] = []

                parent.messages[channel].append(self.__build_copy(message))

            def fetch(self, channel):
                parent.fetch_channel.append(channel)
                current_position = parent.position.get(channel, 0)
                if len(parent.messages) > 0 and current_position < len(parent.messages[channel]):
                    item = parent.messages[channel][current_position]
                    parent.position[channel] = parent.position.get(channel, 0) + 1

                    if callable(item):
                        return item()
                    elif item is None:
                        return item
                    else:
                        return self.__build_copy(item)

                return None
        self.client_class = MQClient

    def __check_and_set_instantiation(self):
        if self.__instantiated == True:
            raise RuntimeError, 'You can only get one copy of the test double per MQClientSpy instance'

        self.__instantiated = True

    def build_mqclient_class(self):
        self.__check_and_set_instantiation() 
        return self.client_class

    def build_mqclient_instance(self):
        self.__check_and_set_instantiation() 
        return self.client_class(None, None)
    
