import { test, expect } from '@playwright/test';

/**
 * Helper function to generate unique user data for each test
 */
function generateUniqueUser() {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 10000);
  return {
    username: `testuser_${timestamp}_${random}`,
    email: `testuser_${timestamp}_${random}@example.com`,
    password: 'SecurePass123!',
  };
}

/**
 * Helper function to clear browser storage
 */
async function clearStorage(page) {
  // Navigate to a page first to access localStorage
  await page.goto('/static/register.html');
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
}

test.describe('Registration - Positive Tests', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
    await page.goto('/static/register.html');
  });

  test('should successfully register with valid data', async ({ page }) => {
    const user = generateUniqueUser();

    // Fill in registration form
    await page.fill('#username', user.username);
    await page.fill('#email', user.email);
    await page.fill('#password', user.password);
    await page.fill('#confirmPassword', user.password);

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for success message
    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-success')).toContainText('Registration successful');

    // Verify JWT token is stored in localStorage
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(token).toBeTruthy();
    expect(token).toMatch(/^eyJ/); // JWT tokens start with 'eyJ'

    // Verify user data is stored
    const storedUser = await page.evaluate(() => localStorage.getItem('user'));
    expect(storedUser).toBeTruthy();
    const userData = JSON.parse(storedUser);
    expect(userData.username).toBe(user.username);
    expect(userData.email).toBe(user.email);

    // Verify token type is stored
    const tokenType = await page.evaluate(() => localStorage.getItem('token_type'));
    expect(tokenType).toBe('bearer');
  });

  test('should show password strength indicator', async ({ page }) => {
    const user = generateUniqueUser();

    // Type a weak password
    await page.fill('#password', 'weak');
    await expect(page.locator('#passwordStrength')).toBeVisible();
    await expect(page.locator('#passwordStrength')).toHaveClass(/weak/);

    // Type a medium password
    await page.fill('#password', 'Medium123');
    await expect(page.locator('#passwordStrength')).toHaveClass(/medium/);

    // Type a strong password
    await page.fill('#password', 'StrongPass123!@#');
    await expect(page.locator('#passwordStrength')).toHaveClass(/strong/);
  });

  test('should show success state on valid inputs', async ({ page }) => {
    const user = generateUniqueUser();

    // Fill username
    await page.fill('#username', user.username);
    await expect(page.locator('#username')).toHaveClass(/success/);

    // Fill email
    await page.fill('#email', user.email);
    await expect(page.locator('#email')).toHaveClass(/success/);

    // Fill password
    await page.fill('#password', user.password);
    await expect(page.locator('#password')).toHaveClass(/success/);

    // Fill confirm password
    await page.fill('#confirmPassword', user.password);
    await expect(page.locator('#confirmPassword')).toHaveClass(/success/);
  });

  test('should accept valid email formats', async ({ page }) => {
    const validEmails = [
      'user@example.com',
      'user.name@example.com',
      'user+tag@example.co.uk',
      'user123@test-domain.com',
    ];

    for (const email of validEmails) {
      await page.fill('#email', '');
      await page.fill('#email', email);
      await expect(page.locator('#email')).toHaveClass(/success/);
      await expect(page.locator('#emailError')).not.toBeVisible();
    }
  });

  test('should accept password with minimum 8 characters', async ({ page }) => {
    await page.fill('#password', 'Pass1234');
    await expect(page.locator('#password')).toHaveClass(/success/);
    await expect(page.locator('#passwordError')).not.toBeVisible();
  });

  test('should redirect to home page after successful registration', async ({ page }) => {
    const user = generateUniqueUser();

    await page.fill('#username', user.username);
    await page.fill('#email', user.email);
    await page.fill('#password', user.password);
    await page.fill('#confirmPassword', user.password);

    await page.click('button[type="submit"]');

    // Wait for redirect (1.5 seconds according to the code)
    await page.waitForURL('/', { timeout: 3000 });
    expect(page.url()).toContain('/');
  });
});

test.describe('Registration - Negative Tests', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
    await page.goto('/static/register.html');
  });

  test('should show error for short username (< 3 characters)', async ({ page }) => {
    await page.fill('#username', 'ab');
    await page.fill('#email', 'test@example.com'); // Focus away from username
    
    await expect(page.locator('#usernameError')).toBeVisible();
    await expect(page.locator('#usernameError')).toContainText('3-50 characters');
    await expect(page.locator('#username')).toHaveClass(/error/);
  });

  test('should show error for long username (> 50 characters)', async ({ page }) => {
    const longUsername = 'a'.repeat(51);
    await page.fill('#username', longUsername);
    await page.fill('#email', 'test@example.com');
    
    await expect(page.locator('#usernameError')).toBeVisible();
    await expect(page.locator('#username')).toHaveClass(/error/);
  });

  test('should show error for invalid email format', async ({ page }) => {
    const invalidEmails = [
      'notanemail',
      'missing@domain',
      '@nodomain.com',
      'spaces in@email.com',
      'double@@domain.com',
    ];

    for (const email of invalidEmails) {
      await page.fill('#email', '');
      await page.fill('#email', email);
      await page.fill('#username', 'test'); // Focus away
      
      await expect(page.locator('#emailError')).toBeVisible();
      await expect(page.locator('#emailError')).toContainText('valid email');
      await expect(page.locator('#email')).toHaveClass(/error/);
    }
  });

  test('should show error for short password (< 8 characters)', async ({ page }) => {
    await page.fill('#password', 'Short1');
    await page.fill('#confirmPassword', 'Short1');
    await page.click('button[type="submit"]');

    await expect(page.locator('#passwordError')).toBeVisible();
    await expect(page.locator('#passwordError')).toContainText('at least 8 characters');
  });

  test('should show error for mismatched passwords', async ({ page }) => {
    await page.fill('#password', 'Password123');
    await page.fill('#confirmPassword', 'Different456');
    
    await expect(page.locator('#confirmPasswordError')).toBeVisible();
    await expect(page.locator('#confirmPasswordError')).toContainText('do not match');
    await expect(page.locator('#confirmPassword')).toHaveClass(/error/);
  });

  test('should show error when submitting with empty fields', async ({ page }) => {
    await page.click('button[type="submit"]');

    // Alert should show
    await expect(page.locator('.alert-error')).toBeVisible();
    await expect(page.locator('.alert-error')).toContainText('fix the errors');
  });

  test('should show server error for duplicate username', async ({ page }) => {
    const user = generateUniqueUser();

    // Register first time
    await page.fill('#username', user.username);
    await page.fill('#email', user.email);
    await page.fill('#password', user.password);
    await page.fill('#confirmPassword', user.password);
    await page.click('button[type="submit"]');

    // Wait for success
    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    
    // Clear storage and go back to register page
    await clearStorage(page);
    await page.goto('/static/register.html');

    // Try to register with same username but different email
    await page.fill('#username', user.username);
    await page.fill('#email', `different_${user.email}`);
    await page.fill('#password', user.password);
    await page.fill('#confirmPassword', user.password);
    await page.click('button[type="submit"]');

    // Should show error from server
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText('already registered');
  });

  test('should show server error for duplicate email', async ({ page }) => {
    const user = generateUniqueUser();

    // Register first time
    await page.fill('#username', user.username);
    await page.fill('#email', user.email);
    await page.fill('#password', user.password);
    await page.fill('#confirmPassword', user.password);
    await page.click('button[type="submit"]');

    // Wait for success
    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    
    // Clear storage and go back to register page
    await clearStorage(page);
    await page.goto('/static/register.html');

    // Try to register with different username but same email
    await page.fill('#username', `different_${user.username}`);
    await page.fill('#email', user.email);
    await page.fill('#password', user.password);
    await page.fill('#confirmPassword', user.password);
    await page.click('button[type="submit"]');

    // Should show error from server
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText('already registered');
  });

  test('should prevent submission while loading', async ({ page }) => {
    const user = generateUniqueUser();

    await page.fill('#username', user.username);
    await page.fill('#email', user.email);
    await page.fill('#password', user.password);
    await page.fill('#confirmPassword', user.password);

    await page.click('button[type="submit"]');

    // Button should be disabled
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
    
    // Loading spinner should be visible
    await expect(page.locator('.loading-spinner')).toBeVisible();
  });

  test('should redirect already logged in users', async ({ page }) => {
    const user = generateUniqueUser();

    // First register
    await page.fill('#username', user.username);
    await page.fill('#email', user.email);
    await page.fill('#password', user.password);
    await page.fill('#confirmPassword', user.password);
    await page.click('button[type="submit"]');

    // Wait for redirect to home
    await page.waitForURL('/', { timeout: 3000 });

    // Try to go back to register page
    await page.goto('/static/register.html');

    // Should show already logged in message and redirect
    await expect(page.locator('.alert-info')).toBeVisible();
    await expect(page.locator('.alert-info')).toContainText('already logged in');
  });
});
