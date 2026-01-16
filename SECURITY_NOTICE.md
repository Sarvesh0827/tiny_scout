## ⚠️ SECURITY NOTICE

**Your previous Anthropic API key was exposed in this conversation.**

### Immediate Action Required:

1. **Revoke the old key**: Go to https://console.anthropic.com/settings/keys
2. **Generate a new key**: Create a fresh API key
3. **Update your .env file**:
   ```bash
   python setup_api_key.py
   ```
   Or manually edit `.env`:
   ```
   ANTHROPIC_API_KEY=your_new_key_here
   ANTHROPIC_MODEL=claude-sonnet-4-5
   ```

### Security Best Practices:
- ✅ Never commit `.env` files to git (already in `.gitignore`)
- ✅ Rotate API keys regularly
- ✅ Use environment variables for all secrets
- ✅ Revoke keys immediately if exposed

**The `.env` file is already in `.gitignore` to prevent future exposure.**
