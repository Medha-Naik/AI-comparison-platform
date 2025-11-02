# Email Notification Setup Instructions

## Problem
Email notifications are not being sent when target price is reached.

## Solution
Email notifications require SMTP configuration. Follow these steps to enable email alerts.

## Gmail Setup (Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security**
3. Enable **2-Step Verification** if not already enabled

### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select **Mail** as the app
3. Select **Other (Custom name)** as the device, enter "Shopping Assistant"
4. Click **Generate**
5. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 3: Set Environment Variables
Create a `.env` file in your project root (or set these in your system environment):

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
```

**Important:** 
- Use your **actual Gmail address** for `SMTP_USERNAME`
- Use the **16-character App Password** (remove spaces) for `SMTP_PASSWORD`
- **NOT** your regular Gmail password!

### Step 4: Restart Your Application
Restart your Flask application for the environment variables to take effect.

## Testing Email Notifications

1. Add a product to your wishlist
2. Set a target price **below** the current lowest price
3. The system will immediately check and send an email if the condition is met
4. Check your server console logs for detailed email sending status:
   - `[EMAIL] ✅` = Email sent successfully
   - `[EMAIL] ❌` = Error (check the error message)
   - `[EMAIL] SMTP NOT CONFIGURED` = Environment variables not set

## Troubleshooting

### Email Not Sending
1. **Check console logs** - Look for `[EMAIL]` messages in your server output
2. **Verify environment variables** - Make sure `.env` file is loaded or variables are set
3. **Test SMTP connection** - The logs will show connection errors
4. **Check spam folder** - Emails might be filtered as spam initially

### Common Errors

**SMTP Authentication Error:**
- You're using your regular password instead of App Password
- Generate a new App Password and update `SMTP_PASSWORD`

**Connection Refused:**
- Check your firewall settings
- Verify `SMTP_SERVER` and `SMTP_PORT` are correct

**Email Not Found:**
- Make sure your user account has an email address
- Check the database to verify user.email is set

## Alternative Email Providers

### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your.email@outlook.com
SMTP_PASSWORD=your-app-password
```

### Yahoo
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your.email@yahoo.com
SMTP_PASSWORD=your-app-password
```

## Verification

After setup, check your server console. You should see:
```
[PRICE ALERT] Checking alerts for item X...
[PRICE ALERT] ✅ Price condition met!
[EMAIL] Attempting to send price alert to user@email.com...
[EMAIL] ✅ Price alert email successfully sent to user@email.com
```

If you see errors, they will be clearly marked with `❌` and include details on what went wrong.
