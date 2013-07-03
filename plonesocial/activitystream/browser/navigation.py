from zope.interface import implements
from zope.viewlet.interfaces import IViewlet
from zope.publisher.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getMultiAdapter

from plonesocial.activitystream.integration import PLONESOCIAL


class PloneSocialNavigation(BrowserView):
    """Provide toplevel navigation that spans plonesocial.activitystream
    and plonesocial.network.
    """
    implements(IViewlet)

    def __init__(self, context, request, view, manager):
        self.context = context
        self.request = request
        self.view = self.__parent__ = view
        self.manager = manager

    def update(self):
        pass

    render = ViewPageTemplateFile("templates/navigation.pt")

    def portal_url(self):
        portal_state = getMultiAdapter(
            (self.context, self.request),
            name=u'plone_portal_state')
        return portal_state.portal_url()

    def items(self):
        menu = [dict(url='@@stream',
                     title='Explore',
                     state='')]
        if PLONESOCIAL.network:
            menu.extend([dict(url='@@stream/network',
                              title='My network',
                              state=''),
                         dict(url='@@profile',
                              title='My profile',
                              state='')])
        for item in menu:
            fullurl = "/".join((self.portal_url(), item['url']))
            if self.request.URL.endswith(fullurl):
                item['state'] = 'active'
        return menu
