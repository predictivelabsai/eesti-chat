"""Central registry of all eesti.chat specialist assistants."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentSpec:
    slug: str
    name: str
    category: str
    icon: str
    one_liner: str
    description: str
    prefix: str
    example_prompts: tuple[str, ...] = field(default_factory=tuple)


CATEGORIES: list[dict] = [
    {
        "key": "business",
        "name": "e-Residency & Business",
        "blurb": "Apply for e-Residency and start or run an EU company remotely.",
        "icon": "€",
    },
    {
        "key": "living",
        "name": "Living in Estonia",
        "blurb": "Moving, residence, taxes, and everyday public services.",
        "icon": "⌂",
    },
    {
        "key": "digital",
        "name": "Digital Society",
        "blurb": "e-ID, digital signatures, and the e-Estonia infrastructure.",
        "icon": "#",
    },
    {
        "key": "discover",
        "name": "Discover Estonia",
        "blurb": "The e-Estonia story, culture, and why Estonia.",
        "icon": "★",
    },
]


AGENTS: tuple[AgentSpec, ...] = (
    # Business
    AgentSpec(
        slug="eresidency", name="e-Residency & Company",
        category="business", icon="€", prefix="business:",
        one_liner="Apply for e-Residency and start or run an EU company from anywhere.",
        description=(
            "Helps applicants and e-residents understand and use Estonian e-Residency: eligibility, "
            "the application and its fees, collecting the digital ID, and then starting and running an "
            "EU company remotely — company registration, business banking, invoicing, and annual reports. "
            "Grounds every answer in official sources such as e-resident.gov.ee, rik.ee (Company "
            "Registration Portal) and emta.ee (Tax and Customs Board)."
        ),
        example_prompts=(
            "business: how do I apply for e-Residency and what does it cost?",
            "business: steps to register a private limited company (OÜ) online",
            "business: can I open a business bank account as an e-resident?",
            "business: what are my annual reporting duties for an Estonian OÜ?",
        ),
    ),
    # Living
    AgentSpec(
        slug="moving", name="Living & Moving",
        category="living", icon="⌂", prefix="move:",
        one_liner="Residence permits, visas, registering your address, and settling in.",
        description=(
            "Guides people moving to or living in Estonia: visas and residence permits (work, study, "
            "family, digital nomad visa), registering your place of residence, the personal ID code, "
            "and practical settling-in steps. Grounds answers in official sources such as politsei.ee "
            "(Police and Border Guard Board) and eesti.ee."
        ),
        example_prompts=(
            "move: how do I get a residence permit to work in Estonia?",
            "move: what is the digital nomad visa and who qualifies?",
            "move: how do I register my address after moving to Tallinn?",
            "move: how do I get an Estonian personal identification code?",
        ),
    ),
    AgentSpec(
        slug="tax", name="Taxes & Finance",
        category="living", icon="%", prefix="tax:",
        one_liner="Income tax, VAT, and filing through the e-Tax Board.",
        description=(
            "Explains Estonian taxation for individuals and companies: income tax, the corporate "
            "distributed-profit model, VAT registration and rates, social tax, and how to declare "
            "and pay through the e-Tax Board (e-MTA). Grounds answers in official sources, primarily "
            "emta.ee (Tax and Customs Board)."
        ),
        example_prompts=(
            "tax: how does Estonia's corporate income tax on distributed profits work?",
            "tax: when do I have to register my company for VAT?",
            "tax: how do I file my personal income tax return in the e-Tax Board?",
            "tax: what taxes does a sole proprietor (FIE) pay?",
        ),
    ),
    AgentSpec(
        slug="services", name="Public Services",
        category="living", icon="+", prefix="gov:",
        one_liner="Health, education, family benefits, voting, and everyday state services.",
        description=(
            "Helps residents use everyday Estonian public services: healthcare and the health insurance "
            "system, education and schools, family and parental benefits, pensions, voting (including "
            "i-voting), and documents like the ID card and passport. Grounds answers in official sources "
            "such as eesti.ee, tervisekassa.ee and the relevant agencies."
        ),
        example_prompts=(
            "gov: how do I renew my Estonian ID card?",
            "gov: how does health insurance work for residents?",
            "gov: what family benefits can new parents claim?",
            "gov: how does online voting (i-voting) work in Estonia?",
        ),
    ),
    # Digital
    AgentSpec(
        slug="digital", name="Digital ID & e-Services",
        category="digital", icon="#", prefix="id:",
        one_liner="e-ID, Smart-ID, Mobiil-ID, digital signatures, and X-Tee.",
        description=(
            "Explains Estonia's digital identity and e-service infrastructure: the e-ID / ID card, "
            "Smart-ID and Mobiil-ID, giving legally binding digital signatures, logging into state "
            "e-services, and how X-Tee and the once-only principle connect it all. Grounds answers in "
            "official sources such as ria.ee (Information System Authority), id.ee and e-estonia.com."
        ),
        example_prompts=(
            "id: how do I set up Smart-ID or Mobiil-ID?",
            "id: how do I digitally sign a document and is it legally binding?",
            "id: what is X-Tee and how does it protect my data?",
            "id: how do I log in to state e-services from abroad?",
        ),
    ),
    # Discover
    AgentSpec(
        slug="explore", name="Discover Estonia",
        category="discover", icon="★", prefix="estonia:",
        one_liner="The e-Estonia story, digital society, culture, and why Estonia.",
        description=(
            "A friendly explainer for an international audience: the e-Estonia story and how the world's "
            "most advanced digital society came to be, plus culture, history, innovation, and reasons to "
            "visit, study, invest, or become an e-resident. Grounds answers in reputable sources such as "
            "e-estonia.com and official tourism and government pages."
        ),
        example_prompts=(
            "estonia: what makes Estonia the world's most advanced digital society?",
            "estonia: give me a short intro to Estonian history and culture",
            "estonia: why do startups and investors choose Estonia?",
            "estonia: what should I see on a first visit to Tallinn?",
        ),
    ),
)

AGENTS_BY_SLUG: dict[str, AgentSpec] = {a.slug: a for a in AGENTS}


def by_slug(slug: str) -> AgentSpec | None:
    return AGENTS_BY_SLUG.get(slug)
