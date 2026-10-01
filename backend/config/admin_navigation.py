"""
Unfold sidebar navigation.

This file is the "sidebar navigator per service" requirement. The schema
deliberately does not duplicate a model per service (BUILD_PROMPT.md design
note) -- the per-service reading of the admin comes from how this navigation
is grouped, not from six copies of the same table.

Service groups combine shared content with dedicated models and case-study proxies.

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
        {
            "title": "Translation log",
            "icon": "translate",
            "link": "/admin/translations/translationlog/",
        },
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


def group(title, items):
    return {
        "title": title,
        "separator": True,
        "collapsible": True,
        "items": [
            {"title": label, "icon": icon, "link": f"/admin/{path}/"} for path, label, icon in items
        ],
    }


PRODUCTS_GROUP = group(
    "Products",
    [
        ("products/product", "All products", "inventory_2"),
        ("products/productfeature", "Features", "list_alt"),
        ("products/productimage", "Gallery", "photo_library"),
    ],
)
MEDIA_GROUP = group("Media", [("core/video", "Videos", "videocam")])
CONTENT_GROUP = group(
    "Content",
    [
        ("blog/post", "Blog posts", "article"),
        ("blog/category", "Categories", "category"),
        ("blog/tag", "Tags", "label"),
        ("portfolio/casestudy", "All case studies", "work"),
    ],
)
LEADS_GROUP = group(
    "Leads",
    [
        ("crm/lead", "Leads", "contact_mail"),
        ("crm/newslettersubscriber", "Newsletter", "mail"),
    ],
)
SERVICE_MODELS = [
    (
        "digital_marketing",
        "digitalmarketingcasestudy",
        [
            ("campaign", "Campaigns"),
            ("creativework", "Creative work"),
            ("socialchannel", "Social channels"),
        ],
    ),
    (
        "ai_automation",
        "aiautomationcasestudy",
        [
            ("automationusecase", "Use cases"),
            ("agenttype", "Agent types"),
            ("integration", "Integrations"),
        ],
    ),
    (
        "custom_software",
        "customsoftwarecasestudy",
        [("systemtype", "System types"), ("databasecapability", "Database capabilities")],
    ),
    ("web_development", "webdevelopmentcasestudy", [("webcapability", "Capabilities")]),
    ("mobile_development", "mobiledevelopmentcasestudy", [("mobileapp", "Apps")]),
    (
        "cyber_security",
        "cybersecuritycasestudy",
        [
            ("securityservice", "Security services"),
            ("compliancestandard", "Compliance"),
            ("certification", "Certifications"),
        ],
    ),
]
for service_group, (app, proxy, models) in zip(SERVICE_GROUPS, SERVICE_MODELS, strict=True):
    service_group["items"].extend(
        group(
            "",
            [(f"{app}/{model}", label, "view_list") for model, label in models]
            + [(f"{app}/{proxy}", "Case studies", "work")],
        )["items"]
    )

NAVIGATION = [
    {
        "title": "Dashboard",
        "items": [{"title": "Overview", "icon": "dashboard", "link": "/admin/"}],
    },
    SITE_GROUP,
    SERVICES_GROUP,
    PRODUCTS_GROUP,
    MEDIA_GROUP,
    *SERVICE_GROUPS,
    CONTENT_GROUP,
    LEADS_GROUP,
    SYSTEM_GROUP,
]
