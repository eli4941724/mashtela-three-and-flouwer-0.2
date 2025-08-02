from flask import Flask, request, render_template, redirect
import os
import pandas as pd
import requests

app = Flask(__name__)

# קריאת משתני סביבה (Twilio ו־ImgBB)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.environ.get("TWILIO_FROM")
TWILIO_TO = os.environ.get("TWILIO_TO")
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY")

# דף הבית עם רשימת הצמחים
@app.route('/')
def index():
    df = pd.read_csv("plants.csv")
    page = int(request.args.get("page", 1))
    per_page = 15
    total_pages = (len(df) - 1) // per_page + 1
    plants = df.iloc[(page-1)*per_page : page*per_page].to_dict(orient='records')
    return render_template("form.html.jinja2", plants=plants, current_page=page, total_pages=total_pages)

# שליחת הזמנה
@app.route('/send', methods=['POST'])
def send():
    full_name = request.form.get('fullName', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    cart_data = request.form.get('cartData', '{}')
    image = request.files.get('image')

    # בדיקת שם ומספר טלפון
    if not full_name or not phone:
        return "<h2 style='color:red;'>יש למלא שם מלא ומספר טלפון!</h2><a href='/'>חזרה לטופס</a>"

    # העלאת תמונה (אם קיימת)
    image_url = None
    if image and image.filename:
        upload_url = 'https://api.imgbb.com/1/upload'
        try:
            res = requests.post(upload_url, params={"key": IMGBB_API_KEY}, files={"image": image.read()})
            data = res.json()
            image_url = data['data']['url'] if 'data' in data else None
        except Exception as e:
            print("Image upload failed:", e)

    # בניית ההודעה
    message = f"\u2709\ufe0f הזמנה חדשה מהמשתלה!\n\n"
    message += f"\U0001f464 שם: {full_name}\n"
    message += f"\U0001f4de טלפון: {phone}\n"
    message += f"\U0001f4cd כתובת: {address}\n\n"
    message += f"\U0001f4e6 פריטים בעגלה:\n"

    try:
        cart = eval(cart_data)
        for name, item in cart.items():
            message += f"- {name} x{item['quantity']}\n"
    except Exception as e:
        message += "(שגיאה בקריאת העגלה)\n"
        print("Cart parse error:", e)

    if image_url:
        message += f"\n\U0001f4f7 תמונה מצורפת: {image_url}"

    # שליחה ל־Twilio
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

# הרצה תואמת Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
