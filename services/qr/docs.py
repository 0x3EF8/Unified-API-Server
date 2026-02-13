"""QR Code Generator — API documentation and examples.

Auto-loaded by the service loader for the tester Docs tab.
"""

NOTES = [
    "Returns the QR code image directly — <code>png</code>, <code>svg</code>, <code>pdf</code>, <code>eps</code>, or <code>txt</code>",
    "For WiFi QR codes, use <code>ssid</code> instead of <code>data</code>",
    "Custom colors accept CSS color names, hex (<code>#FF0000</code>), or RGB values",
    "Error correction levels: <strong>L</strong> (7%), <strong>M</strong> (15%), <strong>Q</strong> (25%), <strong>H</strong> (30%)",
]

EXAMPLES = [
    {
        "title": "Website URL",
        "description": "QR code linking to a website — scan with any phone camera",
        "body": {"data": "https://github.com"},
    },
    {
        "title": "YouTube Video Link",
        "description": "Share a YouTube video via QR code",
        "body": {"data": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    },
    {
        "title": "Facebook Profile / Page",
        "description": "Link to a Facebook page or profile",
        "body": {"data": "https://www.facebook.com/yourpage"},
    },
    {
        "title": "Instagram Profile",
        "description": "Generate a QR code for an Instagram profile",
        "body": {"data": "https://www.instagram.com/yourprofile"},
    },
    {
        "title": "TikTok Profile",
        "description": "Share a TikTok profile via QR code",
        "body": {"data": "https://www.tiktok.com/@yourusername"},
    },
    {
        "title": "Twitter / X Profile",
        "description": "Link to a Twitter/X profile",
        "body": {"data": "https://x.com/yourusername"},
    },
    {
        "title": "Email Address (Mailto)",
        "description": "Opens the email app with a pre-filled recipient",
        "body": {"data": "mailto:contact@example.com?subject=Hello"},
    },
    {
        "title": "Phone Number",
        "description": "Scan to call a phone number directly",
        "body": {"data": "tel:+1234567890"},
    },
    {
        "title": "SMS Message",
        "description": "Opens SMS with a pre-filled message",
        "body": {"data": "sms:+1234567890?body=Hello from QR!"},
    },
    {
        "title": "Plain Text",
        "description": "Encode any text content into a QR code",
        "body": {"data": "Meeting at 3 PM in Conference Room B"},
    },
    {
        "title": "vCard (Contact Card)",
        "description": "Save a contact directly to phone — supports name, phone, email",
        "body": {"data": "BEGIN:VCARD\nVERSION:3.0\nFN:John Doe\nTEL:+1234567890\nEMAIL:john@example.com\nEND:VCARD"},
    },
    {
        "title": "WiFi Network",
        "description": "Scan to auto-connect to a WiFi network — no typing passwords",
        "body": {"ssid": "MyWiFi", "password": "supersecret123", "security": "WPA"},
    },
    {
        "title": "WiFi (Hidden Network)",
        "description": "Connect to a hidden WiFi network",
        "body": {"ssid": "HiddenNet", "password": "secret", "security": "WPA", "hidden": True},
    },
    {
        "title": "WiFi (Open / No Password)",
        "description": "QR for an open WiFi network without a password",
        "body": {"ssid": "CoffeeShop_Free", "security": "nopass"},
    },
    {
        "title": "Custom Styled QR",
        "description": "Custom colors, high error correction, SVG format",
        "body": {"data": "https://example.com", "dark": "#1a1a2e", "light": "#e0e0e8", "error_correction": "H", "format": "svg", "scale": 15, "border": 2},
    },
    {
        "title": "Calendar Event",
        "description": "Add an event directly to calendar app",
        "body": {"data": "BEGIN:VEVENT\nSUMMARY:Team Meeting\nDTSTART:20260301T140000\nDTEND:20260301T150000\nLOCATION:Room 101\nEND:VEVENT"},
    },
    {
        "title": "Geo Location",
        "description": "Open a location in maps — great for business addresses",
        "body": {"data": "geo:40.7128,-74.0060?q=New+York+City"},
    },
]

CODE_EXAMPLES = {
    "curl": '''curl -X POST '{base_url}/qr' \\
  -H 'Content-Type: application/json' \\
  -d '{
  "data": "https://github.com"
}' --output qrcode.png''',

    "python": '''import requests

response = requests.post(
    "{base_url}/qr",
    json={
        "data": "https://github.com"
    }
)

# Save the QR code image
with open("qrcode.png", "wb") as f:
    f.write(response.content)
print(f"Saved qrcode.png ({{len(response.content)}} bytes)")''',

    "javascript": '''const response = await fetch("{base_url}/qr", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    "data": "https://github.com"
  })
});

// Display the QR code image
const blob = await response.blob();
const url = URL.createObjectURL(blob);
const img = document.createElement("img");
img.src = url;
document.body.appendChild(img);''',
}
