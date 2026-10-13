# Module 12 — Notifications

The API stores in-app notifications with a recipient, type, title, message,
optional internal link, creation time, and read timestamp. User notifications
are scoped by authenticated user ID. Invitation notifications are initially
addressed to the invitee's email and are claimed by the authenticated account
when its JWT email claim matches.

The current events are successful document processing, parsing/no-text
failures, report generation success/failure, and organization invitation
creation. Notification creation is committed with the corresponding database
update where the event is transactional. Delivery is in-app only; email or
push delivery is not included.

See [Notifications API](../api/notifications.md).
