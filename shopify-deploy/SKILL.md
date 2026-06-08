---
name: shopify-deploy
description: |-
  Deploy Shopify themes safely. Always confirm development vs live theme before pushing. Validate Liquid, test mobile responsiveness, never push to live without explicit approval.
---

# Shopify Deploy Skill
1. Ask user: development or live theme? Get explicit confirmation.
2. Run `shopify theme list` to identify correct theme ID
3. Validate all Liquid files before upload: `shopify theme check`
4. Push to DEVELOPMENT theme only unless user explicitly confirms live
5. Test mobile responsiveness on key pages
6. Report summary of files changed
