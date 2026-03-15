import { expect, test } from "@playwright/test";

async function doLogin(page) {
  await page.request.post("/api/auth/dev-login", {
    data: { email: "e2e@test.com" },
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
}

test("shows login form when not authenticated", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: /sign in with google/i })
  ).toBeVisible();
});

test("loads the kanban board after login", async ({ page }) => {
  await doLogin(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("allows user to log in and then log out", async ({ page }) => {
  await doLogin(page);
  await page.click('button:has-text("Log out")');
  await expect(
    page.getByRole("button", { name: /sign in with google/i })
  ).toBeVisible();
});

test("adds a card to a column", async ({ page }) => {
  await doLogin(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card").first()).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await doLogin(page);
  const card = page.getByTestId("card-1");
  const targetColumn = page.getByTestId("column-3");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-1")).toBeVisible();
});

test("sends a message to AI and receives response", async ({ page }) => {
  await doLogin(page);

  const chatInput = page.getByPlaceholder("Type a message...");
  const sendButton = page.getByRole("button", { name: /send/i });

  await chatInput.fill("Add a new card to Backlog");
  await sendButton.click();

  await expect(page.getByText("Add a new card to Backlog")).toBeVisible();
});
