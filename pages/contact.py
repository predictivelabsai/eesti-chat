from fasthtml.common import *


INPUT_CLS = 'public-field'


def contact_page(name='', email='', message='', error=''):
    return Div(
        Section(
            Div(
                H1('Contact us', cls='public-page-title'),
                P('Questions or feedback about eesti.chat? Send us a message. '
                  'For official matters, contact the relevant government authority.',
                  cls='public-page-intro'),
                cls='portal-container public-hero-content'
            ),
            cls='public-page-hero'
        ),
        Section(
            Div(
                Div(
                    Form(
                        *([P(error, cls='contact-error', role='alert')] if error else []),
                        Div(
                            Label('Name', **{'for': 'contact-name'}, cls='field-label'),
                            Input(type='text', id='contact-name', name='name', placeholder='Your name',
                                  value=name, autocomplete='name', required=True, cls=INPUT_CLS),
                        ),
                        Div(
                            Label('Email', **{'for': 'contact-email'}, cls='field-label'),
                            Input(type='email', id='contact-email', name='email', placeholder='you@example.com',
                                  value=email, autocomplete='email', required=True, cls=INPUT_CLS),
                        ),
                        Div(
                            Label('Message', **{'for': 'contact-message'}, cls='field-label'),
                            Textarea(message, id='contact-message', name='message', placeholder='Your message...', rows=5,
                                     required=True,
                                     cls=INPUT_CLS + ' resize-none'),
                        ),
                        Button('Send message', type='submit',
                               cls='public-button public-button-primary public-button-full'),
                        method='post', action='/contact',
                        cls='contact-form'
                    ),
                    cls='max-w-7xl mx-auto'
                ),
            ),
            cls='public-section public-section-alt contact-section'
        ),
    )
