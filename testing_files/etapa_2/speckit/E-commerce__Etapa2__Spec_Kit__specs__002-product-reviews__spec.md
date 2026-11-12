# Feature Specification: Stage 2 Product Reviews & Moderation

**Feature Branch**: `002-product-reviews`

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "Extend Stage 1 with product reviews that support images and moderation. Preserve the existing purchasing journey. Keep it local, in-memory, and easy to demonstrate."

## User Scenarios & Testing

### User Story 1 - Submit Product Review with Image (Priority: P1)

As an authenticated customer, I want to submit a review (rating and text comment) with an optional image for a product so that I can share my experience.

**Why this priority**: Core of Stage 2 functional scope. Allows users to write reviews and attach images.

**Independent Test**: Log in as a customer, go to a product details page, write a comment, select a rating from 1 to 5 stars, select an image file, click submit, and verify that the submission is successful and goes to moderation.

**Acceptance Scenarios**:

1. **Given** a customer is logged in and on a product details page, **When** they fill out the review form with a valid rating (1-5), comment, and select an optional image, and submit, **Then** the review is sent to the backend and a confirmation message is shown explaining that the review has been submitted and is pending moderation.
2. **Given** a customer is on the review form, **When** they submit without entering a rating or comment, **Then** form validation errors are shown and submission is blocked.
3. **Given** an unauthenticated visitor is on the product details page, **When** they view the reviews section, **Then** the review form is hidden or displays a message prompting them to sign in first.

---

### User Story 2 - View Moderated Reviews on Catalog / Product Page (Priority: P2)

As a user (visitor or customer), I want to see approved reviews for a product on its details page so that I can make informed buying decisions.

**Why this priority**: Essential to make the submitted reviews useful for potential buyers.

**Independent Test**: Visit a product details page and verify that only approved reviews are displayed (showing rating, comment, user identifier, and uploaded image if available). Pending or rejected reviews must not be visible to normal users.

**Acceptance Scenarios**:

1. **Given** a user is viewing a product details page, **When** there are approved reviews for this product, **Then** those reviews are displayed, including user, rating, comment, and image (if attached).
2. **Given** there are pending or rejected reviews for a product, **When** a normal user views the product details, **Then** those reviews are NOT displayed.
3. **Given** a product has no approved reviews, **When** a user views the product details, **Then** a friendly message indicating no reviews have been posted yet is shown.

---

### User Story 3 - Moderator Dashboard & Review Approval (Priority: P3)

As a moderator, I want to view all submitted reviews (pending, approved, rejected) and approve or reject them so that I can moderate the content.

**Why this priority**: Necessary moderation workflow to control what content is published in the store.

**Independent Test**: Log in as `moderator` (credentials: identifier `moderator`, password `moderator`), navigate to the "Moderator Dashboard" (only accessible to the `moderator` user), view the list of reviews, and click "Approve" or "Reject" on a pending review, verifying that its status updates.

**Acceptance Scenarios**:

1. **Given** I am logged in as the user `moderator`, **When** I view the navigation bar, **Then** I see a link to the "Moderation Dashboard".
2. **Given** I am on the Moderation Dashboard, **When** I view the page, **Then** I see a list of all reviews across all products, categorized or marked by status (Pending, Approved, Rejected).
3. **Given** a pending review on the dashboard, **When** I click "Approve", **Then** the review's status changes to "approved" on the backend and it immediately appears as visible on the product page.
4. **Given** a pending review on the dashboard, **When** I click "Reject", **Then** the review's status changes to "rejected" on the backend and it remains hidden from the product page.
5. **Given** a regular customer is logged in (username is not `moderator`), **When** they attempt to access `/moderation` or look at the navbar, **Then** they cannot see or access the Moderation Dashboard.

---

### Edge Cases

- **Session Expiration**: If the session expires or restarts, all reviews remain in memory but the user must log in again to write reviews or moderate.
- **Large Image Handling**: Standard image files are converted to Base64 on the client side. If the image is too large, the frontend can limit it to 2MB or show a message, ensuring smooth memory operations on the local FastAPI backend.
- **Invalid Product ID**: Submitting a review for a non-existent product is validated and rejected by the backend.

## Requirements

### Functional Requirements

#### Review Submission
- **FR-001**: Only authenticated users MUST be allowed to submit reviews.
- **FR-002**: A review MUST include a rating from 1 to 5 stars.
- **FR-003**: A review MUST include a text comment (non-empty).
- **FR-004**: A review MAY support one attached image.
- **FR-005**: An attached image MUST be uploaded by the client and stored in-memory (as Base64) on the backend.
- **FR-006**: When submitted, a review MUST start in `pending` status.

#### Review Moderation
- **FR-007**: Only the user with identifier `moderator` MUST be treated as a moderator.
- **FR-008**: The moderator MUST have access to a Moderation Dashboard.
- **FR-009**: The Moderation Dashboard MUST display all reviews (pending, approved, and rejected) in the system.
- **FR-010**: The moderator MUST be able to approve a review, changing its status to `approved`.
- **FR-011**: The moderator MUST be able to reject a review, changing its status to `rejected`.

#### Review Display
- **FR-012**: Users (authenticated or not) MUST see approved reviews on the product details view.
- **FR-013**: Pending or rejected reviews MUST NOT be visible to normal users.
- **FR-014**: Review displays MUST show the rating, comment, user's identifier, and the attached image (if present).
