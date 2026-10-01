"""
Unfold sidebar navigation.

This file is the "sidebar navigator per service" requirement. The schema
deliberately does not duplicate a model per service (BUILD_PROMPT.md design
note) -- the per-service reading of the admin comes from how this navigation
is grouped, not from six copies of the same table.

Phase 1 groups each service's existing shared content. Phase 2 will add
its distinct models and case-study proxies to these same groups.

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

SERVICE_GROUPS = [
    {
        "title": title,
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": "Overview",
                "icon": "widgets",
                "link": f"/admin/services/service/?key__exact={key}",
            },
            *[
                {
                    "title": label,
                    "icon": icon,
                    "link": f"/admin/services/{model}/?service__key__exact={key}",
                }
                for model, label, icon in (
                    ("serviceoffering", "Offerings", "view_agenda"),
                    ("processstep", "Process steps", "list_alt"),
                    ("faq", "FAQs", "help"),
                )
            ],
        ],
    }
    for key, title in (
        ("digital-marketing", "Digital Marketing"),
        ("ai-automation", "AI & Automation"),
        ("custom-software", "Custom Software"),
        ("web-development", "Web Development"),
        ("mobile-development", "Mobile Development"),
        ("cyber-security", "Cyber Security"),
    )
]

NAVIGATION = [SITE_GROUP, SERVICES_GROUP, *SERVICE_GROUPS, SYSTEM_GROUP]
