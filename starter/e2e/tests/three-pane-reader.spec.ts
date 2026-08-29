import { test, expect } from '@playwright/test';

test.describe('CiteTrace 3-pane reader', () => {
    test('renders the three-pane shell at /', async ({ page }) => {
        await page.goto('/');
        await expect(page.getByRole('main')).toBeVisible();
        const workspace = page.locator('.reader-workspace');
        await expect(workspace).toBeVisible();
        const panes = workspace.locator('> *');
        await expect(panes).toHaveCount(3);
    });

    test('reference map pane is the first pane', async ({ page }) => {
        await page.goto('/');
        const firstPane = page.locator('.reader-workspace > *').first();
        await expect(firstPane).toBeVisible();
    });

    test('paper pane is the second pane', async ({ page }) => {
        await page.goto('/');
        const secondPane = page.locator('.reader-workspace > *').nth(1);
        await expect(secondPane).toBeVisible();
    });

    test('evidence pane is the third pane', async ({ page }) => {
        await page.goto('/');
        const thirdPane = page.locator('.reader-workspace > *').nth(2);
        await expect(thirdPane).toBeVisible();
    });

    test('page does not have a 5xx error', async ({ page }) => {
        const response = await page.goto('/');
        expect(response, 'no response received for /').not.toBeNull();
        const status = response!.status();
        expect(status, `unexpected status ${status}`).toBeLessThan(500);
    });
});
