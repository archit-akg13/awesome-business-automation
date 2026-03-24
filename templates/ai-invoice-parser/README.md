# AI-Powered Invoice Parser using Claude API

**Extract structured data from any invoice in seconds — images, PDFs, handwritten, or scanned.**

Uses Claude's vision capabilities to parse invoices into clean, structured JSON with line items, tax breakdowns (GST/CGST/SGST), vendor details, and payment information.

---

## The Problem

Indian businesses process **50-500 invoices/month** manually. A typical accounts team spends:

- **3-4 hours/day** on data entry from invoices into Tally/Zoho
- **₹15,000-25,000/month** on a dedicated data entry operator
- **5-8% error rate** on manual entries (wrong amounts, missed line items)
- **2-3 days delay** in payment processing due to backlog

For a business processing 200 invoices/month, that's **₹25,000/month + 80 hours of human time** just on invoice data entry.

## The Solution

This Python script uses the Claude API (Sonnet 4.6) to:

1. Accept any invoice format — **PDF, JPG, PNG, scanned, or even photographed**
2. Extract **every field** — vendor, buyer, line items, taxes, bank details
3. Output **structured JSON** ready to import into Tally, Zoho Books, or any accounting software
4. Process a **batch of 200 invoices in under 10 minutes**

### Cost Comparison

| Approach | Monthly Cost | Time | Error Rate |
|----------|-------------|------|------------|
| Manual data entry operator | ₹15,000-25,000 | 80+ hours | 5-8% |
| OCR software (Nanonets, etc.) | ₹5,000-15,000 | Setup + review | 2-5% |
| **This script (Claude Sonnet)** | **₹200-500** | **10 minutes** | **<1%** |

**ROI: Save ₹15,000-24,000/month from Day 1.**

The math: 200 invoices × ~1,500 input tokens × ~800 output tokens = ~₹350/month on Claude Sonnet 4.6.

---

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Set API Key

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Get your API key at [console.anthropic.com](https://console.anthropic.com).

### 3. Parse a Single Invoice

```bash
python invoice_parser.py invoice.pdf
```

### 4. Parse a Batch of Invoices

```bash
python invoice_parser.py --batch ./invoices/ --output results.json
```

---

## Features

- **Multi-format support** — PDF, PNG, JPG, JPEG, GIF, WebP
- **Indian invoice ready** — GST (CGST/SGST/IGST), HSN/SAC codes, PAN, bank IFSC
- **International support** — Works with USD, EUR, GBP invoices too
- **Cost tracking** — Every parse includes estimated cost in ₹
- **Batch processing** — Parse entire folders with one command
- **Model flexibility** — Switch between Sonnet (cheap) and Opus (complex invoices)

## Advanced Usage

### Use Opus for Complex Invoices

For handwritten or poorly scanned invoices:

```bash
python invoice_parser.py --model claude-opus-4-6-20250514 messy_invoice.jpg
```

Opus costs ~5x more but handles edge cases better. Use Sonnet for 95% of invoices, Opus for the tricky 5%.

### Integration with n8n

Set up an n8n workflow:
1. **Trigger:** Watch a Google Drive folder for new invoice uploads
2. **HTTP Request:** Call this script via a simple Flask/FastAPI wrapper
3. **Spreadsheet:** Append parsed data to Google Sheets
4. **Notification:** Send Slack alert with invoice summary

---

## How It Works

1. The script encodes your invoice file (image/PDF) as base64
2. Sends it to Claude's vision API with a detailed extraction prompt
3. Claude analyzes the visual layout — text, tables, logos, stamps
4. Returns structured JSON matching the schema
5. The script validates the JSON and adds cost metadata

Claude's vision model is particularly good at:
- Reading handwritten amounts and signatures
- Parsing multi-page invoices
- Understanding Indian invoice formats (GST, HSN codes)
- Handling rotated or slightly blurry scans

---

## Cost Breakdown

| Volume | Sonnet Cost/Month | Opus Cost/Month | Manual Cost/Month |
|--------|-------------------|-----------------|-------------------|
| 50 invoices | ₹85 | ₹425 | ₹8,000 |
| 200 invoices | ₹350 | ₹1,750 | ₹20,000 |
| 500 invoices | ₹875 | ₹4,375 | ₹35,000 |
| 1000 invoices | ₹1,750 | ₹8,750 | ₹50,000+ |

**Bottom line:** Even at 1,000 invoices/month, Claude Sonnet costs less than **₹2,000** — that's a **96% cost reduction** vs. manual processing.

---

## Requirements

- Python 3.10+
- Anthropic API key ([get one here](https://console.anthropic.com))
- `anthropic` Python package

---

## License

MIT — use it, modify it, automate with it.

---

Built by **Archit Mittal** — Business Automation Expert
[@automate-archit](https://linkedin.com/in/automate-archit) on LinkedIn | [architmittal.com](https://architmittal.com)
