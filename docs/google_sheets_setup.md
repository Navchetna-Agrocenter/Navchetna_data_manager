# Google Sheets Integration Setup Guide

This guide will walk you through setting up Google Sheets as a persistent storage solution for the Plantation Data Management System.

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click on the project dropdown at the top of the page
4. Click "New Project"
5. Enter a name for your project (e.g., "Navchetna Plantation Manager")
6. Click "Create"

## Step 2: Enable Required APIs

1. From the Google Cloud Console dashboard, navigate to "APIs & Services" > "Library"
2. Search for and enable the following APIs:
   - Google Sheets API
   - Google Drive API

## Step 3: Create a Service Account

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" and select "Service Account"
3. Enter a name for your service account (e.g., "plantation-app-service")
4. Add a description (optional)
5. Click "Create and Continue"
6. For the "Service account permissions" step, you can skip by clicking "Continue"
7. For the "Grant users access" step, you can skip by clicking "Done"

## Step 4: Create Service Account Key

1. On the Credentials page, find your newly created service account
2. Click on the service account name to view its details
3. Go to the "Keys" tab
4. Click "Add Key" > "Create new key"
5. Select "JSON" as the key type
6. Click "Create"
7. The JSON key file will be downloaded to your computer
8. Save this file securely - it contains sensitive credentials!

## Step 5: Configure Your Application

You have three options to add the credentials to your application:

### Option 1: Local Development (service_account.json)

1. Rename the downloaded JSON file to `service_account.json`
2. Place it in the root directory of your application
3. Add `service_account.json` to your `.gitignore` file to avoid committing sensitive credentials

### Option 2: Streamlit Cloud Secrets

1. In your Streamlit Cloud dashboard, go to your app settings
2. Find the "Secrets" section
3. Add the entire contents of your JSON file as follows:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
YOUR_PRIVATE_KEY_HERE
-----END PRIVATE KEY-----
"""
client_email = "your-service-account@your-project-id.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
```

### Option 3: Environment Variables

1. Set an environment variable named `GOOGLE_SHEETS_CREDS` with the entire contents of your JSON file
2. For Streamlit Cloud, you can set this as a secret:

```toml
GOOGLE_SHEETS_CREDS = '{"type":"service_account","project_id":"your-project-id",...}'
```

## Step 6: Test Your Integration

1. Run your application locally: `streamlit run app.py`
2. Check the application output for confirmation of Google Sheets connection
3. Add some test data to verify it's being saved to Google Sheets

## How It Works

- When your application starts, it tries to connect to Google Sheets
- If successful, it sets the `deployment_mode` to "gsheets"
- All data operations (read/write) are directed to Google Sheets instead of local files
- For each project, a separate spreadsheet is created
- Each data type (KML tracking, plantation records, etc.) is saved as a separate worksheet

## Troubleshooting

### Connection Issues

- Verify that your service account credentials are correct
- Check that the Google Sheets API and Google Drive API are enabled
- Make sure your service account has the necessary permissions

### Permission Denied Errors

If you see "Permission denied" errors:

1. Open one of the automatically created Google Sheets
2. Click "Share" in the top-right corner
3. Add your service account email (found in the JSON file as `client_email`)
4. Give it "Editor" access
5. Click "Send"

### Rate Limiting

Google APIs have usage limits. If you encounter rate limiting:

1. Implement caching in your application
2. Reduce the frequency of reads/writes
3. Consider upgrading to a paid Google Cloud account for higher limits

## Security Considerations

- Never commit your service account JSON file to a public repository
- Use Streamlit secrets or environment variables for deployment
- Regularly rotate your service account keys
- Limit the permissions of your service account to only what's needed

## Need Help?

If you encounter any issues or need assistance, please:

1. Check the [gspread documentation](https://gspread.readthedocs.io/)
2. Review the [Google Sheets API documentation](https://developers.google.com/sheets/api)
3. Contact your system administrator or the application developer 