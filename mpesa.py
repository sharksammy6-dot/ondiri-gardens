import requests
import base64
from datetime import datetime

# M-PESA Sandbox credentials
consumer_key = "Q6k1yFshTfRlHR0RsWdZEl7uUctODFA51h1OMLeueaLW6B9k"
consumer_secret = "HjAQl3D6QCCrPsU5BzwGnEiG0VPrPeYVJaPSPwJABhIsW4rOm227sytZB6MThBuC"

# Get access token
def get_access_token():

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(
        url,
        auth=(consumer_key, consumer_secret)
    )

    data = response.json()

    return data["access_token"]

def stk_push(phone, amount):

    access_token = get_access_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    shortcode = "174379"   # Sandbox test shortcode
    passkey = "N/A"

    password = base64.b64encode(
        (shortcode + passkey + timestamp).encode()
    ).decode()

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    data = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": "https://yourdomain.com/callback",
        "AccountReference": "Ondiri Gardens",
        "TransactionDesc": "Garden Booking Payment"
    }

    response = requests.post(url, json=data, headers=headers)

    return response.json()
# Test connection
token = get_access_token()

print("M-PESA Connected")
print(token)
response = stk_push("254743562856", 1)

print(response)