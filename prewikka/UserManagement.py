import sys

import time
import random
import md5

from prewikka import Log, Action, DataSet
from prewikka.templates import LoginPasswordForm, PropertiesChangeForm
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


class LoginPasswordActionParameters(Action.ActionParameters):
    def register(self):
        self.registerParameter("login", str, required=True)
        self.registerParameter("password", str, required=True)
        
    def getLogin(self):
        return self["login"]
    
    def getPassword(self):
        return self["password"]



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
                raise Action.ActionParameterInvalidError(capability)



class AddUserActionParameters(Action.ActionParameters, CapabilityActionParameters):
    def register(self):
        CapabilityActionParameters.register(self)
        self.registerParameter("login", str, required=True)
        self.registerParameter("password1", str, required=True)
        self.registerParameter("password2", str, required=True)
        
    def getLogin(self):
        return self["login"]

    def getPassword(self):
        return self["password1"]
    
    def check(self):
        Action.ActionParameters.check(self)
        CapabilityActionParameters.check(self)



class UserActionParameters(Action.ActionParameters):
    def register(self):
        self.registerParameter("id", int, required=True)
        
    def getID(self):
        return self["id"]
    
    def setID(self, id):
        self["id"] = id



class ChangePasswordActionParameters(UserActionParameters):
    def register(self):
        UserActionParameters.register(self)
        self.registerParameter("password1", str, required=True)
        self.registerParameter("password2", str, required=True)
        
    def getPassword(self):
        return self["password1"]
        
    def check(self):
        UserActionParameters.check(self)
        if self["password1"] != self["password2"]:
            raise Action.ActionParameterError



class ChangeCapabilitiesActionParameters(UserActionParameters, CapabilityActionParameters):
    def register(self):
        UserActionParameters.register(self)
        CapabilityActionParameters.register(self)
        
    def check(self):
        UserActionParameters.check(self)
        CapabilityActionParameters.check(self)



class LoginPasswordPromptView(DataSet.BaseDataSet, LoginPasswordForm.LoginPasswordForm):
    def __init__(self, login_action):
        DataSet.BaseDataSet.__init__(self)
        LoginPasswordForm.LoginPasswordForm.__init__(self)
        self.login_action = Action.get_action_name(login_action)



class UsersDataSet(DataSet.ConfigDataSet):
    active_tab = "Users"



class UserListingView(UsersDataSet, UserListing.UserListing):
    def __init__(self, add_user_action, delete_user_action, change_password_action, change_capabilities_action):
        UsersDataSet.__init__(self)
        UserListing.UserListing.__init__(self)
        self.users = [ ]
        self.add_form_hiddens = self.createAccess(add_user_action)
        self._delete_user_action = delete_user_action
        self._change_password_action = change_password_action
        self._change_capabilities_action = change_capabilities_action
        self.capabilities = CAPABILITIES

    def createAccess(self, action, parameters=[]):
        return [("action", Action.get_action_name(action))] + parameters

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



class UserAddForm(UsersDataSet, DataSet.PropertiesChangeDataSet, PropertiesChangeForm.PropertiesChangeForm):
    def __init__(self, action):
        UsersDataSet.__init__(self)
        DataSet.PropertiesChangeDataSet.__init__(self, "add", action)
        PropertiesChangeForm.PropertiesChangeForm.__init__(self)
        self.addTextProperty("Login", "login")
        self.addPasswordProperty("Password", "password1")
        self.addPasswordProperty("Password confirmation", "password2")
        for capability in CAPABILITIES:
            self.addBooleanProperty(capability, capability)



class ChangePasswordForm(UsersDataSet, DataSet.PropertiesChangeDataSet, PropertiesChangeForm.PropertiesChangeForm):
    def __init__(self, id, action):
        UsersDataSet.__init__(self)
        DataSet.PropertiesChangeDataSet.__init__(self, "change", action)
        PropertiesChangeForm.PropertiesChangeForm.__init__(self)
        self.addHidden("id", id)
        self.addPasswordProperty("Password", "password1")
        self.addPasswordProperty("Password confirmation", "password2")



class ChangeCapabilitiesForm(UsersDataSet, DataSet.PropertiesChangeDataSet, PropertiesChangeForm.PropertiesChangeForm):
    def __init__(self, user, action):
        UsersDataSet.__init__(self)
        DataSet.PropertiesChangeDataSet.__init__(self, "change", action)
        PropertiesChangeForm.PropertiesChangeForm.__init__(self)
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
        self.core.interface.registerConfigurationSection("Users", self.handle_user_listing)
        self.core.interface.registerQuickAccessor("logout", self.handle_user_logout, None)
        self.core.action_engine.registerLoginAction(self.login, LoginPasswordActionParameters)
        self.core.action_engine.registerAction(self.handle_user_listing, Action.ActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.action_engine.registerAction(self.handle_user_add_form, Action.ActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.action_engine.registerAction(self.handle_user_add, AddUserActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.action_engine.registerAction(self.handle_change_password_form, UserActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.action_engine.registerAction(self.handle_change_password, ChangePasswordActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.action_engine.registerAction(self.handle_change_capabilities_form, UserActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.action_engine.registerAction(self.handle_change_capabilities, ChangeCapabilitiesActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.action_engine.registerAction(self.handle_user_delete, UserActionParameters, [ CAPABILITY_USER_MANAGEMENT ])
        self.core.action_engine.registerAction(self.handle_user_logout, Action.ActionParameters, [ ])
        
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
        return LoginPasswordPromptView(self.login)
    
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
        
    def login(self, request):
        login = request.parameters.getLogin()
        password = request.parameters.getPassword()
        
        try:
            user = self.getUserByLogin(login)
        except LoginError:
            request.log(Log.EVENT_BAD_LOGIN, request, login)
            raise AuthError
        
        try:
            user.checkPassword(password)
        except PasswordError:
            request.log(Log.EVENT_BAD_PASSWORD, request, login, password)
            raise AuthError
        
        t = int(time.time())
        sessionid = md5.new(str(t * random.random())).hexdigest()
        user.addSession(sessionid, t)
        user.save()
        
        request.output_cookie["sessionid"] = sessionid
        request.user = user
        
        request.log(Log.EVENT_LOGIN_SUCCESSFUL, request, user)
        
        return request.action_engine.processDefaultAction(request)
    
    def handle_user_listing(self, request):
        ids = self.getUsers()
        ids.sort()
        view = UserListingView(self.handle_user_add_form,
                               self.handle_user_delete,
                               self.handle_change_password_form,
                               self.handle_change_capabilities_form)
        for id in ids:
            user = self.getUserByID(id)
            view.addUser(user)

        return view
        
    
    def handle_user_add_form(self, request):
        return UserAddForm(self.handle_user_add)
    
    def handle_user_add(self, request):
        user = self.newUser()
        user.setLogin(request.parameters.getLogin())
        user.setPassword(request.parameters.getPassword())
        user.setCapabilities(request.parameters.getCapabilities())
        user.save()

        request.parameters = Action.ActionParameters()
        
        return self.handle_user_listing(request)
        
    def handle_user_delete(self, request):
        self.removeUser(request.parameters.getID())

        request.parameters = Action.ActionParameters()
        
        return self.handle_user_listing(request)
    
    def handle_change_password_form(self, request):
        return ChangePasswordForm(request.parameters.getID(), self.handle_change_password)
    
    def handle_change_password(self, request):
        user = self.getUserByID(request.parameters.getID())
        user.setPassword(request.parameters.getPassword())
        user.save()

        request.parameters = Action.ActionParameters()
        
        return self.handle_user_listing(request)
    
    def handle_change_capabilities_form(self, request):
        return ChangeCapabilitiesForm(self.getUserByID(request.parameters.getID()), self.handle_change_capabilities)
    
    def handle_change_capabilities(self, request):
        user = self.getUserByID(request.parameters.getID())
        user.setCapabilities(request.parameters.getCapabilities())
        user.save()

        request.parameters = Action.ActionParameters()
        
        return self.handle_user_listing(request)

    def handle_user_logout(self, request):
        request.user.removeSession(request.input_cookie["sessionid"].value)
        request.user.save()

        request.log(Log.EVENT_LOGOUT, request, request.user)
        
        return LoginPasswordPromptView(self.login)
