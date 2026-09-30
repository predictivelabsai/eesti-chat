from fasthtml.common import *


def about_page():
    return Div(
        Section(
            Div(
                H1('About eesti', Span('.chat', cls='text-brand'),
                   cls='font-display text-4xl font-extrabold text-black mb-4'),
                P('A conversational AI portal to Estonia and the e-Estonia digital society.',
                  cls='text-lg text-gray-500'),
                cls='max-w-7xl mx-auto relative z-10'
            ),
            cls='bg-white py-16 px-8'
        ),
        Section(
            Div(
                Div(
                    H2('What we do', cls='text-2xl font-medium text-black mb-4'),
                    P('eesti.chat is an AI "front door" to Estonia. Ask a question in plain language — about '
                      'e-Residency, starting a company, taxes, digital identity, moving to Estonia, or any public '
                      'service — and a specialist assistant answers, grounded in official Estonian sources and with '
                      'links so you can verify every step.',
                      cls='text-gray-500 text-sm leading-relaxed mb-6'),
                    H2('How it works', cls='text-2xl font-medium text-black mb-4'),
                    P('Instead of navigating dozens of agency websites, you describe what you need. Our router sends '
                      'your question to the right assistant, which searches live across official domains — eesti.ee, '
                      'ria.ee, emta.ee, e-resident.gov.ee, politsei.ee and more — reads the current guidance, and '
                      'returns a clear, cited answer. It is a conversational layer on top of Estonia’s mature '
                      'digital state: X-Road, e-ID, digital signatures, and the once-only principle.',
                      cls='text-gray-500 text-sm leading-relaxed mb-6'),
                    H2('Inspiration & credit', cls='text-2xl font-medium text-black mb-4'),
                    P('eesti.chat is inspired by ',
                      A('america.gov', href='https://www.america.gov', cls='text-brand no-underline hover:underline'),
                      ' — the U.S. government’s AI-powered services portal — and the U.S. State Department’s ',
                      A('ShareAmerica', href='https://share.america.gov', cls='text-brand no-underline hover:underline'),
                      ', reimagined for e-Estonia. We gratefully credit both as the model for a chat-first, '
                      'citizen-friendly gateway to government.',
                      cls='text-gray-500 text-sm leading-relaxed mb-6'),
                    H2('Technology', cls='text-2xl font-medium text-black mb-4'),
                    P('Built with FastHTML, LangGraph multi-agent orchestration, xAI Grok, and live Exa web search, '
                      'with content in English and Estonian (and more languages via the switcher).',
                      cls='text-gray-500 text-sm leading-relaxed mb-6'),
                    Div(
                        P('Disclaimer', cls='text-black font-medium text-sm mb-1'),
                        P('eesti.chat is an independent project and is not an official government service. Answers are '
                          'AI-generated from public sources and may be incomplete or out of date. Always confirm with '
                          'the official source before acting. This is not legal advice.',
                          cls='text-gray-500 text-xs leading-relaxed'),
                        cls='p-4 rounded-xl bg-brand-light border border-brand/20',
                    ),
                    cls='max-w-3xl mx-auto'
                ),
                cls='max-w-7xl mx-auto'
            ),
            cls='py-20 px-8 bg-gray-50'
        ),
    )
