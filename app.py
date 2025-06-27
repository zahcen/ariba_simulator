from flask import Flask, render_template, redirect, request
import requests
import uuid
from xml.etree.ElementTree import Element, SubElement, tostring

app = Flask(__name__)

SUPPLIER_GATEWAY_URL = "http://localhost:5000/punchout/start"  # Update if needed


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/punchout', methods=['POST'])
def punchout():
    session_id = "XYZ-1234"  # Static session ID for demonstration

    # Build cXML
    cxml = Element('cXML')

    # Header
    header = SubElement(cxml, 'Header')
    sender_el = SubElement(header, 'Sender')
    cred_sender = SubElement(sender_el, 'Credential', {'domain': 'NetworkID'})
    SubElement(cred_sender, 'Identity').text = "BUYER_ID"
    SubElement(cred_sender, 'SharedSecret').text = "abc123"

    # Request
    request_el = SubElement(cxml, 'Request')
    punchout_setup = SubElement(request_el, 'PunchOutSetupRequest')
    SubElement(punchout_setup, 'BuyerCookie').text = session_id

    browser_form_post = SubElement(punchout_setup, 'BrowserFormPost')
    SubElement(browser_form_post, 'URL').text = "http://localhost:5001/return"

    supplier_setup = SubElement(punchout_setup, 'SupplierSetup')
    SubElement(supplier_setup, 'URL').text = "http://localhost:5000/punchout/start"

    # Serialize XML to string
    xml_string = tostring(cxml, encoding='utf-8', method='xml')
    print(f"Sending cXML:\n{xml_string.decode('utf-8')}")

    # Send request to supplier
    headers = {'Content-Type': 'application/xml'}
    response = requests.post("http://localhost:5000/punchout/start", data=xml_string, headers=headers)

    if response.status_code == 200:
        try:
            from xml.etree import ElementTree as ET
            tree = ET.fromstring(response.content)
            start_page_url = tree.find('.//StartPage/URL').text
            return redirect(start_page_url)
        except Exception as e:
            return f"<h1>Error parsing supplier response</h1><pre>{e}</pre>", 500
    else:
        return f"<h1>Supplier error</h1><p>Status: {response.status_code}</p>", 500
    
@app.route('/return', methods=['POST'])
def return_cart():
    xml_data = request.data.decode('utf-8')
    return f"<h1>Received Cart</h1><pre>{xml_data}</pre>", 200


if __name__ == '__main__':
    app.run(port=5001)
