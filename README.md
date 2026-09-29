# GST Verification Pro (App & API)

A modern, fast, and comprehensive GSTIN verification application and REST API that fetches official taxpayer details directly from the Government GST portal (`services.gst.gov.in`).

---

## 🚀 Quick Start (One-Click)

If you are on Windows, simply **double-click** [`start.bat`](start.bat). It will automatically launch the server and open the web dashboard in your browser at:

👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## ✨ Features

- **Interactive Web Dashboard**: Beautiful, clean UI accessible at `http://127.0.0.1:5000`.
- **Live State & PAN Intelligence**: Automatically detects the Indian State/UT and extracts the PAN as you type the GSTIN.
- **Dynamic Captcha Handling**: Live captcha rendering with a 1-click reload button and auto-refresh on failed attempts.
- **Structured Taxpayer Details**:
  - Legal Name, Trade Name, Constitution of Business
  - Active / Cancelled status badges with cancellation dates
  - Complete Principal Place of Business address
  - Nature of Business Activity tags (Wholesale, Retail, Manufacturing, etc.)
  - Centre and State tax jurisdictions, Aadhaar verification, and e-Invoice status.
- **Productivity Tools**:
  - **Copy Summary**: Formats details into a clean text summary ready for email or WhatsApp.
  - **Print / PDF**: Clean, print-ready document view.
  - **Search History**: Saves recent lookups in your browser for quick review.
- **REST API Support**: Fully backward-compatible endpoints (`/api/v1/getCaptcha` and `/api/v1/getGSTDetails`) for automated scripts, Postman, and backend integrations.

---

## 🛠 Manual Installation

1. Open your terminal in this repository:
   ```powershell
   cd D:\Applications_Github\GST-Verification-API\GST-Verification-API
   ```

2. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\activate
   ```

3. Run the application:
   ```powershell
   python app.py
   ```

4. Open **http://127.0.0.1:5000** in your browser.
  
## EndPoints

### Fetching Captcha

**Endpoint:** `/api/v1/getCaptcha`

**Method:** `GET`

**Description:** `This Endpoint gets the current instance of captcha from that website as a base64 encoding`

**Response**
```json
{
  "sessionId": "someencoding",
  "image": 'data:image/png;base64, captchaBase64 '
}
```
**Status Codes**
- 200 OK : `Captcha Recieved`

### Get GST Details to verify

**Endpoint:** `/api/v1/getGSTDetails`

**Method:** `POST`

**Description:** `Submits the GSTIN and captcha given, to the website and extract or scrap further GSTIN Taxpayer Details`

**Request Body:**
```json
{
  "sessionId": "OBTAINED ON FETCHING CAPTCHA",
  "GSTIN": "01ABCDE0123F0AA",
  "captcha": "your_captcha_here"
}
```
**Response**
```json
{
    "adhrVFlag": "Yes",
    "adhrVdt": "29/01/2021",
    "cmpRt": "NA",
    "ctb": "Proprietorship",
    "ctj": "Address",
    "cxdt": "",
    "dty": "Regular",
    "einvoiceStatus": "No",
    "ekycVFlag": "Not Applicable",
    "gstin": "01ABCDE0123F0AA",
    "isFieldVisitConducted": "No",
    "lgnm": "ABCDEF GHIJK",
    "nba": [
        "Retail Business",
        "Wholesale Business",
        "Supplier of Services"
    ],
    "ntcrbs": "TRD:TRR",
    "pradr": {
        "adr": "Address"
    },
    "rgdt": "Registration Date",
    "stj": "Division",
    "sts": "Status",
    "tradeNam": "Trade Name"
}
```
**Status Codes**
- 200 OK : `Data Retrieved Successfuly`

## Support
For Support Contact me at itzshubhamofficial@gmail.com
or Mobile Number : `+917687877772`

Hosted support and onboarding:

- https://gstverify.dubey.app/support
- https://api.gstverify.dubey.app

## Contribution

We welcome contributions to improve this project. Here are some ways you can contribute:

1. **Report Bugs:** If you find any bugs, please report them by opening an issue on GitHub.
2. **Feature Requests:** If you have ideas for new features, feel free to suggest them by opening an issue.
3. **Code Contributions:** 
    - Fork the repository.
    - Create a new branch (`git checkout -b feature-branch`).
    - Make your changes.
    - Commit your changes (`git commit -m 'Add some feature'`).
    - Push to the branch (`git push origin feature-branch`).
    - Open a pull request.

4. **Documentation:** Improve the documentation to help others understand and use the project.
5. **Testing:** Write tests to improve code coverage and ensure stability.

Please make sure your contributions adhere to our coding guidelines and standards.

## License

This project is licensed under the MIT License.
See the LICENSE file for details.
