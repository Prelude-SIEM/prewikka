import sys

import time
import random
import md5

from prewikka import Interface, Views
from prewikka.templates import LoginPasswordForm, Table, PropertiesChange
from prewikka.templates import UserListing


class Error(Exception):
    pass


class SessionError(Error):
    pass


class AuthError(Error):
    pass


class LoginError(Error):
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
        


class LoginPasswordPromptView(Views.TopView):
    def build(self, action):
        action_name = Interface.get_action_name(action)
        Views.TopView.build(self, str(LoginPasswordForm.LoginPasswordForm(action_name)))



class UsersView(Interface.OnlineConfigView):
    def __init__(self, core):
        Interface.OnlineConfigView.__init__(self, core)
        self.setActiveTab("Users")



class UserListingView(UsersView):
    def createButton(self, name, action, id):
        return \
               """<form action='?' method='POST'><input type='hidden' name='action' value='%s'/><input type='hidden' name='id' value='%d'/><input type='submit' value='%s'/></form>""" % (Interface.get_action_name(action), id, name)
    
    def buildMainContent(self, user_management):
        table = Table.Table()
        table.setHeader(["Id", "Login"] + CAPABILITIES + [ "" ] * 3)
        ids = user_management.getUsers()
        ids.sort()
        for id in ids:
            user = user_management.getUserByID(id)
            row = [ user.getID(), user.getLogin() ]
            row += map(lambda cap: ("", "x")[user.hasCapability(cap)], CAPABILITIES)
            row.append(self.createButton("delete", user_management.handle_user_delete, user.getID()))
            row.append(self.createButton("password", user_management.handle_change_password_form, user.getID()))
            row.append(self.createButton("capabilities", user_management.handle_change_capabilities_form, user.getID()))
            table.addRow(row)
            
        return str(UserListing.UserListing(str(table), Interface.get_action_name(user_management.handle_user_add_form)))



class UserAddForm(UsersView):
    def buildMainContent(self, action):
        template = PropertiesChange.PropertiesChange()
        template.addHiddenEntry("action", Interface.get_action_name(action))
        template.addTextEntry("Login", "login")
        template.addPasswordEntry("Password", "password1")
        template.addPasswordEntry("Password confirmation", "password2")
        for capability in CAPABILITIES:
            template.addCheckboxEntry(capability, capability)
        template.setButtonLabel("add")
        
        return str(template)



class ChangePasswordForm(UsersView):
    def buildMainContent(self, data):
        template = PropertiesChange.PropertiesChange()
        template.addHiddenEntry("action", Interface.get_action_name(data["action"]))
        template.addHiddenEntry("id", data["id"])
        template.addPasswordEntry("Password", "password1")
        template.addPasswordEntry("Password confirmation", "password2")
        template.setButtonLabel("change")

        return str(template)


class ChangeCapabilitiesForm(UsersView):
    def buildMainContent(self, data):
        template = PropertiesChange.PropertiesChange()
        template.addHiddenEntry("action", Interface.get_action_name(data["action"]))
        user = data["user"]
        template.addHiddenEntry("id", user.getID())
        for capability in CAPABILITIES:
            template.addCheckboxEntry(capability, capability, user.hasCapability(capability))
        template.setButtonLabel("change")
        
        return str(template)



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
        self._use_ssl = config.get("use_ssl", "") in ("yes", "true", "on")
        self._expiration = int(config.get("expiration", 30))
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
        view = LoginPasswordPromptView(self.core)
        view.build(self.login)
        return str(view)
    
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
        user = self.getUserByLogin(parameters.getLogin())
        user.checkPassword(parameters.getPassword())
        t = int(time.time())
        sessionid = md5.new(str(t * random.random())).hexdigest()
        user.addSession(sessionid, t)
        user.save()
        
        request.output_cookie["sessionid"] = sessionid
        request.user = user
        
        return self.core.interface.forwardToDefaultAction(core, request)
    
    def handle_user_listing(self, core, parameters, request):
        return UserListingView, self
    
    def handle_user_add_form(self, core, parameters, request):
        return UserAddForm, self.handle_user_add
    
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
        return ChangePasswordForm, { "action": self.handle_change_password, "id": parameters.getID() }
    
    def handle_change_password(self, core, parameters, request):
        user = self.getUserByID(parameters.getID())
        user.setPassword(parameters.getPassword())
        user.save()
        
        return self.handle_user_listing(core, Interface.ActionParameters(), request)
    
    def handle_change_capabilities_form(self, core, parameters, request):
        return ChangeCapabilitiesForm, { "action": self.handle_change_capabilities, "user": self.getUserByID(parameters.getID()) }
    
    def handle_change_capabilities(self, core, parameters, request):
        user = self.getUserByID(parameters.getID())
        user.setCapabilities(parameters.getCapabilities())
        user.save()
        
        return self.handle_user_listing(core, Interface.ActionParameters(), request)

    def handle_user_logout(self, core, parameters, request):
        request.user.removeSession(request.input_cookie["sessionid"].value)
        request.user.save()
        
        return LoginPasswordPromptView, self.login
