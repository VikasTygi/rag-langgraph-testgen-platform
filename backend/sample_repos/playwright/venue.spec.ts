import { test, expect } from '@playwright/test';

// Declare process to avoid TypeScript errors when node types are not installed
declare const process: any;

test('create venue on ruckus cloud', async ({ page }) => {
  await page.goto('https://ruckus.cloud/login');

  await page.fill('#username', process.env.RC_USERNAME || 'admin');
  await page.fill('#password', process.env.RC_PASSWORD || 'password');
  await page.click('button[type="submit"]');

  await expect(page.locator('text=Dashboard')).toBeVisible();

  await page.click('text=Tenant');
  await page.click('text=DemoTenant');

  await page.click('text=Venues');
  await page.click('text=Create Venue');

  await page.fill('#venueName', 'Auto_Venue_001');
  await page.click('button[type="submit"]');

  await expect(page.locator('text=Auto_Venue_001')).toBeVisible();
});