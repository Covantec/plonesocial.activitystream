from zope.interface import Interface
from zope.interface import implements
from zope.component import adapts
from zope.component import getMultiAdapter
try:
    from zope.component.hooks import getSite
except ImportError:
    from zope.app.component.hooks import getSite

from AccessControl import getSecurityManager

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from ploneintranet.activitystream.interfaces import IStatusActivity
from ploneintranet.microblog.interfaces import IStatusUpdate

from .interfaces import IPloneIntranetActivitystreamLayer
from .interfaces import IStatusConversationProvider
from .interfaces import IActivityProvider

from ploneintranet.core.integration import PLONEINTRANET

import logging

logger = logging.getLogger(__name__)


class StatusConversationProvider(object):
    """Render a thread of IStatusUpdates
    """
    implements(IStatusConversationProvider)
    adapts(IStatusUpdate, IPloneIntranetActivitystreamLayer, Interface)

    index = ViewPageTemplateFile("templates/statusconversation_provider.pt")

    def __init__(self, context, request, view):
        self.context = context
        self.request = request
        self.view = self.__parent__ = view
        # the first status of a conversation has thread_id==None
        self.thread_id = context.thread_id or context.id

    def update(self):
        pass

    def render(self):
        return self.index()

    __call__ = render

    def activities(self):
        container = PLONEINTRANET.microblog
        if not container:
            return []

        return [IStatusActivity(item) for item in
                container.thread_values(self.thread_id)]

    def activity_providers(self):
        for activity in self.activities():
            yield getMultiAdapter(
                (activity, self.request, self.view),
                IActivityProvider)

    def can_view(self, activity):
        """Returns true if current user has the 'View' permission.
        """
        sm = getSecurityManager()
        permission = "Plone Social: View Microblog Status Update"
        return sm.checkPermission(permission, self.context)

    def is_anonymous(self):
        portal_membership = getToolByName(getSite(),
                                          'portal_membership',
                                          None)
        return portal_membership.isAnonymousUser()
