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
  await page.goto('/static/login.html');
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
}

/**
 * Helper function to register a test user
 */
async function registerUser(page, user) {
  await page.goto('/static/register.html');
  await page.fill('#username', user.username);
  await page.fill('#email', user.email);
  await page.fill('#password', user.password);
  await page.fill('#confirmPassword', user.password);
  await page.click('button[type="submit"]');
  await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
  await clearStorage(page);
}

test.describe('Login - Positive Tests', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('should successfully login with valid username and password', async ({ page }) => {
    const user = generateUniqueUser();
    
    // First register the user
    await registerUser(page, user);

    // Now login
    await page.goto('/static/login.html');
    await page.fill('#username', user.username);
    await page.fill('#password', user.password);
    await page.click('button[type="submit"]');

    // Wait for success message
    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-success')).toContainText('Login successful');

    // Verify JWT token is stored (default: sessionStorage)
    const token = await page.evaluate(() => sessionStorage.getItem('access_token'));
    expect(token).toBeTruthy();
    expect(token).toMatch(/^eyJ/); // JWT tokens start with 'eyJ'

    // Verify user data is stored
    const storedUser = await page.evaluate(() => sessionStorage.getItem('user'));
    expect(storedUser).toBeTruthy();
    const userData = JSON.parse(storedUser);
    expect(userData.username).toBe(user.username);
    expect(userData.email).toBe(user.email);

    // Verify token type
    const tokenType = await page.evaluate(() => sessionStorage.getItem('token_type'));
    expect(tokenType).toBe('bearer');
  });

  test('should successfully login with email instead of username', async ({ page }) => {
    const user = generateUniqueUser();
    
    // First register the user
    await registerUser(page, user);

    // Now login with email
    await page.goto('/static/login.html');
    await page.fill('#username', user.email);  // Using email field
    await page.fill('#password', user.password);
    await page.click('button[type="submit"]');

    // Wait for success message
    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    
    // Verify token is stored
    const token = await page.evaluate(() => sessionStorage.getItem('access_token'));
    expect(token).toBeTruthy();
  });

  test('should store token in localStorage when "Remember Me" is checked', async ({ page }) => {
    const user = generateUniqueUser();
    
    // First register the user
    await registerUser(page, user);

    // Login with Remember Me checked
    await page.goto('/static/login.html');
    await page.fill('#username', user.username);
    await page.fill('#password', user.password);
    await page.check('#rememberMe');
    await page.click('button[type="submit"]');

    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });

    // Verify token is in localStorage (not sessionStorage)
    const localToken = await page.evaluate(() => localStorage.getItem('access_token'));
    const sessionToken = await page.evaluate(() => sessionStorage.getItem('access_token'));
    
    expect(localToken).toBeTruthy();
    expect(sessionToken).toBeNull();
  });

  test('should store token in sessionStorage when "Remember Me" is unchecked', async ({ page }) => {
    const user = generateUniqueUser();
    
    // First register the user
    await registerUser(page, user);

    // Login without Remember Me
    await page.goto('/static/login.html');
    await page.fill('#username', user.username);
    await page.fill('#password', user.password);
    // Don't check rememberMe
    await page.click('button[type="submit"]');

    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });

    // Verify token is in sessionStorage (not localStorage)
    const localToken = await page.evaluate(() => localStorage.getItem('access_token'));
    const sessionToken = await page.evaluate(() => sessionStorage.getItem('access_token'));
    
    expect(sessionToken).toBeTruthy();
    expect(localToken).toBeNull();
  });

  test('should redirect to home page after successful login', async ({ page }) => {
    const user = generateUniqueUser();
    
    // First register the user
    await registerUser(page, user);

    // Login
    await page.goto('/static/login.html');
    await page.fill('#username', user.username);
    await page.fill('#password', user.password);
    await page.click('button[type="submit"]');

    // Wait for redirect (1 second according to the code)
    await page.waitForURL('/', { timeout: 3000 });
    expect(page.url()).toContain('/');
  });

  test('should show success state on valid inputs', async ({ page }) => {
    await page.goto('/static/login.html');
    
    await page.fill('#username', 'testuser');
    await expect(page.locator('#username')).toHaveClass(/success/);

    await page.fill('#password', 'password123');
    await expect(page.locator('#password')).toHaveClass(/success/);
  });

  test('should log user information to console', async ({ page }) => {
    const user = generateUniqueUser();
    
    // First register the user
    await registerUser(page, user);

    // Listen for console logs
    const consoleLogs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'log') {
        consoleLogs.push(msg.text());
      }
    });

    // Login
    await page.goto('/static/login.html');
    await page.fill('#username', user.username);
    await page.fill('#password', user.password);
    await page.click('button[type="submit"]');

    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });

    // Wait a bit for console logs
    await page.waitForTimeout(500);

    // Verify console logs contain token and user info
    const hasTokenLog = consoleLogs.some(log => log.includes('JWT Token stored'));
    const hasUserLog = consoleLogs.some(log => log.includes('User info'));
    
    expect(hasTokenLog || hasUserLog).toBeTruthy();
  });
});

test.describe('Login - Negative Tests', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('should show error for empty username', async ({ page }) => {
    await page.goto('/static/login.html');
    
    await page.fill('#password', 'somepassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('#usernameError')).toBeVisible();
    await expect(page.locator('#usernameError')).toContainText('username or email');
  });

  test('should show error for empty password', async ({ page }) => {
    await page.goto('/static/login.html');
    
    await page.fill('#username', 'someuser');
    await page.click('button[type="submit"]');

    await expect(page.locator('#passwordError')).toBeVisible();
    await expect(page.locator('#passwordError')).toContainText('password');
  });

  test('should show error when submitting empty form', async ({ page }) => {
    await page.goto('/static/login.html');
    
    await page.click('button[type="submit"]');

    await expect(page.locator('.alert-error')).toBeVisible();
    await expect(page.locator('.alert-error')).toContainText('required fields');
  });

  test('should show 401 error for wrong password', async ({ page }) => {
    const user = generateUniqueUser();
    
    // First register the user
    await registerUser(page, user);

    // Try to login with wrong password
    await page.goto('/static/login.html');
    await page.fill('#username', user.username);
    await page.fill('#password', 'WrongPassword123!');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText('Invalid username or password');

    // Token should NOT be stored
    const localToken = await page.evaluate(() => localStorage.getItem('access_token'));
    const sessionToken = await page.evaluate(() => sessionStorage.getItem('access_token'));
    expect(localToken).toBeNull();
    expect(sessionToken).toBeNull();
  });

  test('should show 401 error for non-existent user', async ({ page }) => {
    await page.goto('/static/login.html');
    
    await page.fill('#username', 'nonexistentuser12345');
    await page.fill('#password', 'SomePassword123!');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText('Invalid username or password');

    // Token should NOT be stored
    const localToken = await page.evaluate(() => localStorage.getItem('access_token'));
    const sessionToken = await page.evaluate(() => sessionStorage.getItem('access_token'));
    expect(localToken).toBeNull();
    expect(sessionToken).toBeNull();
  });

  test('should clear password field after failed login', async ({ page }) => {
    await page.goto('/static/login.html');
    
    await page.fill('#username', 'wronguser');
    await page.fill('#password', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Wait for error
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });

    // Password field should be empty
    const passwordValue = await page.inputValue('#password');
    expect(passwordValue).toBe('');
  });

  test('should re-enable submit button after failed login', async ({ page }) => {
    await page.goto('/static/login.html');
    
    await page.fill('#username', 'wronguser');
    await page.fill('#password', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Wait for error
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });

    // Button should be enabled again
    await expect(page.locator('button[type="submit"]')).toBeEnabled();
    
    // Loading class should be removed
    const hasLoadingClass = await page.locator('button[type="submit"]').evaluate(
      el => el.classList.contains('loading')
    );
    expect(hasLoadingClass).toBe(false);
  });

  test('should disable submit button while loading', async ({ page }) => {
    const user = generateUniqueUser();
    await registerUser(page, user);

    await page.goto('/static/login.html');
    await page.fill('#username', user.username);
    await page.fill('#password', user.password);
    
    await page.click('button[type="submit"]');

    // Button should be disabled immediately
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
    
    // Loading spinner should be visible
    await expect(page.locator('.loading-spinner')).toBeVisible();
  });

  test('should redirect already logged in users', async ({ page }) => {
    const user = generateUniqueUser();
    
    // Register and login
    await registerUser(page, user);
    await page.goto('/static/login.html');
    await page.fill('#username', user.username);
    await page.fill('#password', user.password);
    await page.click('button[type="submit"]');

    // Wait for redirect
    await page.waitForURL('/', { timeout: 3000 });

    // Try to go back to login page
    await page.goto('/static/login.html');

    // Should show already logged in message and redirect
    await expect(page.locator('.alert-info')).toBeVisible();
    await expect(page.locator('.alert-info')).toContainText('already logged in');
  });

  test('should handle network errors gracefully', async ({ page }) => {
    await page.goto('/static/login.html');
    
    // Intercept and fail the request
    await page.route('**/users/login', route => route.abort());

    await page.fill('#username', 'testuser');
    await page.fill('#password', 'password123');
    await page.click('button[type="submit"]');

    // Should show network error
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText(/network|connection/i);
  });

  test('should show error message from server for inactive account', async ({ page }) => {
    // This test would require a way to deactivate a user account
    // For now, we'll test the UI behavior assuming a 403 response
    
    await page.goto('/static/login.html');
    
    // Mock a 403 response
    await page.route('**/users/login', route => {
      route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'User account is inactive' })
      });
    });

    await page.fill('#username', 'inactiveuser');
    await page.fill('#password', 'password123');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText('inactive');
  });

  test('should handle validation errors from server', async ({ page }) => {
    await page.goto('/static/login.html');
    
    // Mock a 422 validation error response
    await page.route('**/users/login', route => {
      route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: [
            { loc: ['body', 'username'], msg: 'field required', type: 'value_error.missing' }
          ]
        })
      });
    });

    await page.fill('#username', 'test');
    await page.fill('#password', 'password');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Login - UI/UX Tests', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
    await page.goto('/static/login.html');
  });

  test('should display forgot password link', async ({ page }) => {
    const forgotLink = page.locator('.forgot-password');
    await expect(forgotLink).toBeVisible();
    await expect(forgotLink).toHaveText('Forgot password?');
  });

  test('should show info message when clicking forgot password', async ({ page }) => {
    await page.click('.forgot-password');
    
    await expect(page.locator('.alert-info')).toBeVisible();
    await expect(page.locator('.alert-info')).toContainText('coming soon');
  });

  test('should have link to register page', async ({ page }) => {
    const registerLink = page.locator('a[href="register.html"]');
    await expect(registerLink).toBeVisible();
    await expect(registerLink).toContainText('Register here');
  });

  test('should navigate to register page when clicking register link', async ({ page }) => {
    await page.click('a[href="register.html"]');
    await expect(page).toHaveURL(/register\.html/);
  });

  test('should have proper form labels', async ({ page }) => {
    await expect(page.locator('label[for="username"]')).toContainText('Username or Email');
    await expect(page.locator('label[for="password"]')).toContainText('Password');
  });

  test('should have proper input placeholders', async ({ page }) => {
    await expect(page.locator('#username')).toHaveAttribute('placeholder', /username or email/i);
    await expect(page.locator('#password')).toHaveAttribute('placeholder', /password/i);
  });
});
