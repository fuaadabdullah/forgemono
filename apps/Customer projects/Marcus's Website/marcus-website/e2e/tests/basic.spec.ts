import { test, expect } from '@playwright/test';

test('Bookings flow and pages load', async ({ page, baseURL }) => {
  await page.goto('/');
  await expect(page.locator('h1', { hasText: 'Elbey Projects' })).toBeVisible();

  // Click Book Inspection (CTA) - scroll to booking form
  await page.locator('text=Book Inspection').click();
  await expect(page.locator('#booking')).toBeVisible();

  // Fill booking form minimally
  await page.fill('input[name="name"]', 'Playwright Test User');
  await page.fill('input[name="phone"]', '(555) 555-0123');
  await page.fill('input[name="address"]', '123 Elm Street');
  await page.fill('input[name="vehicle"]', 'Honda Civic 2018');
  await page.check('input[name="consent"]');

  await page.click('text=Book Service Now');
  await expect(page.locator('text=Thank you! Your service request has been submitted.')).toBeVisible({ timeout: 10000 });

  // Visit blog page and open a blog post
  await page.goto('/blog');
  await expect(page.locator('text=How to Tell If Your Suspension is Shot')).toBeVisible();
  await page.click('text=How to Tell If Your Suspension is Shot');

  await expect(page.locator('h1', { hasText: 'How to Tell If Your Suspension is Shot' })).toBeVisible();

  // Visit testimonials page
  await page.goto('/testimonials');
  await expect(page.locator('text=Customer Testimonials')).toBeVisible();
  await expect(page.locator('text=What Our Customers Say')).toBeVisible();
});
