# Requirements Checklist: Stage 2 Product Reviews & Moderation

This checklist verifies all Stage 2 Product Reviews functional requirements.

## Review Submission
- [x] **FR-001**: Only authenticated users are allowed to submit reviews.
- [x] **FR-002**: A review includes a rating from 1 to 5 stars.
- [x] **FR-003**: A review includes a non-empty text comment.
- [x] **FR-004**: A review supports one optional attached image.
- [x] **FR-005**: Attached images are stored in-memory (as Base64 string) on the backend.
- [x] **FR-006**: When submitted, reviews start in `"pending"` status.

## Review Moderation
- [x] **FR-007**: Only the user with identifier `"moderator"` is treated as a moderator.
- [x] **FR-008**: The moderator has access to a Moderation Dashboard.
- [x] **FR-009**: The Moderation Dashboard displays all reviews (pending, approved, and rejected) in the system.
- [x] **FR-010**: The moderator can approve a review, changing its status to `"approved"`.
- [x] **FR-011**: The moderator can reject a review, changing its status to `"rejected"`.

## Review Display
- [x] **FR-012**: Users (authenticated or not) see approved reviews on the product details view.
- [x] **FR-013**: Pending or rejected reviews are hidden from normal users.
- [x] **FR-014**: Review displays show the rating, comment, user's identifier, and the attached image (if present).
