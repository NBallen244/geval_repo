# Quickstart & Validation Guide: Stage 2 Product Reviews

This guide describes how to run and validate the Stage 2 Product Reviews & Moderation functionality.

## Prerequisites & Running
Follow the main `README.md` to start the backend and frontend components.

- **Backend**:
  ```powershell
  cd backend
  python -m uvicorn src.main:app --reload --port 8000
  ```
- **Frontend**:
  ```bash
  cd frontend
  npm start
  ```

---

## Moderator Credentials & Seeding
To make validation extremely simple, the backend automatically registers a default moderator user when it starts up:
- **Identifier**: `moderator`
- **Password**: `moderator`

When logged in with these credentials, the header/navigation bar will display a link to the **Moderator Dashboard** (at `/moderation`).

---

## End-to-End Validation Scenario

### Step 1: Browse Products & Review Empty State
1. Open the browser to `http://localhost:3000`.
2. Click on a product (e.g. "Standard Coffee Maker") to view its details.
3. Observe that under the details, there is a section called **Product Reviews**.
4. Since no reviews exist yet, you will see a message: "No reviews have been posted for this product yet."
5. Observe that since you are currently not signed in, you see a message: "Please sign in to write a review."

### Step 2: Sign In and Submit a Review
1. Register or sign in with any test user (e.g., username: `alice`, password: `password123`).
2. Go back to the catalog, and click on the "Standard Coffee Maker" product.
3. You will now see a form to **Write a Review** with:
   - Rating selection (1 to 5 stars dropdown or radio buttons)
   - Comment text box
   - Optional image upload input
4. Write a comment (e.g., "Love this coffee maker, brews super fast!"), select a 5-star rating, and upload an optional picture.
5. Click **Submit Review**.
6. You will see a success feedback toast or notification: "Your review has been submitted and is pending moderation."
7. The review form will clear. The review is NOT yet visible in the reviews list for the "Standard Coffee Maker" because it is still pending moderation.

### Step 3: Access Moderator Dashboard & Approve Review
1. Click **Sign Out** to end your session as `alice`.
2. Navigate to the Sign In page and sign in as the moderator:
   - **Identifier**: `moderator`
   - **Password**: `moderator`
3. Notice that a new link **Moderation Dashboard** appears in the navigation header.
4. Click **Moderation Dashboard**.
5. You will see the review submitted by `alice` listed under **Pending Reviews**, showing her comment, 5-star rating, and the uploaded image thumbnail.
6. Click **Approve**.
7. The review's status shifts immediately to approved, moving it to the "Approved" section.

### Step 4: Verify Approved Review Display
1. Click **Sign Out** or stay logged in.
2. Go back to the product catalog and click on "Standard Coffee Maker".
3. Check the **Product Reviews** section at the bottom.
4. The review from `alice` is now displayed, showing her identifier (`alice`), her 5-star rating, her comment, and the attached image.
