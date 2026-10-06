/* Optional: run against the seeded local development server. */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require('playwright');

const baseURL = process.env.LMS_BASE_URL || 'http://127.0.0.1:8000';
const screenshots = path.resolve(__dirname, '../docs/screenshots');
let activeBrowser;

async function main() {
  await fs.mkdir(screenshots, { recursive: true });
  const browser = activeBrowser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {}) });
  const context = await browser.newContext({ baseURL, viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {
    if (response.url().startsWith(baseURL) && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
  });

  async function visit(url) {
    const response = await page.goto(url);
    assert.equal(response.status(), 200, url);
    await page.evaluate(() => document.fonts.ready);
    await page.locator('img').evaluateAll(images => Promise.all(images.map(image => {
      image.loading = 'eager';
      return image.complete ? Promise.resolve() : new Promise(resolve => { image.onload = resolve; image.onerror = resolve; });
    })));
    const broken = await page.locator('img').evaluateAll(images => images.filter(image => !image.naturalWidth).map(image => image.src));
    assert.deepEqual(broken, [], `Broken images at ${url}`);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
    if (overflow) console.error(await page.evaluate(() => [...document.querySelectorAll('main *')].filter(element => element.getBoundingClientRect().right > innerWidth + 1).slice(0, 12).map(element => ({ tag: element.tagName, class: element.className, width: element.getBoundingClientRect().width, right: element.getBoundingClientRect().right }))));
    assert.equal(overflow, false, `Horizontal overflow at ${url}`);
  }

  async function capture(url, filename, fullPage = true) {
    await visit(url);
    await page.screenshot({ path: path.join(screenshots, filename), fullPage });
    console.log(`Captured ${filename}`);
  }

  async function login(username, password) {
    await visit('/login/');
    await page.getByLabel(/^Username/).fill(username);
    await page.getByLabel(/^Password/).fill(password);
    await Promise.all([page.waitForURL(/dashboard\/|admin\//), page.getByRole('button', { name: 'Log in', exact: false }).click()]);
  }

  async function logout() {
    await page.getByRole('button', { name: 'Log out', exact: true }).click();
    await page.waitForURL('/');
  }

  await capture('/', 'home-page.png', false);
  await page.screenshot({ path: path.join(screenshots, 'home-full-page.png'), fullPage: true });
  await capture('/courses/', 'course-list.png');
  await capture('/courses/python-programming-fundamentals/', 'course-page.png');
  await capture('/login/', 'login-page.png');
  await visit('/courses/');
  await page.getByLabel('Search courses', { exact: true }).fill('Django');
  await page.getByRole('button', { name: 'Find courses' }).click();
  assert.equal(await page.locator('.course-card').count(), 1);

  await login('student1', 'Student123!');
  await capture('/dashboard/student/', 'student-dashboard.png', false);
  await visit('/profile/');
  await visit('/assignments/');
  await page.locator('.modern-table tbody a').first().click();
  await page.waitForLoadState();
  await visit('/quizzes/');
  await page.getByRole('link', { name: 'Open quiz' }).first().click();
  await page.getByRole('button', { name: 'Start quiz' }).click();
  await page.locator('.quiz-question').first().waitFor();
  await page.screenshot({ path: path.join(screenshots, 'quiz-page.png'), fullPage: true });
  const questions = page.locator('.quiz-question');
  for (let i = 0; i < await questions.count(); i++) await questions.nth(i).locator('input[type=radio]').first().check();
  await page.getByRole('button', { name: 'Submit answers' }).click();
  await page.waitForURL(/quizzes\/results\//);
  await page.locator('.score-circle').waitFor();

  await visit('/courses/python-programming-fundamentals/');
  await page.getByRole('link', { name: 'Continue learning', exact: false }).first().click();
  await page.locator('.lesson-content').waitFor();
  await page.screenshot({ path: path.join(screenshots, 'lesson-page.png'), fullPage: true });

  // Mobile layouts, menu behavior, tables, forms, and the lesson sidebar.
  await page.setViewportSize({ width: 390, height: 844 });
  await visit('/dashboard/student/');
  await page.screenshot({ path: path.join(screenshots, 'student-dashboard-mobile.png'), fullPage: true });
  for (const url of ['/assignments/', '/quizzes/', '/profile/', '/profile/edit/', '/courses/python-programming-fundamentals/']) await visit(url);
  await page.getByRole('button', { name: 'Toggle navigation' }).click();
  await page.locator('#main-nav.show').waitFor();
  await page.getByRole('button', { name: 'Toggle navigation' }).click();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await visit('/dashboard/student/');
  await logout();

  await login('instructor1', 'Instructor123!');
  await capture('/dashboard/instructor/', 'instructor-dashboard.png', false);
  await page.getByRole('link', { name: 'Manage', exact: false }).first().click();
  await page.locator('.manage-item').first().waitFor();
  await page.getByRole('link', { name: 'Edit course', exact: true }).click();
  await page.getByLabel(/^Title/).waitFor();
  await page.setViewportSize({ width: 390, height: 844 });
  await visit('/dashboard/instructor/');
  await page.screenshot({ path: path.join(screenshots, 'instructor-dashboard-mobile.png'), fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await visit('/dashboard/instructor/');
  await logout();

  await login('admin', 'Admin123!');
  await capture('/admin/', 'admin-panel.png');
  await context.clearCookies();
  await page.setViewportSize({ width: 390, height: 844 });
  await capture('/', 'home-mobile.png');
  await visit('/courses/');
  await visit('/register/');
  for (const url of ['/about/', '/contact/', '/courses/categories/', '/login/']) await visit(url);
  await page.setViewportSize({ width: 768, height: 1024 });
  await visit('/');
  await visit('/courses/');
  assert.deepEqual(errors, [], 'Browser/server errors');
  await browser.close();
  console.log('Browser checks passed: public pages, search, demo logins, quiz submission, lessons, instructor studio, admin, mobile/tablet layouts, images, and JavaScript.');
}
main().catch(async error => { console.error(error); if (activeBrowser) await activeBrowser.close(); process.exitCode = 1; });
