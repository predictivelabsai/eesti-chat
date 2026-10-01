from fasthtml.common import *
from fasthtml.common import NotStr
from utils.i18n import t, agent_t, get_lang
from chat.components import signin_overlay
from agents.registry import AGENTS_BY_SLUG
from utils.brand import Icon, Mark, AGENT_ICONS


def _stat(value, label):
    return Div(
        Span(value, cls='stat-value'),
        Span(label, cls='stat-label'),
        cls='stat-item',
    )


def _statement_parts(copy):
    parts = []
    for segment in copy.split('[['):
        if ']]' not in segment:
            parts.append(segment)
            continue
        accent, remainder = segment.split(']]', 1)
        parts.append(
            Span(
                accent,
                cls='statement-accent',
            )
        )
        if remainder:
            parts.append(remainder)
    return parts


def _feature_visual(kind):
    if kind == 'ask':
        return Div(
            Icon('chat', 88, cls='editorial-visual-icon', stroke=1.5),
            cls='editorial-visual editorial-visual-blue',
            aria_hidden='true',
        )
    if kind == 'stone':
        return Div(
            Mark(88, cls='editorial-mark'),
            cls='editorial-visual editorial-visual-blue',
            aria_hidden='true',
        )
    if kind == 'sources':
        return Div(
            Icon('source', 68, cls='editorial-visual-icon', stroke=1.5),
            cls='editorial-visual editorial-visual-ink',
            aria_hidden='true',
        )
    return Div(
        Mark(132, cls='editorial-mark editorial-mark-large'),
        cls='editorial-visual editorial-visual-blue',
        aria_hidden='true',
    )


def home_page(sess=None):
    lang = get_lang(sess or {})

    agents = ["eresidency", "moving", "tax", "digital", "services", "explore"]

    hero_chips = [
        A(
            agent_t(slug, 'name', lang),
            href=f"/app?q={AGENTS_BY_SLUG[slug].prefix.strip()}",
            cls='hero-chip',
        )
        for slug in agents
    ]

    hero = Section(
        Div(
            Div(
                Span(t('feat_estonia', lang), cls='hero-kicker'),
                H1(t('hero_h1', lang), cls='hero-title'),
                P(t('hero_h2', lang), cls='hero-subtitle'),
                P(t('hero_body', lang), cls='hero-copy'),
                Div(
                    Form(
                        Label(t('chat_placeholder', lang), **{'for': 'hero-prompt-input'}, cls='visually-hidden'),
                        Input(type='search', name='q', placeholder=t('chat_placeholder', lang),
                             autocomplete='off', id='hero-prompt-input', cls='hero-prompt-input'),
                        Button(
                            Icon('arrow-right', 20),
                            type='submit', cls='hero-prompt-submit', title=t('hero_cta_start', lang),
                            aria_label=t('hero_cta_start', lang),
                        ),
                        action='/app', method='get', role='search', cls='hero-prompt-form',
                    ),
                    cls='hero-prompt-slot',
                ),
                Div(*hero_chips, cls='hero-chips'),
                Div(
                    A(
                        Span(t('hero_cta_start', lang)), Icon('arrow-right', 16),
                        href='/app', cls='hero-action hero-action-primary',
                    ),
                    A(
                        Span(t('hero_cta_explore', lang)), Icon('arrow-right', 16),
                        href='#topics', cls='hero-action hero-action-secondary',
                    ),
                    cls='hero-actions',
                ),
                cls='home-hero-content',
            ),
            cls='home-hero-inner',
        ),
        cls='home-hero',
    )

    statement = Section(
        Div(
            H2(*_statement_parts(t('home_statement', lang)), cls='statement-copy'),
            cls='portal-container statement-inner',
        ),
        cls='statement-section',
    )

    stats = Div(
        Div(_stat('99%', t('stat_services', lang)),
            _stat('2001', t('stat_xroad', lang)),
            _stat('2014', t('stat_eres', lang)),
            _stat('~2%', t('stat_signatures', lang)),
            cls='portal-container stats-grid'),
        cls='stats-band',
    )

    feature_rows = [
        ('ask', 'editorial-row', t('how_01_title', lang), t('feat_ask', lang),
         t('feat_ask_body', lang), t('feat_ask_link', lang), '/app'),
        ('sources', 'editorial-row-reverse', t('how_03_title', lang), t('feat_sources', lang),
         t('feat_sources_body', lang), t('feat_sources_link', lang), '#how'),
        ('estonia', 'editorial-row', t('feat_estonia_link', lang), t('feat_estonia', lang),
         t('feat_estonia_body', lang), t('feat_estonia_link', lang), '/about'),
    ]

    features = Section(
        Div(
            H2('Why eesti.chat', cls='visually-hidden'),
            Div(
                *[Article(
                    _feature_visual(kind),
                    Div(
                        Span(eyebrow, cls='editorial-eyebrow'),
                        H3(title, cls='editorial-title'),
                        P(body, cls='editorial-copy'),
                        A(Span(link), Icon('arrow-right', 16), href=href, cls='editorial-link'),
                        cls='editorial-copy-column',
                    ),
                    cls=f'editorial-row-shell {direction}',
                ) for kind, direction, eyebrow, title, body, link, href in feature_rows],
                cls='editorial-list',
            ),
            cls='portal-container',
        ),
        cls='public-section feature-section',
    )

    agent_cards = [
        A(
            Span(Icon(AGENT_ICONS[slug], 28), cls='agent-card-icon'),
            Div(agent_t(slug, 'name', lang), cls='agent-card-title'),
            P(agent_t(slug, 'one_liner', lang), cls='agent-card-copy'),
            href=f"/app?q={AGENTS_BY_SLUG[slug].prefix.strip()}",
            cls='portal-card agent-card',
        )
        for slug in agents
    ]

    agents_section = Section(
        Div(
            Span(t('topics_title', lang), cls='section-label-blue'),
            H2(t('topics_subtitle', lang), cls='section-title'),
            Div(*agent_cards, cls='agent-grid'),
            cls='portal-container',
        ),
        id='topics',
        cls='public-section public-section-alt scroll-mt-16',
    )

    how = Section(
        Div(
            Span(t('how_02_title', lang), cls='section-label-blue'),
            H2(t('how_title', lang), cls='section-title'),
            Div(
                *[Article(
                    P(num, cls='step-number'),
                    Div(
                        H3(title, cls='step-title'),
                        P(body, cls='step-copy'),
                        cls='step-content',
                    ),
                    cls='step-row',
                ) for num, title, body in [
                    ('01', t('how_01_title', lang), t('how_01_body', lang)),
                    ('02', t('how_02_title', lang), t('how_02_body', lang)),
                    ('03', t('how_03_title', lang), t('how_03_body', lang)),
                ]],
                cls='steps-list',
            ),
            cls='portal-container',
        ),
        id='how',
        cls='public-section public-section-white scroll-mt-16',
    )

    cta = Section(
        Div(
            H2(t('cta_headline', lang), cls='section-title cta-title'),
            P(t('cta_body', lang), cls='cta-copy'),
            A(
                Span(t('hero_cta_start', lang)), Icon('arrow-right', 16),
                href='/app', cls='public-button public-button-primary',
            ),
            cls='portal-container cta-inner',
        ),
        cls='public-section cta-section',
    )

    auth_modal = signin_overlay(lang)

    auth_js = Script(NotStr("""
function switchAuthTab(tab) {
    document.getElementById('auth-form-login').style.display = tab === 'login' ? '' : 'none';
    document.getElementById('auth-form-register').style.display = tab === 'register' ? '' : 'none';
    document.getElementById('auth-form-forgot').style.display = tab === 'forgot' ? '' : 'none';
    document.querySelectorAll('.auth-tab').forEach(function(t) { t.classList.remove('active'); });
    var tabEl = document.getElementById('auth-tab-' + tab);
    if (tabEl) tabEl.classList.add('active');
}
function showForgotPassword(e) { e && e.preventDefault(); switchAuthTab('forgot'); }
function showSignIn() {
    var overlay = document.getElementById('signin-overlay');
    overlay.classList.add('visible');
    switchAuthTab('login');
    var first = Array.from(overlay.querySelectorAll('.auth-panel input')).find(function(input) { return input.offsetParent !== null; });
    if (first) first.focus();
}
async function doLogin() {
    var email = document.getElementById('login-email').value.trim();
    var password = document.getElementById('login-password').value;
    var errEl = document.getElementById('login-error');
    errEl.textContent = '';
    if (!email || !password) { errEl.textContent = 'Enter your email and password'; return; }
    var resp = await fetch('/auth/login', { method: 'POST', body: new URLSearchParams({ email: email, password: password }) });
    var data = await resp.json();
    if (data.ok) { window.location.href = '/app'; }
    else if (data.error === 'no_password') {
        errEl.innerHTML = 'No password is set. <a href="#" onclick="showSetPassword(\\'' + email + '\\');return false" style="color:var(--blue);font-weight:700;">Set one now</a>';
    } else { errEl.textContent = data.error || 'Sign-in failed'; }
}
async function doRegister() {
    var name = document.getElementById('reg-name').value.trim();
    var email = document.getElementById('reg-email').value.trim();
    var password = document.getElementById('reg-password').value;
    var errEl = document.getElementById('reg-error');
    var okEl = document.getElementById('reg-success');
    errEl.textContent = ''; okEl.textContent = '';
    if (!email || !password) { errEl.textContent = 'Enter your email and password'; return; }
    var resp = await fetch('/auth/register', { method: 'POST', body: new URLSearchParams({ email: email, password: password, name: name }) });
    var data = await resp.json();
    if (data.ok) { okEl.textContent = data.message || 'Check your email to verify'; }
    else { errEl.textContent = data.error || 'Registration failed'; }
}
async function doForgot() {
    var email = document.getElementById('forgot-email').value.trim();
    var msgEl = document.getElementById('forgot-msg');
    msgEl.textContent = '';
    if (!email) { msgEl.textContent = 'Enter your email address'; msgEl.style.color = 'var(--danger)'; return; }
    var resp = await fetch('/auth/forgot', { method: 'POST', body: new URLSearchParams({ email: email }) });
    var data = await resp.json();
    msgEl.style.color = 'var(--success)';
    msgEl.textContent = data.message || 'Reset link sent if account exists';
}
function showSetPassword(email) {
    var form = document.getElementById('auth-form-login');
    form.innerHTML = '<p style="font-size:13px;color:var(--ink-2);margin-bottom:12px;">Set a password for <strong>' + email + '</strong></p>'
        + '<input type="password" id="set-pw-input" placeholder="New password (6 characters minimum)" aria-label="New password (6 characters minimum)" style="width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:4px;font-size:14px;margin-bottom:12px;">'
        + '<div id="set-pw-error" role="alert" style="color:var(--danger);font-size:12px;margin-bottom:8px;"></div>'
        + '<button onclick="doSetPassword(\\'' + email + '\\')" style="padding:8px 16px;background:var(--blue);color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:13px;">Set password</button>';
}
async function doSetPassword(email) {
    var password = document.getElementById('set-pw-input').value;
    var errEl = document.getElementById('set-pw-error');
    if (!password || password.length < 6) { errEl.textContent = 'Use at least 6 characters'; return; }
    var resp = await fetch('/auth/set-password', { method: 'POST', body: new URLSearchParams({ email: email, password: password }) });
    var data = await resp.json();
    if (data.ok) window.location.href = '/app';
    else errEl.textContent = data.error || 'Could not set the password';
}
document.addEventListener('click', function(e) {
    var overlay = document.getElementById('signin-overlay');
    if (e.target === overlay) overlay.classList.remove('visible');
});
document.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
        var overlay = document.getElementById('signin-overlay');
        if (overlay && overlay.classList.contains('visible')) {
            var focusable = Array.from(overlay.querySelectorAll('button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])')).filter(function(el) { return !el.disabled && el.offsetParent !== null; });
            if (focusable.length) {
                var first = focusable[0], last = focusable[focusable.length - 1];
                if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
                else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
            }
        }
    }
    if (e.key === 'Escape') {
        var overlay = document.getElementById('signin-overlay');
        if (overlay) overlay.classList.remove('visible');
    }
});
"""))

    auth_css = Style("""
.signin-overlay { position:fixed; inset:0; background:rgba(15,23,42,0.56); display:none; align-items:center; justify-content:center; z-index:100; padding:20px; }
.signin-overlay.visible { display:flex; }
.auth-tab { padding:10px 16px; font-size:13px; font-weight:700; background:transparent; border:none; border-bottom:2px solid transparent; color:var(--ink-3); cursor:pointer; }
.auth-tab.active { color:var(--ink); border-bottom-color:var(--blue); }
.google-btn { display:flex; align-items:center; justify-content:center; gap:10px; width:100%; padding:10px 16px; border:1px solid var(--line); border-radius:4px; background:#fff; font-size:14px; font-weight:700; color:var(--ink-2); text-decoration:none; cursor:pointer; transition:background 0.15s, box-shadow 0.15s; }
.google-btn:hover { background:var(--bg-alt); box-shadow:0 1px 3px rgba(15,23,42,0.08); }
.google-btn-icon { display:flex; align-items:center; }
.google-btn-text { font-family:'Aino', Verdana, system-ui, sans-serif; }
.google-divider { display:flex; align-items:center; gap:12px; margin:14px 0; }
.google-divider-line { flex:1; height:1px; background:var(--line); }
.google-divider-text { font-size:12px; color:var(--ink-3); }
""")

    return Div(
        hero, statement, stats, features, agents_section, how, cta,
        auth_modal, auth_css, auth_js,
        cls='home-page',
    )
