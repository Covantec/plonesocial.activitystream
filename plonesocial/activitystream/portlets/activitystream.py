import itertools

from zope.interface import implements
from zope.component import queryUtility

from zope import schema
from zope.formlib import form
from Acquisition import aq_inner

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone import PloneMessageFactory as PMF
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter
from AccessControl import getSecurityManager

from plonesocial.microblog.interfaces import IMicroblogTool
from plonesocial.activitystream.interfaces import IActivity

from zope.i18nmessageid import MessageFactory
_ = MessageFactory('plonesocial.activitystream')


class IActivitystreamPortlet(IPortletDataProvider):
    """A portlet to render the activitystream.
    """

    title = schema.TextLine(title=PMF(u"Title"),
                            description=_(u"A title for this portlet"),
                            required=True,
                            default=u"Activity Stream")

    count = schema.Int(
        title=_(u"Number of updates to display"),
        description=_(u"Maximum number of updates to show"),
        required=True,
        default=5)

    compact = schema.Bool(title=_(u"Compact rendering"),
                          description=_(u"Hide portlet header and footer"),
                          default=True)

    show_microblog = schema.Bool(
        title=_(u"Show microblog"),
        description=_(u"Show microblog status updates"),
        default=True)

    show_content = schema.Bool(
        title=_(u"Show content creation"),
        description=_(u"Show creation of new content"),
        default=True)

    show_discussion = schema.Bool(
        title=_(u"Show discussion"),
        description=_(u"Show discussion replies"),
        default=True)


class Assignment(base.Assignment):
    implements(IActivitystreamPortlet)

    title = u""  # overrides readonly property method from base class

    def __init__(self,
                 title='Activity Stream',
                 count=5,
                 compact=True,
                 show_microblog=True,
                 show_content=True,
                 show_discussion=True):
        self.title = title
        self.count = count
        self.compact = compact
        self.show_microblog = show_microblog
        self.show_content = show_content
        self.show_discussion = show_discussion


class Renderer(base.Renderer):

    render = ViewPageTemplateFile('activitystream.pt')

    def __init__(self, context, request, view, manager, data):
        base.Renderer.__init__(self, context, request, view, manager, data)
        self.items = []

    @property
    def available(self):
        return True

    @property
    def compact(self):
        return self.data.compact

    @property
    def portal_url(self):
        context = aq_inner(self.context)
        portal_state = getMultiAdapter((context, self.request),
                                       name=u'plone_portal_state')
        return portal_state.portal_url()

    def update(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        results = []
        brains = catalog.searchResults(sort_on='effective',
                                       sort_order='reverse',
                                       sort_limit=self.data.count,
                                       )[:self.data.count]

        # Combine these brains with activities.
        container = queryUtility(IMicroblogTool)

        min_date = brains[-1].effective
        min_time = long(min_date.time)
        activities = container.values(min=min_time)[-self.data.count:]
        # Make it a list and reverse it.
        #activities = list(activities)
        #activities = activities.reverse()

        data = itertools.chain(brains, activities)

        def date_key(item):
            if hasattr(item, 'effective'):
                # catalog brain
                return item.effective
            # Activity
            return item.date

        data = sorted(data, key=date_key, reverse=True)
        data = data[:self.data.count]

        for item in data:
            results.append(IActivity(item))
        self.items = results

    def is_anonymous(self):
        portal_membership = getToolByName(self.context,
                                          'portal_membership',
                                          None)
        return portal_membership.isAnonymousUser()

    def can_review(self):
        """Returns true if current user has the 'Review comments' permission.
        """
        return getSecurityManager().checkPermission('Review comments',
                                                    aq_inner(self.context))


class AddForm(base.AddForm):
    form_fields = form.Fields(IActivitystreamPortlet)

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    form_fields = form.Fields(IActivitystreamPortlet)
