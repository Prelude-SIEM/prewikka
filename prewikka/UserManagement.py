import sys

import time
import random
import md5

from prewikka import Log, Interface, Views
from prewikka.templates import LoginPasswordForm, PropertiesChange
from prewikka.templates import UserListing


class Error(Exception):
    pass


class SessionError(Error):
    pass


class LoginError(Error):
    pass


class PasswordError(Error):
    pass


class AuthError(Error):
    pass



CAPABILITY_READ_MESSAGE = "READ_MESSAGE"
CAPABILITY_DELETE_MESSAGE = "DELETE_MESSAGE"
CAPABILITY_USER_MANAGEMENT = "USER_MANAGEMENT"

CAPABILITIES = [ CAPABILITY_READ_MESSAGE, CAPABILITY_DELETE_MESSAGE, CAPABILITY_USER_MANAGEMENT ]
CAPABILITIES_ADMIN = CAPABILITIES


class LoginPasswordActionParameters(Interface.ActionParameters):
    def register(self):
        self.registerParameter("login", str)
        self.registerParameter("password", str)
        
    def getLogin(self):
        return self["login"]
    
    def getPassword(self):
        return self["password"]
    
    def check(self):
        return self.hasParameter("login") and self.hasParameter("password")



class CapabilityActionParameters:
    def register(self):
        for capability in CAPABILITIES:
            self.registerParameter(capability, str)
        
    def can(self, capability):
        return self.hasParameter(capability)
    
    def getCapabilities(self):
        return filter(lambda cap: self.can(cap), CAPABILITIES)
    
    def check(self):
        for capability in CAPABILITIES:
            if self.hasParameter(capability) and self[capability] != "on":
                raise Interface.ActionParameterInvalidError(capability)

            

class AddUserActionParameters(Interface.ActionParameters, CapabilityActionParameters):
    def register(self):
        CapabilityActionParameters.register(self)
        self.registerParameter("login", str)
        self.registerParameter("password1", str)
        self.registerParameter("password2", str)
        
    def getLogin(self):
        return self["login"]

    def getPassword(self):
        return self["password1"]
    
    def check(self):
        CapabilityActionParameters.check(self)
        for parameter in "login", "password1", "password2":
            if not self.hasParameter(parameter):
                raise Interface.ActionParameterMissingError(parameter)
            



class UserActionParameters(Interface.ActionParameters):
    def register(self):
        self.registerParameter("id", int)
        
    def getID(self):
        return self["id"]
    
    def setID(self, id):
        self["id"] = id
        
    def check(self):
        if not self.hasParameter("id"):
            raise Interface.ActionParameterMissingError("id")



class ChangePasswordActionParameters(UserActionParameters):
    def register(self):
        UserActionParameters.register(self)
        self.registerParameter("password1", str)
        self.registerParameter("password2", str)
        
    def getPassword(self):
        return self["password1"]
        
    def check(self):
        UserActionParameters.check(self)
        for parameter in "password1", "password2":
            if not self.hasParameter(parameter):
                raise Interface.ActionParameterMissingError(parameter)



class ChangeCapabilitiesActionParameters(UserActionParameters, CapabilityActionParameters):
    def register(self):
        UserActionParameters.register(self)
        CapabilityActionParameters.register(self)
        
    def check(self):
        UserActionParameters.check(self)
        CapabilityActionParameters.check(self)



def template(name):
    return getattr(__import__("prewikka/templates/" + name), name)



class LoginPasswordPromptView(template("LoginPasswordForm")):
    def __init__(self, core, login_action):
        template("LoginPasswordForm").__init__(self, core)
        self.login_action = Interface.get_action_name(login_action)



class UsersView(Interface.ConfigView):
    active_tab = "Users"



class UserListingView(UsersView, template("UserListing")):
    def __init__(self, core, add_user_action, delete_user_action, change_password_action, change_capabilities_action):
        UsersView.__init__(self, core)
        template("UserListing").__init__(self, core)
        self.users = [ ]
        self.add_form_hiddens = self.createAccess(add_user_action)
        self._delete_user_action = delete_user_action
        self._change_password_action = change_password_action
        self._change_capabilities_action = change_capabilities_action
        self.capabilities = CAPABILITIES

    def createAccess(self, action, parameters=[]):
        return [("action", Interface.get_action_name(action))] + parameters

    def addUser(self, user):
        parameters = [("id", user.getID())]
        new = { }
        new["id"] = user.getID()
        new["login"] = user.getLogin()
        new["capabilities"] = map(lambda cap: user.hasCapability(cap), CAPABILITIES)
        new["delete_form_hiddens"] = self.createAccess(self._delete_user_action, parameters)
        new["password_form_hiddens"] = self.createAccess(self._change_password_action, parameters)
        new["capabilities_form_hiddens"] = self.createAccess(self._change_capabilities_action, parameters)
        self.users.append(new)



class UserAddForm(UsersView, Views.PropertiesChangeView):
    def __init__(self, core, action):
        UsersView.__init__(self, core)
        Views.PropertiesChangeView.__init__(self, core, "add", action)
        self.addTextProperty("Login", "login")
        self.addPasswordProperty("Password", "password1")
        self.addPasswordProperty("Password confirmation", "password2")
        for capability in CAPABILITIES:
            self.addBooleanProperty(capability, capability)
        


class ChangePasswordForm(UsersView, Views.PropertiesChangeView):
    def __init__(self, core, id, action):
        UsersView.__init__(self, core)
        Views.PropertiesChangeView.__init__(self, core, "change", action)
        self.addHidden("id", id)
        self.addPasswordProperty("Password", "password1")
        self.addPasswordProperty("Password confirmation", "password2")



class ChangeCapabilitiesForm(UsersView, Views.PropertiesChangeView):
    def __init__(self, core, user, action):
        UsersView.__init__(self, core)
        Views.PropertiesChangeView.__init__(self, core, "change", action)
        self.addHidden("id", user.getID())
        for cap in CAPABILITIES:
            self.addBooleanProperty(cap, cap, user.hasCapability(cap))



class User:
    def canReadMessage(self, value=None):
        return self.hasCapability(CAPABILITY_READ_MESSAGE)
    
    def canDeleteMessage(self, value=None):
        return self.hasCapability(CAPABILITY_DELETE_MESSAGE)
    
    def canManageUser(self, value=None):
        return self.hasCapability(CAPABILITY_USER_MANAGEMENT)
    
    def __str__(self):
        content = ""
        content += "id: %s\n" % self.getID()
        content += "login: %s\n" % self.getLogin()
        content += "password: %s\n" % self.getPassword()
        content += "sessions: %s\n" % str(self.sessions)
        content += "can read message: %s\n" % self.canReadMessage()
        content += "can delete message: %s\n" % self.canDeleteMessage()
        
        return content
    


class UserManagement:
    def __init__(self, core, config):
        self.core = core
        self._use_ssl = config.getOptionValue("use_ssl", "") in ("yes", "true", "on")
        self._expiration = int(config.getOptionValue("expiration", 30))
        self.core.interface.registerLoginAction(self.login, LoginPasswordActionParameters)
        self.core.interface.registerConfigurationSection("Users", self.handle_user_listing)
        self.core.interface.registerAction(self.handle_user_listing, Interface.ActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.interface.registerAction(self.handle_user_add_form, Interface.ActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.interface.registerAction(self.handle_user_add, AddUserActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.interface.registerAction(self.handle_change_password_form, UserActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.interface.registerAction(self.handle_change_password, ChangePasswordActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.interface.registerAction(self.handle_change_capabilities_form, UserActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.interface.registerAction(self.handle_change_capabilities, ChangeCapabilitiesActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.interface.registerAction(self.handle_user_delete, UserActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.interface.registerSpecialAction("logout", self.handle_user_logout, None)
        self.core.interface.registerAction(self.handle_user_logout, Interface.ActionParameters, [ ])
        
    def enableSSL(self):
        self._use_ssl = True
        
    def disableSSL(self):
        self._use_ssl = False
        
    def isSSLenabled(self):
        return self._use_ssl
    
    def setExpiration(self, expiration):
        self._expiration = expiration
        
    def _checkSSL(self, request):
        pass # TODO
    
    def redirectToLogin(self):
        return LoginPasswordPromptView(self.core, self.login)
    
    def _checkSession(self, request):
        if request.input_cookie.has_key("sessionid"):
            try:
                sessionid = request.input_cookie["sessionid"].value
                user = self.getUserBySessionID(sessionid)
            except SessionError:
                # TODO: log invalid sessions
                return self.redirectToLogin()
            if time.time() - user.getSessionTime(sessionid) < self._expiration * 60:
                request.user = user
                return
            
            user.removeSession(sessionid)
            user.save()
            
        return self.redirectToLogin()
    
    def check(self, request):
        if self._use_ssl:
            self._checkSSL()
        else:
            return self._checkSession(request)
        
    def login(self, core, parameters, request):
        login = parameters.getLogin()
        password = parameters.getPassword()
        
        try:
            user = self.getUserByLogin(login)
        except LoginError:
            core.log.event(Log.EVENT_BAD_LOGIN, request, login)
            raise AuthError
        
        try:
            user.checkPassword(password)
        except PasswordError:
            core.log.event(Log.EVENT_BAD_PASSWORD, request, login, password)
            raise AuthError
        
        t = int(time.time())
        sessionid = md5.new(str(t * random.random())).hexdigest()
        user.addSession(sessionid, t)
        user.save()
        
        request.output_cookie["sessionid"] = sessionid
        request.user = user
        
        core.log.event(Log.EVENT_LOGIN_SUCCESSFUL, request, user)
        
        return self.core.interface.forwardToDefaultAction(core, request)
    
    def handle_user_listing(self, core, parameters, request):
        ids = self.getUsers()
        ids.sort()
        view = UserListingView(core,
                               self.handle_user_add_form,
                               self.handle_user_delete,
                               self.handle_change_password_form,
                               self.handle_change_capabilities_form)
        for id in ids:
            user = self.getUserByID(id)
            view.addUser(user)

        return view
        
    
    def handle_user_add_form(self, core, parameters, request):
        return UserAddForm(core, self.handle_user_add)
    
    def handle_user_add(self, core, parameters, request):
        user = self.newUser()
        user.setLogin(parameters.getLogin())
        user.setPassword(parameters.getPassword())
        user.setCapabilities(parameters.getCapabilities())
        user.save()
        
        return self.handle_user_listing(core, Interface.ActionParameters(), request)
        
    def handle_user_delete(self, core, parameters, request):
        self.removeUser(parameters.getID())
        
        return self.handle_user_listing(core, Interface.ActionParameters(), request)
    
    def handle_change_password_form(self, core, parameters, request):
        return ChangePasswordForm(core, parameters.getID(), self.handle_change_password)
    
    def handle_change_password(self, core, parameters, request):
        user = self.getUserByID(parameters.getID())
        user.setPassword(parameters.getPassword())
        user.save()
        
        return self.handle_user_listing(core, Interface.ActionParameters(), request)
    
    def handle_change_capabilities_form(self, core, parameters, request):
        return ChangeCapabilitiesForm(core, self.getUserByID(parameters.getID()), self.handle_change_capabilities)
    
    def handle_change_capabilities(self, core, parameters, request):
        user = self.getUserByID(parameters.getID())
        user.setCapabilities(parameters.getCapabilities())
        user.save()
        
        return self.handle_user_listing(core, Interface.ActionParameters(), request)

    def handle_user_logout(self, core, parameters, request):
        request.user.removeSession(request.input_cookie["sessionid"].value)
        request.user.save()

        core.log.event(Log.EVENT_LOGOUT, request, request.user)
        
        return LoginPasswordPromptView(core, self.login)
