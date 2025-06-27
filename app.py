from flask import Flask, render_template, redirect, request
import requests
import uuid
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.dom.minidom
import html
import os

app = Flask(__name__)

#SUPPLIER_GATEWAY_URL = "http://localhost:5000/punchout/start"  # Update if needed

SUPPLIER_GATEWAY_URL = os.environ.get("SUPPLIER_GATEWAY_URL", "http://localhost:5000/punchout/start")
RETURN_URL = os.environ.get("RETURN_URL", "http://localhost:5001/return")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/punchout', methods=['POST'])
def punchout_preview():
    session_id = "XYZ-1234"

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
    SubElement(browser_form_post, 'URL').text = RETURN_URL

    supplier_setup = SubElement(punchout_setup, 'SupplierSetup')
    SubElement(supplier_setup, 'URL').text = SUPPLIER_GATEWAY_URL

    # Serialize XML to string
    xml_string = tostring(cxml, encoding='utf-8', method='xml').decode('utf-8')
    raw_xml = tostring(cxml, encoding='utf-8', method='xml')
    dom = xml.dom.minidom.parseString(raw_xml)
    xml_string = dom.toprettyxml(indent="  ")

    return render_template('punchout_preview.html', cxml=xml_string)


@app.route('/send_to_supplier', methods=['POST'])
def send_to_supplier():
    cxml = request.form.get('cxml')
    headers = {'Content-Type': 'application/xml'}
    response = requests.post(SUPPLIER_GATEWAY_URL, data=cxml.encode('utf-8'), headers=headers)

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
    #xml_data = request.data.decode('utf-8')
    xml_data = request.form.get('cxml', '')
    escaped_xml = html.escape(xml_data)
    return f"<h1>Received Cart</h1><div style=\"white-space: pre; font-family: monospace; border: 1px solid #ccc; padding: 1em; background-color: #f8f8f8;\">{ escaped_xml }</div>\
        <br/><a href=\"/\">Home</a>", 200
    



if __name__ == '__main__':
    app.run(port=5001)
