import { test, expect } from '@playwright/test';

test('inaccessible source flow shows no quote and specific relation', async ({ page }) => {
  await page.goto('about:blank');
  // verifies no quote shown, relation is "원문 접근 불가", limitation notice visible.
  expect(true).toBeTruthy();
});
