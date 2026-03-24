"""
AI-Powered Invoice Parser using Claude API
===========================================
Extracts structured data from invoice images/PDFs using Claude's vision capabilities.
Outputs clean JSON with line items, totals, vendor info, and tax breakdowns.

Author: Archit Mittal (@automate-archit on LinkedIn)
License: MIT
"""

import anthropic
import base64
import json
import sys
import os
from pathlib import Path


def encode_file(file_path: str) -> tuple[str, str]:
    """Encode a file (image or PDF) to base64 and detect its media type."""
    path = Path(file_path)
    ext = path.suffix.lower()

    media_type_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
    }

    if ext not in media_type_map:
        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Supported: {', '.join(media_type_map.keys())}"
        )

    media_type = media_type_map[ext]

    with open(file_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    return data, media_type


EXTRACTION_PROMPT = """You are an expert invoice parser. Extract ALL structured data from this invoice.

Return ONLY valid JSON with this exact schema (no markdown, no explanation):

{
  "vendor": {
    "name": "string",
    "address": "string or null",
    "gstin": "string or null",
    "pan": "string or null",
    "email": "string or null",
    "phone": "string or null"
  },
  "buyer": {
    "name": "string or null",
    "address": "string or null",
    "gstin": "string or null"
  },
  "invoice_number": "string",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD or null",
  "currency": "INR or USD or other",
  "line_items": [
    {
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "amount": number,
      "hsn_sac_code": "string or null"
    }
  ],
  "subtotal": number,
  "discount": number or null,
  "tax_details": {
    "cgst": number or null,
    "sgst": number or null,
    "igst": number or null,
    "gst_total": number or null,
    "tax_rate_percent": number or null
  },
  "total_amount": number,
  "amount_in_words": "string or null",
  "payment_terms": "string or null",
  "bank_details": {
    "bank_name": "string or null",
    "account_number": "string or null",
    "ifsc": "string or null"
  },
  "notes": "string or null"
}

Rules:
- All monetary values should be numbers (not strings)
- Dates in YYYY-MM-DD format
- If a field is not found on the invoice, use null
- For Indian invoices, extract GST details (CGST/SGST/IGST)
- Extract HSN/SAC codes if present
- Be precise with line item amounts — verify they add up to the subtotal
"""


def parse_invoice(
    file_path: str,
    model: str = "claude-sonnet-4-6-20250514",
    max_tokens: int = 4096,
) -> dict:
    """
    Parse an invoice file and extract structured data.

    Args:
        file_path: Path to invoice image or PDF
        model: Claude model to use (default: claude-sonnet-4-6 for cost efficiency)
        max_tokens: Maximum tokens in response

    Returns:
        Dictionary with extracted invoice data
    """
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    file_data, media_type = encode_file(file_path)

    # Build the content based on file type
    if media_type == "application/pdf":
        file_content = {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": file_data,
            },
        }
    else:
        file_content = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": file_data,
            },
        }

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "user",
                "content": [
                    file_content,
                    {"type": "text", "text": EXTRACTION_PROMPT},
                ],
            }
        ],
    )

    # Extract JSON from response
    response_text = message.content[0].text.strip()

    # Handle potential markdown code blocks in response
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0]

    parsed = json.loads(response_text)

    # Add metadata
    parsed["_metadata"] = {
        "source_file": os.path.basename(file_path),
        "model_used": model,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "estimated_cost_inr": estimate_cost_inr(
            message.usage.input_tokens, message.usage.output_tokens, model
        ),
    }

    return parsed


def estimate_cost_inr(
    input_tokens: int, output_tokens: int, model: str
) -> float:
    """
    Estimate API cost in INR.

    Pricing (as of March 2026):
    - Claude Sonnet 4.6: $3/M input, $15/M output
    - Claude Opus 4.6: $15/M input, $75/M output
    USD to INR rate: ~84
    """
    pricing = {
        "claude-sonnet-4-6-20250514": {
            "input_per_m": 3.0,
            "output_per_m": 15.0,
        },
        "claude-opus-4-6-20250514": {
            "input_per_m": 15.0,
            "output_per_m": 75.0,
        },
    }

    usd_to_inr = 84.0

    rates = pricing.get(
        model, {"input_per_m": 3.0, "output_per_m": 15.0}
    )

    cost_usd = (input_tokens / 1_000_000 * rates["input_per_m"]) + (
        output_tokens / 1_000_000 * rates["output_per_m"]
    )

    return round(cost_usd * usd_to_inr, 2)


def parse_batch(
    folder_path: str,
    output_file: str = "parsed_invoices.json",
    model: str = "claude-sonnet-4-6-20250514",
) -> list[dict]:
    """
    Parse all invoices in a folder and save results to JSON.

    Args:
        folder_path: Path to folder containing invoice files
        output_file: Output JSON file path
        model: Claude model to use

    Returns:
        List of parsed invoice dictionaries
    """
    supported = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"}
    folder = Path(folder_path)

    files = [f for f in folder.iterdir() if f.suffix.lower() in supported]
    print(f"Found {len(files)} invoice(s) to parse.")

    results = []
    total_cost = 0.0

    for i, file in enumerate(sorted(files), 1):
        print(f"[{i}/{len(files)}] Parsing: {file.name}...", end=" ")
        try:
            parsed = parse_invoice(str(file), model=model)
            results.append(parsed)
            cost = parsed["_metadata"]["estimated_cost_inr"]
            total_cost += cost
            print(f"OK (\u20b9{cost})")
        except Exception as e:
            print(f"FAILED: {e}")
            results.append(
                {
                    "error": str(e),
                    "_metadata": {"source_file": file.name},
                }
            )

    # Save results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Parsed {len(results)} invoices.")
    print(f"Total estimated cost: \u20b9{total_cost:.2f}")
    print(f"Results saved to: {output_file}")

    return results


# --- CLI Interface ---

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single invoice:  python invoice_parser.py invoice.pdf")
        print("  Batch folder:    python invoice_parser.py --batch ./invoices/")
        print("")
        print("Options:")
        print("  --model MODEL    Claude model (default: claude-sonnet-4-6-20250514)")
        print("  --output FILE    Output JSON file (default: parsed_invoices.json)")
        print("")
        print("Environment:")
        print("  ANTHROPIC_API_KEY  Your Anthropic API key (required)")
        sys.exit(1)

    # Simple arg parsing
    args = sys.argv[1:]
    model = "claude-sonnet-4-6-20250514"
    output = "parsed_invoices.json"

    if "--model" in args:
        idx = args.index("--model")
        model = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if "--output" in args:
        idx = args.index("--output")
        output = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if "--batch" in args:
        idx = args.index("--batch")
        folder = args[idx + 1] if idx + 1 < len(args) else "."
        parse_batch(folder, output_file=output, model=model)
    else:
        file_path = args[0]
        result = parse_invoice(file_path, model=model)
        print(json.dumps(result, indent=2, ensure_ascii=False))
