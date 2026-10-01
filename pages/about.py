from fasthtml.common import *


def about_page():
    return Div(
        Section(
            Div(
                H1('About eesti', Span('.chat', cls='wordmark-suffix'),
                   cls='public-page-title'),
                P('A conversational AI portal for Estonia and its digital society.',
                  cls='public-page-intro'),
                cls='portal-container public-hero-content'
            ),
            cls='public-page-hero'
        ),
        Section(
            Div(
                Div(
                    H2('What we do', cls='public-subtitle'),
                    P('eesti.chat is an AI "front door" to Estonia. Ask a question in plain language about '
                      'e-Residency, starting a company, taxes, digital identity, moving to Estonia, or any public '
                      'service. A specialist assistant answers from official Estonian sources and provides links '
                      'so you can verify each step.',
                      cls='public-paragraph'),
                    H2('How it works', cls='public-subtitle'),
                    P('You describe what you need instead of navigating dozens of agency websites. Our router sends '
                      'your question to the right assistant. It searches official domains in real time, including '
                      'eesti.ee, ria.ee, emta.ee, e-resident.gov.ee, politsei.ee and more, reads the current '
                      'guidance, and returns a clear answer with citations. eesti.chat adds a conversational layer '
                      'to Estonia\'s mature digital state: X-Road, e-ID, digital signatures, and the once-only '
                      'principle.',
                      cls='public-paragraph'),
                    H2('Technology', cls='public-subtitle'),
                    P('Built with FastHTML, LangGraph multi-agent orchestration, xAI Grok, and live Exa web search. '
                      'Content is available in English and Estonian, with more languages via the switcher.',
                      cls='public-paragraph'),
                    Div(
                        P('Disclaimer', cls='callout-title'),
                        P('eesti.chat is an independent project, not an official government service. Answers are '
                          'AI-generated from public sources and may be incomplete or out of date. Always confirm '
                          'details with the official source before acting. This is not legal advice.',
                          cls='callout-copy'),
                        cls='public-callout',
                    ),
                    cls='public-reading-column'
                ),
                cls='portal-container'
            ),
            cls='public-section public-section-alt'
        ),
    )
