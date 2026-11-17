# ARCH Email Variables Reference

Every merge token used across the 30 templates. Tokens are written `{{name}}` and appear in the HTML, the plain-text version, the subject line and the preheader. Replace every token before sending. None is left in place.

Example values are for testing only.

| Token | What it is | Example value | Supplied by | Used in |
|---|---|---|---|---|
| `{{asset_base_url}}` | Absolute HTTPS address of the folder that hosts arch-monogram-email.png. No trailing slash. Every HTML email. Not used in plain text. | https://assets.example.com/email | Developer / hosting | all 30 emails |
| `{{app_url}}` | Link that opens the ARCH app (universal link, with a web fallback). Buttons in welcome-style and account emails. | https://app.example.com/open | Developer | 5 emails: 01_welcome, 09_payment_confirmed_web, 12_membership_cancelled_apple, 12_membership_cancelled_web, 19_account_restored |
| `{{signin_url}}` | Link to the sign-in screen. Used where she should sign in to continue or to recover. | https://app.example.com/signin | Developer | 4 emails: 13_address_reminder, 14_email_changed_new, 06_deletion_requested_apple, 06_deletion_requested_google |
| `{{manage_url}}` | Signed-in link to Profile, Manage membership. Web-billing emails only. | https://app.example.com/profile/membership | Developer | 5 emails: 08_trial_started_web, 05_trial_ending_web, 10_membership_renewed_web, 16_renewal_reminder_yearly_web, 17_renewal_reminder_monthly_web |
| `{{update_payment_url}}` | Link to update the payment method. Web-billing emails only. | https://app.example.com/profile/payment | Developer | 2 emails: 11_payment_failed_web, 15_payment_failed_final_web |
| `{{reset_url}}` | Single-use password reset link. Expires after link_minutes. | https://app.example.com/reset?token=EXAMPLE | Developer (generated per request) | 2 emails: 03_password_reset, 04_password_changed |
| `{{privacy_url}}` | Privacy policy page. Footer of every email. | https://www.example.com/privacy | Developer | all 30 emails |
| `{{terms_url}}` | Terms page. Footer of every email. | https://www.example.com/terms | Developer | all 30 emails |
| `{{legal_address}}` | Postal address line printed in the footer. Footer of every email. | Business address, City, State | Business details (supplied by the business owner) | all 30 emails |
| `{{verification_code}}` | Six-digit one-time code, shown grouped as 3 + 3. | 482 915 | Developer (generated per request) | 1 emails: 02_verification_code |
| `{{code_minutes}}` | Whole number of minutes the code stays valid. Must match the real expiry. | 10 | Developer configuration | 1 emails: 02_verification_code |
| `{{link_minutes}}` | Whole number of minutes the reset link stays valid. Must match the real expiry. | 30 | Developer configuration | 1 emails: 03_password_reset |
| `{{change_date}}` | Date and time the change was made. Day, month name, year, 24-hour time. Decide once whether to add a time zone; the templates need no change either way. | 1 December 2026, 14:32 | Developer | 3 emails: 04_password_changed, 14_email_changed_old, 14_email_changed_new |
| `{{new_email_masked}}` | New address with the middle hidden. First character, then dots, then the domain. | c••••@gmail.com | Developer | 1 emails: 14_email_changed_old |
| `{{trial_start_date}}` | Date the free trial started. | 1 December 2026 | Developer | 2 emails: 08_trial_started_apple, 08_trial_started_web |
| `{{trial_end_date}}` | Last day of the free trial. | 15 December 2026 | Developer | 4 emails: 08_trial_started_apple, 08_trial_started_web, 05_trial_ending_apple, 05_trial_ending_web |
| `{{first_charge_date}}` | Date of the first charge if she does not cancel. | 15 December 2026 | Developer | 4 emails: 08_trial_started_apple, 08_trial_started_web, 05_trial_ending_apple, 05_trial_ending_web |
| `{{plan_price}}` | Price with its period, exactly as billed. Never typed into a template. Currency symbol and amount come from billing. For App Store members, use the amount Apple charges that member (regional price, offer, currency), not a catalogue price. | $X.XX per month  /  $X.XX per year | Billing system | 10 emails: 08_trial_started_apple, 08_trial_started_web, 05_trial_ending_apple, 05_trial_ending_web, 09_payment_confirmed_web, 10_membership_renewed_web, 16_renewal_reminder_yearly_apple, 16_renewal_reminder_yearly_web, 17_renewal_reminder_monthly_apple, 17_renewal_reminder_monthly_web |
| `{{plan_name}}` | Name of her plan. | ARCH Monthly  /  ARCH Yearly | Billing system | 2 emails: 09_payment_confirmed_web, 10_membership_renewed_web |
| `{{renewal_date}}` | A renewal date. Meaning by email: 09 next renewal; 10 the date it renewed; 16 the date being reminded about; 17 the next monthly renewal. | 15 December 2026 | Billing system | 6 emails: 09_payment_confirmed_web, 10_membership_renewed_web, 16_renewal_reminder_yearly_apple, 16_renewal_reminder_yearly_web, 17_renewal_reminder_monthly_apple, 17_renewal_reminder_monthly_web |
| `{{next_renewal_date}}` | The renewal after the one just completed. | 15 January 2027 | Billing system | 1 emails: 10_membership_renewed_web |
| `{{access_until_date}}` | Last day of access. | 16 December 2026 | Billing system | 6 emails: 11_payment_failed_apple, 11_payment_failed_web, 15_payment_failed_final_apple, 15_payment_failed_final_web, 12_membership_cancelled_apple, 12_membership_cancelled_web |
| `{{update_date}}` | Date the payment method was changed. | 1 December 2026 | Developer | 1 emails: 18_payment_method_updated_web |
| `{{request_date}}` | Date the deletion was requested. | 1 December 2026 | Developer | 2 emails: 06_deletion_requested_apple, 06_deletion_requested_google |
| `{{removal_date}}` | Date the account is, or was, removed. Request date plus 14 days. | 15 December 2026 | Developer | 5 emails: 06_deletion_requested_apple, 06_deletion_requested_google, 07_deletion_confirmed_apple, 07_deletion_confirmed_google, 19_account_restored |
| `{{original_subject}}` | Subject line of the customer's original message. Used in the subject line of the reply. Strip line breaks before use in the subject header. | Your question about ARCH | Support tool | 1 emails: 20_customer_service_reply |
| `{{reply_body}}` | The reply text typed by the person replying. HTML version: escape it, convert line breaks to <br>. Text version: insert as typed. | Thank you for your patience. We have looked into this and can confirm the details below. | Support tool | 1 emails: 20_customer_service_reply |
| `{{agent_name}}` | First name of the person replying. | Alex | Support tool | 1 emails: 20_customer_service_reply |
