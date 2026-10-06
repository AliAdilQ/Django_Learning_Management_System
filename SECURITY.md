# Security

This is a local portfolio and demonstration project. The demo credentials in the README are intentionally public and must never be used on a public deployment.

## Implemented boundaries

- Students can access published course lessons, assignments, and quizzes only after enrollment.
- Instructors can edit and grade only their own courses. Parent identifiers are checked against ownership on the server.
- Staff administration is protected by Django's authentication and permission system.
- Registration and profile editing exclude roles, staff flags, and superuser flags.
- State-changing forms use CSRF tokens. Enrollment, logout, completion, review, and deletion use POST.
- Assignment uploads are private and authorized at download time. Randomized stored names prevent collisions. Validation allows PDF/TXT/Markdown files up to 5 MB; text must be UTF-8 and PDFs must have a PDF signature.
- Avatar and thumbnail uploads use Pillow validation, accepted image formats, and size/dimension limits.
- Quiz choices are validated against their question. Attempts can be finalized only once, and deadlines are checked on the server. Saved answer text preserves historical results when question wording changes.
- Database constraints prevent duplicate enrollment, completion, reviews, submissions, and simultaneous active attempts for a student/quiz pair.

## Before public deployment

Start with a clean database, create new administrative credentials, set `DJANGO_DEBUG=False`, configure allowed hosts, and use a unique secret of at least 50 characters supplied by your environment or secret manager. Do not publish `.env`, `db.sqlite3`, or uploads.

Serve the application through a production WSGI/ASGI server behind HTTPS. Configure static and public image media separately. Never expose `private_uploads/` through a public file server. Apply filesystem permissions, backups, request-size limits, login/contact rate limits, and malware scanning appropriate to the deployment. Configure trusted proxy handling only for infrastructure you control.

Run `python manage.py check --deploy` with production environment settings. The local defaults are deliberately convenient for development and are not deployment settings. PDF signatures and extension checks are basic validation, not comprehensive malware detection.

## Reporting

Do not place passwords, private submissions, or exploit details into a public issue. Contact [AliAdilQ](https://github.com/AliAdilQ) using a private contact method available on the maintainer's profile. If the repository enables GitHub private vulnerability reporting, use its Security tab. There is no published response-time commitment for this portfolio project.
