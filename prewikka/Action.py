import copy
import urllib

class Error(Exception):
    pass



class ActionInvalidError(Error):
    pass



class ActionParameterError(Error):
    pass


class ActionDeniedError(Error):
    pass


class ActionParameterInvalidError(ActionParameterError):
    def __init__(self, name):
        self._name = name
        
    def __str__(self):
        return "invalid parameter '%s'" % self._name



class ActionParameterInvalidTypeError(ActionParameterError):
    def __init__(self, name, value, required_type):
        self._name = name
        self._value = value
        self._required_type = required_type
        
    def __str__(self):
        return "invalid type %s for parameter '%s', %s required" % \
               (str(type(self._value)), self._name, str(self._required_type))



class ActionParameterMissingError(ActionParameterError):
    def __init__(self, name):
        self._name = name
        
    def __str__(self):
        return "parameter '%s' is missing" % self._name



class ActionParameterAlreadyRegisteredError(ActionParameterError):
    def __init__(self, name):
        self._name = name

    def __str__(self):
        return "parameter '%s' is already registered" % self._name



def get_action_name(action):
    if isinstance(action, Action):
        return action.getName()
    return "%s.%s.%s" % (action.im_func.__module__, action.im_class.__name__, action.im_func.__name__)



class RegisteredAction:
    def __init__(self, handler, parameters, capabilities):
        self.handler = handler
        self.parameters = parameters
        self.capabilities = capabilities
        self.name = get_action_name(handler)

    def __str__(self):
        return self.name



class ActionEngine:
    def __init__(self, log):
        self._log = log
        self._actions = { }
        self._default_action = None
        self._login_action = None
        
    def registerAction(self, handler, parameters, capabilities, default=False):
        registered = RegisteredAction(handler, parameters, capabilities)
        self._actions[registered.name] = registered
        
        if default:
            self._default_action = registered

        return registered
        
    def registerLoginAction(self, handler, parameters):
        self._login_action = self.registerAction(handler, parameters, [ ])
        
    def getLoginAction(self):
        return self._login_action

    def getRegisteredActionFromName(self, action_name):
        if not action_name:
            return self._default_action
        
        try:
            return self._actions[action_name]
        except KeyError:
            self._log.event(Log.EVENT_INVALID_ACTION, request, action_name)
            raise ActionInvalidError

    def _execute(self, core, handler, parameters, request):
        if isinstance(handler, Action):
            return handler.process(core, parameters, request)
        return handler(core, parameters, request)

    def process(self, core, registered, arguments, request):
        if request.user:
            required = registered.capabilities
            if filter(lambda cap: request.user.hasCapability(cap), required) != required:
                self._log.event(Log.EVENT_ACTION_DENIED, request, registered.name)
                raise ActionDeniedError

        handler = registered.handler
        parameters = registered.parameters()

        try:
            parameters.populate(arguments)
            parameters.check()
        except ActionParameterError, e:
            self._log.event(Log.EVENT_INVALID_ACTION_PARAMETERS, request, str(e))
            raise

        return self._execute(core, handler, parameters, request)

    def processDefaultAction(self, core, request):
        return self.process(core, self._default_action, { }, request)
    


class Action(object):
    def process(self, core, parameters):
        pass
    
    def getName(self):
        return self.__module__ + "." + self.__class__.__name__



class ActionParameters:
    def __init__(self, parameters=None):
        self._parameters = { }
        self._values = { }
        self.register()
        if parameters:
            for name in self._parameters.keys():
                if parameters.hasParameter(name):
                    self[name] = parameters[name]
        
    def register(self):
        pass
    
    def registerParameter(self, name, type):
        if self._parameters.has_key(name):
            raise ActionParameterAlreadyRegisteredError(name)
        
        self._parameters[name] = type
        
    def __setitem__(self, name, value):
        try:
            parameter_type = self._parameters[name]
        except KeyError:
            raise ActionParameterInvalidError(name)
        
        if parameter_type is list and not type(value) is list:
            value = [ value ]
            
        try:
            value = parameter_type(value)
        except ValueError:
            raise ActionParameterInvalidTypeError(name, value, parameter_type)
        
        self._values[name] = value
        
    def __getitem__(self, name):
        return self._values[name]

    def __delitem__(self, name):
        del self._values[name]

    def get(self, name, default_value=None):
        return self._values.get(name, default_value)

    def hasParameter(self, name):
        return self._values.has_key(name)

    def populate(self, query):
        for name, value in query.items():
            self[name] = value
        
    def check(self):
        return True

    def getNames(self, ignore=[]):
        return filter(lambda name: not name in ignore, self._values.keys())

    def items(self):
        return self._values.items()

    def debug(self):
        content = ""
        for key, value in self._values.items():
            content += "%s: %s\n" % (key, value)
        
        return content

    def __str__(self):
        return urllib.urlencode(self._values)

    def __copy__(self):
        new = self.__class__()
        new._parameters = copy.copy(self._parameters)
        new._values = copy.copy(self._values)
        
        return new
