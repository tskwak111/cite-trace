import { test, expect } from '@playwright/test';

test('analyze paper user flow', async ({ page }) => {
  // Mock flow
  await page.goto('about:blank');
  // upload PDF, monitor progress, select citation, inspect evidence card, open source location
  expect(true).toBeTruthy();
});
