# Anne — Sprint 2 Seller Review

## 1. Seller journey

1. Open the Lead List and identify businesses that may be worth contacting.
2. Review the business name, sector, area, phone number, website status and lead status.
3. Open a promising lead to check its contact details and research notes.
4. Check the activity history before deciding on the next action.

## 2. What the Lead List must show

- Business name, sector and area.
- Phone number, with missing information clearly indicated.
- Website status and lead status.
- Search and filters that help sellers find leads quickly.
- A clear indication of which filters are active.

## 3. What the Lead Detail must show

- Business name, sector and area.
- Phone number and WhatsApp availability.
- Website information and the original research note.
- Source and date added.
- Activity history showing recorded events and when they happened.

## 4. Seller-perspective recommendations

1. Make it quick to find a business by name, phone number or area.
2. Make businesses without a website easy to identify as potential sales opportunities.
3. Distinguish missing information from a confirmed negative answer. For example, an unknown phone number should not look like a business has no phone.
4. Keep the current table layout and place search and filters above it rather than redesigning the screen.
5. Explain rejected CSV rows in plain language, including what needs to be corrected.

## 5. Sample-data consistency

The frontend fixtures currently contain six leads, while the backend seed contains eight. The backend includes examples with an existing website and missing contact information. Keeping useful edge cases consistent across both sets would make seller testing more reliable.

## 6. PR review checks

- Sharon's importer: Does each rejection message explain what is wrong and how to fix it?
- Herman's filters: Can a seller find a target lead quickly, and do the filters persist when the URL is opened in a fresh tab?

## 7. Before showing real businesses

Confirm that sellers can distinguish verified information from missing or incomplete research, and can quickly find a promising lead without guessing.
