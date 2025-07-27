from flask import Flask, request, render_template, redirect
import os
import pandas as pd
import requests

app = Flask(__name__)

# Load environment variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.environ.get("TWILIO_FROM")
TWILIO_TO = os.environ.get("TWILIO_TO")
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY")

@app.route('/')
def index():
    df = pd.read_csv("plants.csv")
    page = int(request.args.get("page", 1))
    per_page = 15
    total_pages = (len(df) - 1) // per_page + 1
    plants = df.iloc[(page-1)*per_page : page*per_page].to_dict(orient='records')
    return render_template("form.html", plants=plants, current_page=page, total_pages=total_pages)

@app.route('/send', methods=['POST'])
def send():
    full_name = request.form.get('fullName', '')
    phone = request.form.get('phone', '')
    address = request.form.get('address', '')
    cart_data = request.form.get('cartData', '{}')
    image = request.files.get('image')

    # Optional image upload to ImgBB
    image_url = None
    if image and image.filename:
        upload_url = 'https://api.imgbb.com/1/upload'
        try:
            res = requests.post(upload_url, params={"key": IMGBB_API_KEY}, files={"image": image.read()})
            data = res.json()
            image_url = data['data']['url'] if 'data' in data else None
        except Exception as e:
            print("Image upload failed:", e)

    message = f"\u2709\ufe0f \u05d4\u05d6\u05de\u05e0\u05d4 \u05d7\u05d3\u05e9\u05d4 \u05de\u05d4\u05de\u05e9\u05ea\u05dc\u05d4!\n\n"
    message += f"\U0001f464 \u05e9\u05dd: {full_name}\n"
    message += f"\U0001f4de \u05d8\u05dc\u05e4\u05d5\u05df: {phone}\n"
    message += f"\U0001f4cd \u05db\u05ea\u05d5\u05d1\u05ea: {address}\n\n"
    message += f"\U0001f4e6 \u05e4\u05e8\u05d9\u05d8\u05d9\u05dd \u05d1\u05e2\u05d2\u05dc\u05d4:\n"

    try:
        cart = eval(cart_data)
        for name, item in cart.items():
            message += f"- {name} x{item['quantity']}\n"
    except Exception as e:
        message += "(\u05e9\u05d2\u05d9\u05d0\u05d4 \u05d1\u05e7\u05e8\u05d9\u05d0\u05ea \u05d4\u05e2\u05d2\u05dc\u05d4)\n"
        print("Cart parse error:", e)

    if image_url:
        message += f"\n\U0001f4f7 \u05ea\u05de\u05d5\u05e0\u05d4 \u05de\u05e6\u05d5\u05e8\u05e4\u05ea: {image_url}"

    url = f'https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json'
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    data = {
        'From': TWILIO_FROM,
        'To': TWILIO_TO,
        'Body': message
    }
    try:
        response = requests.post(url, data=data, auth=auth)
        print("Twilio status:", response.status_code)
        print("Response:", response.text)
    except Exception as e:
        print("Failed to send message:", e)

    return "<h2>ההזמנה נשלחה בהצלחה!</h2><a href='/'>חזרה</a>"

if __name__ == '__main__':
    app.run(debug=True)
