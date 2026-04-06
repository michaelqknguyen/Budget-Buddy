## MODIFIED Requirements

### Requirement: Allauth configuration uses v65+ settings format
The system SHALL use django-allauth 65+ settings format. The `ACCOUNT_*` settings structure SHALL be updated to match the new allauth configuration schema. The custom `AccountAdapter` and `SocialAccountAdapter` in `budgetbuddy/users/adapters.py` SHALL remain functional with their `is_open_for_signup` method unchanged.

#### Scenario: Registration toggle works
- **WHEN** `ACCOUNT_ALLOW_REGISTRATION` is set to False
- **THEN** the signup page is not accessible and the adapter blocks new registrations

#### Scenario: Email verification is enforced
- **WHEN** a new user signs up
- **THEN** their email must be verified before they can log in, per `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`

### Requirement: Crispy forms uses Bootstrap 5 template pack
The system SHALL use `crispy-forms` 2.x with the `bootstrap5` template pack. `CRISPY_TEMPLATE_PACK` SHALL be set to `"bootstrap5"`.

#### Scenario: Forms render with Bootstrap 5 styling
- **WHEN** a page with a crispy form is rendered
- **THEN** the form HTML uses Bootstrap 5 classes and layout
