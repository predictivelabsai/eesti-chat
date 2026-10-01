from fasthtml.common import *
from utils.i18n import t, LANGUAGES, get_lang, DEFAULT_LANG
from utils.i18n_flags import flag_svg
from utils.brand import Icon, Mark, Wordmark, brand_head


def app_styles():
    return (
        Meta(charset='utf-8'),
        *brand_head(),
        Style("""
        @font-face {
          font-family: 'AinoHeadline';
          src: url('/static/fonts/AinoWeb-Headline.woff2') format('woff2'),
               url('/static/fonts/AinoWeb-Headline.woff') format('woff');
          font-weight: 400 800;
          font-style: normal;
          font-display: swap;
        }
        @font-face {
          font-family: 'Aino';
          src: url('/static/fonts/Aino-Regular.woff2') format('woff2'),
               url('/static/fonts/Aino-Regular.woff') format('woff');
          font-weight: 400;
          font-style: normal;
          font-display: swap;
        }
        @font-face {
          font-family: 'Aino';
          src: url('/static/fonts/Aino-Bold.woff2') format('woff2'),
               url('/static/fonts/Aino-Bold.woff') format('woff');
          font-weight: 700;
          font-style: normal;
          font-display: swap;
        }
        @font-face {
          font-family: 'Aino';
          src: url('/static/fonts/AinoWeb-Italic.woff2') format('woff2'),
               url('/static/fonts/AinoWeb-Italic.woff') format('woff');
          font-weight: 400;
          font-style: italic;
          font-display: swap;
        }
        """),
        Meta(name='color-scheme', content='light'),
        Meta(name='viewport', content='width=device-width, initial-scale=1'),
        Link(rel='stylesheet', href='/static/tw.css'),
        Link(rel='stylesheet', href='/static/app.css?v=16'),
    )


def _lang_switcher(lang: str = "en"):
    current = LANGUAGES.get(lang, LANGUAGES["en"])
    current_code = lang.upper() if lang in LANGUAGES else "EN"
    options = []
    for code, info in LANGUAGES.items():
        active_cls = ' font-semibold text-ink' if code == lang else ''
        options.append(
            A(Span(NotStr(flag_svg(code)), cls='mr-2 lang-dd-flag'), Span(info["native"], cls='text-xs'),
              href=f'/set-lang/{code}',
              cls=f'lang-option flex items-center gap-1 px-3 py-1.5 text-sm text-ink-3 hover:bg-bg-alt hover:text-blue transition-colors no-underline{active_cls}')
        )
    return Div(
        Button(
               Span(NotStr(flag_svg(current_code.lower())), cls='lang-trigger-flag'),
               Span(current_code, cls='lang-trigger-code'),
               NotStr('<svg class="lang-trigger-chevron" aria-hidden="true" width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m2 3.5 3 3 3-3"/></svg>'),
               type='button',
               cls='lang-trigger',
               aria_haspopup='true', aria_expanded='false',
               onclick="this.nextElementSibling.classList.toggle('hidden'); this.setAttribute('aria-expanded', this.nextElementSibling.classList.contains('hidden') ? 'false' : 'true')"),
        Div(*options,
            cls='hidden absolute right-0 top-full mt-1 bg-white border border-line rounded shadow-sm z-50 py-1 min-w-[130px] flex flex-col'),
        cls='relative',
    )


def NavBar(active='home', sess=None):
    from utils.config import settings
    login_enabled = settings().login_enabled
    lang = get_lang(sess or {})

    nav_items = [
        ('home', '/', t('nav_home', lang)),
        ('advisory', '/app', t('nav_ask', lang)),
        ('topics', '/#topics', t('nav_topics', lang)),
        ('about', '/about', t('nav_about', lang)),
        ('contact', '/contact', t('nav_contact', lang)),
    ]

    def nav_link(key, href, label, drawer=False):
        link_cls = 'public-nav-drawer-link' if drawer else 'public-nav-link'
        if key == active:
            link_cls += ' active'
        return A(label, href=href, cls=link_cls)

    nav_links = [Li(nav_link(k, h, l)) for k, h, l in nav_items]
    drawer_links = [nav_link(k, h, l, drawer=True) for k, h, l in nav_items]

    cta = A(t('nav_open_app', lang), href='/app',
            cls='public-nav-cta')

    return Nav(
        Div(
            Wordmark('/', cls='shrink-0', mark_size=30),
            Ul(*nav_links, cls='hidden lg:flex items-center gap-6 list-none m-0 p-0'),
            Div(
                _lang_switcher(lang),
                Button(
                    Icon('menu', 22),
                    type='button', cls='nav-burger', aria_expanded='false', aria_label='Open menu',
                    onclick="var d=document.getElementById('nav-drawer'); d.classList.toggle('open'); this.setAttribute('aria-expanded', d.classList.contains('open'))",
                ),
                cta,
                cls='public-nav-actions flex items-center gap-3',
            ),
            Div(
                *drawer_links,
                A(t('nav_open_app', lang), href='/app',
                  cls='public-nav-cta public-nav-cta-full'),
                id='nav-drawer', cls='public-nav-drawer',
            ),
            cls='max-w-7xl mx-auto px-5 flex items-center justify-between h-16 gap-4',
        ),
        Script("""document.addEventListener('click', function(e) {
            var dd = e.target.closest('.relative');
            document.querySelectorAll('.relative > div').forEach(function(d) {
                if (d.parentElement !== dd) d.classList.add('hidden');
            });
        });"""),
        cls='public-nav',
        style='display:block',
    )


def PageFooter(lang: str = "en"):
    from fasthtml.components import Footer as FooterTag
    return FooterTag(
        Div(
            Div(
                Div(
                    Wordmark(tag=H3, cls='footer-wordmark', mark_size=38),
                    P(t('footer_desc', lang),
                      cls='footer-desc'),
                ),
                Div(
                    H4(t('footer_platform', lang), cls='footer-heading'),
                    Ul(
                        Li(A(t('nav_ask', lang), href='/app', cls='footer-link'), cls='mb-2'),
                        Li(A(t('nav_topics', lang), href='/#topics', cls='footer-link'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                Div(
                    H4(t('footer_resources', lang), cls='footer-heading'),
                    Ul(
                        Li(A(t('nav_about', lang), href='/about', cls='footer-link'), cls='mb-2'),
                        Li(A(t('nav_contact', lang), href='/contact', cls='footer-link'), cls='mb-2'),
                        Li(A('eesti.ee', href='https://www.eesti.ee', target='_blank', rel='noopener noreferrer', cls='footer-link'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                Div(
                    H4(t('footer_legal', lang), cls='footer-heading'),
                    Ul(
                        Li(A(t('footer_privacy', lang), href='/privacy', cls='footer-link'), cls='mb-2'),
                        Li(A('Delete account', href='/delete-account', cls='footer-link'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                cls='max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12'
            ),
            Div(
                P(t('footer_copyright', lang), cls='footer-meta'),
                P(t('footer_disclaimer', lang), cls='footer-meta'),
                cls='max-w-7xl mx-auto mt-12 pt-8 border-t border-line flex flex-col md:flex-row justify-between items-center text-sm gap-4'
            ),
        ),
        cls='public-footer'
    )


def Page(content, active='home', title='', sess=None):
    lang = get_lang(sess or {})
    return (
        A('Skip to main content', href='#main-content', cls='skip-link'),
        Title(f'{title} | eesti.chat · AI portal for Estonia') if title else Title('eesti.chat · AI portal for Estonia'),
        NavBar(active, sess=sess),
        Main(content, id='main-content', cls='public-page'),
        PageFooter(lang=lang),
        AskBubble(lang),
        Script("""
(function() {
    var bubble = document.querySelector('.ask-bubble');
    if (!bubble || document.querySelector('.home-page .hero-prompt-form')) return;
    function updateAskBubble() {
        var hero = document.querySelector('.home-hero');
        var threshold = hero
            ? hero.getBoundingClientRect().bottom + window.scrollY
            : 480;
        bubble.classList.toggle('visible', window.scrollY > threshold);
    }
    updateAskBubble();
    window.addEventListener('scroll', updateAskBubble, { passive: true });
    window.addEventListener('resize', updateAskBubble);
})();
"""),
    )


def AskBubble(lang: str = "en"):
    return Div(
        Form(
            Label(
                t('chat_placeholder', lang),
                **{'for': 'ask-bubble-input'},
                cls='visually-hidden',
            ),
            Mark(20, cls='ask-bubble-mark'),
            Input(
                type='search',
                name='q',
                id='ask-bubble-input',
                placeholder=t('chat_placeholder', lang),
                autocomplete='off',
                cls='ask-bubble-input',
            ),
            Button(
                Icon('arrow-right', 18),
                type='submit',
                title=t('hero_cta_start', lang),
                aria_label=t('hero_cta_start', lang),
                cls='ask-bubble-submit',
            ),
            action='/app',
            method='get',
            role='search',
            aria_label=t('chat_welcome_title', lang),
            cls='ask-bubble-form',
        ),
        cls='ask-bubble',
    )
