import { test, expect } from '@playwright/test';

const BASE = process.env.BASE_URL || 'http://localhost:3000';

test.describe('Smoke E2E flows', () => {
  test('Home loads, blog and testimonials load, booking form submits', async ({ page }) => {
    await page.goto(BASE + '/');
    await expect(page).toHaveTitle(/Elbey Projects/);

    // Scroll to testimonials
    await page.locator('text=What Our Customers Say').scrollIntoViewIfNeeded();
    await expect(page.locator('text=Read More Reviews')).toBeVisible();

    // Navigate to testimonials page
    await page.click('text=Read More Reviews');
    await expect(page).toHaveURL(BASE + '/testimonials');
    await expect(page.locator('text=Customer Testimonials')).toBeVisible();

    // Navigate back and go to a blog post
    await page.goto(BASE + '/blog');
    await expect(page.locator('text=How to Tell If Your Suspension is Shot')).toBeVisible();
    await page.click('text=How to Tell If Your Suspension is Shot');
    await expect(page).toHaveURL(/.*suspension-warning-signs$/);
    await expect(page.locator('text=How to Tell If Your Suspension is Shot')).toBeVisible();

    // Book service: navigate to home and submit booking
    await page.goto(BASE + '/');
    await page.click('text=Book Service');
    await expect(page.locator('#booking')).toBeVisible();

    await page.fill('#name', 'Playwright Test');
    await page.fill('#phone', '(555) 555-5555');
    await page.fill('#email', 'test@example.com');
    await page.selectOption('#service', 'brakes');
    await page.fill('#description', 'Test booking via e2e');
    await page.check('input[name="consent"]');

    await page.click('text=Book Service Now');
    await expect(page.locator('text=Thank you! Your service request has been submitted')).toBeVisible({ timeout: 5000 });
  });
});
