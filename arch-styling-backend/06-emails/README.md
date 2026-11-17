# ARCH Emails: Developer Handoff

This folder holds the 30 transactional email templates for ARCH, each as HTML with a plain-text twin, plus the sheets that say when each one is sent and what it needs.

## What is here

| File or folder | What it is |
|---|---|
| `ARCH_Email_Sheet.xlsx` and `.csv` | One row per email: trigger, timing, subject line, preheader, file names, merge variables, notes. The two files hold the same data. |
| `ARCH_Email_Variables.md` and `.csv` | Every merge token used, with a description, an example value and where it appears. 28 tokens. |
| `emails/html/` | The 30 HTML templates. |
| `emails/text/` | The 30 plain-text versions. Same file name, `.txt`. |
| `assets/arch-monogram-email.png` | The only image. Host it so that `{{asset_base_url}}/arch-monogram-email.png` loads over HTTPS. |
| `tools/check_templates.py` | A checker. Run `python3 tools/check_templates.py`. It needs only Python 3. |

## How the templates work

- Every `{{token}}` is replaced before sending. Nothing is left in place.
- The subject line and preheader are in the sheet, not in the template body. The preheader is also in the HTML as hidden text. Subject lines can contain tokens, for example `Your ARCH membership renews on {{renewal_date}}`.
- Send every message as multipart: the HTML and the matching `.txt` together. The text version is a full alternative, not a stub. Some clients and some readers will only ever see it.
- If you change the wording in an HTML file, change the `.txt` file in the same commit. The checker confirms that the tokens and links match.
- Where a template sends a button to a store page (Apple Settings, Google Play), the address is fixed in the template. It is not a token.

## Who gets which email

Most emails go to everyone. Some come in versions for each billing path, marked in the file name:

- `_apple` goes to App Store members.
- `_web` goes to members who pay on the web.
- `_google` goes to members who pay through Google Play. Whether Android uses Google Play billing is not yet decided. Do not wire the two `_google` templates until it is.

Rules for the build:

1. App Store members get no payment-confirmed email, no renewed email and no payment-method-updated email from ARCH. Apple sends those. The three templates (`09`, `10`, `18`) exist only as `_web`. Do not create Apple copies.
2. Renewal and trial notices go out on these timings, and the count matters:
   - `05` trial ending: 2 days before `trial_end_date`.
   - `16` yearly renewal reminder: 30 days before `renewal_date`.
   - `17` monthly members: once a year, on the anniversary of the first charge.
3. `15` payment failed (final notice): the suggested send time is 3 days before `access_until_date`. Set the number in configuration.
4. `06` and `07` belong to the 14-day account recovery period. `removal_date` is the request date plus 14 days.
5. `20` customer service reply: the body is typed by a person. Escape it and convert line breaks to `<br>` for the HTML version. Insert it as typed in the text version.
6. Keep a copy of each `08` trial-started email sent, on record.

## Layout and colour rules

These are fixed. The checker enforces most of them.

- Tables for layout. No flexbox, no grid, no float.
- Inline CSS on every element. The one `<style>` block holds only what cannot be inline: small-screen adjustments, link hover, the light-mode declarations, the Outlook overrides, and the Apple Mail dark-mode rules.
- 600 px maximum width. The reading column inside it is 420 px.
- Muted text is `#666666` on the warm white `#FAF6F0`. That is 5.33:1. Do not lighten it to `#888888`. `#888888` appears only inside the dark-mode rules, on the dark ground `#0A0A0A` (5.58:1).
- Gold `#C9A84C` is for rules and the button fill only, never for text. The button label is `#0A0A0A` on gold (8.66:1).
- Tap targets are at least 44 px. Each HTML file stays under 100 KB.

## Dark mode

Every template is declared light: `color-scheme` and `supported-color-schemes` are set to `light` in the head (meta tags and a `:root` rule). `[data-ogsb]` and `[data-ogsc]` rules pin Outlook.com and the Outlook apps to the light colours (ground `#FAF6F0`, ink `#0A0A0A`, muted `#666666`, gold button fill with a `#0A0A0A` label). That stops most forced inversion at the source.

Two limits to know. Gmail ignores these declarations and may still recolour on its own. The `prefers-color-scheme: dark` block is still in each template, so a client that honours that media query (Apple Mail, iOS Mail) shows the designed dark version. Do not remove or edit either without asking. The button keeps its gold fill and dark label in every mode.

Before launch, send two templates to a real Gmail account on a phone and check how they render: `05_trial_ending_web` (button and ledger) and `02_verification_code` (rules only). Also check Outlook and Apple Mail.

## Before launch

- Send each template to real inboxes with realistic token values, including a long `reply_body`, and check the text version in a plain-text client.
- Confirm that `code_minutes` and `link_minutes` match the real expiry times.
- Take prices, plan names and dates only from the billing system. No amount is typed into any template.
