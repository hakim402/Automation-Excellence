"""
Unfold sidebar navigation.

This file is the "sidebar navigator per service" requirement. The schema
deliberately does not duplicate a model per service (BUILD_PROMPT.md design
note) -- the per-service reading of the admin comes from how this navigation
is grouped, not from six copies of the same table.

Groups are added as their models land. Phase 1 ships Site, Services and
System; the six per-service groups arrive in Phase 2 with the models that
make them non-empty (campaigns, agent types, case-study proxies, and so on).

Links are written as literal admin paths rather than reverse_lazy, because
reverse_lazy on a model that does not exist yet fails at render time rather
than at import, which is a confusing way to find out a group is premature.
"""

SITE_GROUP = {
    "title": "Site",
    "separator": True,
    "collapsible": False,
    "items": [
        {"title": "Site settings", "icon": "settings", "link": "/admin/core/sitesettings/"},
        {"title": "Team", "icon": "badge", "link": "/admin/core/teammember/"},
        {"title": "Testimonials", "icon": "format_quote", "link": "/admin/core/testimonial/"},
        {"title": "Tools", "icon": "build", "link": "/admin/core/tool/"},
        {"title": "Industries", "icon": "domain", "link": "/admin/core/industry/"},
        {"title": "Stats", "icon": "trending_up", "link": "/admin/core/stat/"},
    ],
}

SERVICES_GROUP = {
    "title": "Services",
    "separator": True,
    "collapsible": False,
    "items": [
        {"title": "All services", "icon": "widgets", "link": "/admin/services/service/"},
        {"title": "Offerings", "icon": "view_agenda", "link": "/admin/services/serviceoffering/"},
        {"title": "Process steps", "icon": "list_alt", "link": "/admin/services/processstep/"},
        {"title": "FAQs", "icon": "help", "link": "/admin/services/faq/"},
    ],
}

SYSTEM_GROUP = {
    "title": "System",
    "separator": True,
    "collapsible": True,
    "items": [
        {"title": "Users", "icon": "person", "link": "/admin/auth/user/"},
        {"title": "Groups", "icon": "group", "link": "/admin/auth/group/"},
    ],
}

NAVIGATION = [SITE_GROUP, SERVICES_GROUP, SYSTEM_GROUP]
