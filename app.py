from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    Response,
    url_for,
    send_from_directory,
    flash
)

import sqlite3
import os
import csv

from flask_mail import Mail, Message
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.secret_key = "ondiri_secret_key"


# ==========================
# UPLOAD SETTINGS
# ==========================

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)



# ==========================
# EMAIL SETTINGS
# ==========================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True

app.config["MAIL_USERNAME"] = "sharksammy6@gmail.com"

# Replace with your Gmail App Password
app.config["MAIL_PASSWORD"] = "bwlo kypn zxol ijjy"


mail = Mail(app)



# ==========================
# DATABASE CONNECTION
# ==========================

def get_db():

    conn = sqlite3.connect("bookings.db")

    conn.row_factory = sqlite3.Row

    return conn



# ==========================
# CREATE DATABASE TABLES
# ==========================

def create_database():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        email TEXT,

        phone TEXT,

        event TEXT,

        date TEXT,

        message TEXT,

        status TEXT DEFAULT 'Pending'

    )
    """)



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gallery(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        filename TEXT

    )
    """)



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        message TEXT

    )
    """)



    conn.commit()

    conn.close()



create_database()



# ==========================
# HOME PAGE
# ==========================

@app.route("/")
def home():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT date
    FROM bookings
    WHERE status='Confirmed'
    """)

    booked_dates = [
        row["date"]
        for row in cursor.fetchall()
    ]



    cursor.execute("""
    SELECT *
    FROM reviews
    ORDER BY id DESC
    """)

    reviews = cursor.fetchall()


    conn.close()



    return render_template(
        "index.html",
        booked_dates=booked_dates,
        reviews=reviews
    )
# ==========================
# SUBMIT REVIEW FROM HOME
# ==========================

@app.route("/review", methods=["POST"])
def review():

    name = request.form.get("name")

    message = request.form.get("message")


    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO reviews(name,message)

        VALUES(?,?)
        """,
        (name, message)
    )


    conn.commit()

    conn.close()


    flash(
        "Review submitted successfully!",
        "success"
    )


    return redirect("/")



# ==========================
# BOOKING SYSTEM
# ==========================

@app.route("/book", methods=["POST"])
def book():

    name = request.form.get("name")

    email = request.form.get("email")

    phone = request.form.get("phone")

    event = request.form.get("event")

    date = request.form.get("date")

    message = request.form.get("message")



    conn = get_db()

    cursor = conn.cursor()



    # CHECK DATE AVAILABILITY

    cursor.execute(
        """
        SELECT *
        FROM bookings

        WHERE date=?

        AND status='Confirmed'
        """,
        (date,)
    )


    existing = cursor.fetchone()



    if existing:

        conn.close()


        return f"""

        <h2>❌ Date Not Available</h2>

        <p>
        Sorry, {date} is already booked.
        </p>

        <a href="/">Choose Another Date</a>

        """



    # SAVE BOOKING

    cursor.execute(
        """
        INSERT INTO bookings

        (
        name,
        email,
        phone,
        event,
        date,
        message,
        status
        )

        VALUES(?,?,?,?,?,?,?)

        """,

        (
        name,
        email,
        phone,
        event,
        date,
        message,
        "Pending"
        )

    )


    conn.commit()

    conn.close()



    # ==========================
    # SEND EMAILS
    # ==========================

    try:


        admin_mail = Message(

            "New Ondiri Gardens Booking",

            sender=app.config["MAIL_USERNAME"],

            recipients=[
                "sharksammy6@gmail.com"
            ]

        )


        admin_mail.body = f"""

New Booking Received


Name: {name}

Email: {email}

Phone: {phone}

Event: {event}

Date: {date}


Message:

{message}

"""


        mail.send(admin_mail)



        customer_mail = Message(

            "Ondiri Gardens Booking Received",

            sender=app.config["MAIL_USERNAME"],

            recipients=[email]

        )


        customer_mail.body = f"""

Dear {name},


Thank you for booking Ondiri Gardens.


Your booking details:


Event: {event}

Date: {date}

Phone: {phone}


Status: Pending


We will contact you soon.


Ondiri Gardens Team

"""


        mail.send(customer_mail)



    except Exception as e:

        print(
            "Email Error:",
            e
        )




    return """

    <h2>✅ Booking Received</h2>

    <p>
    Thank you for choosing Ondiri Gardens.
    </p>

    <p>
    Your booking is waiting for confirmation.
    </p>


    <a href="/">Return Home</a>

    """
# ==========================
# ADMIN LOGIN SETTINGS
# ==========================

ADMIN_USERNAME = "admin"

ADMIN_PASSWORD = "12345"



# ==========================
# ADMIN LOGIN
# ==========================

@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")

        password = request.form.get("password")



        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            session["admin"] = True

            return redirect("/dashboard")

        else:

            flash(
                "Wrong username or password",
                "danger"
            )



    return render_template(
        "admin_login.html"
    )




# ==========================
# ADMIN DASHBOARD
# ==========================

@app.route("/dashboard")
def dashboard():


    if not session.get("admin"):

        return redirect("/admin")



    search = request.args.get(
        "search",
        ""
    )



    conn = get_db()

    cursor = conn.cursor()



    # SEARCH BOOKINGS

    if search:


        cursor.execute(
            """
            SELECT *

            FROM bookings

            WHERE name LIKE ?

            OR email LIKE ?

            OR phone LIKE ?

            OR event LIKE ?

            ORDER BY id DESC

            """,

            (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
            )

        )


    else:


        cursor.execute(
            """
            SELECT *

            FROM bookings

            ORDER BY id DESC

            """
        )



    bookings = cursor.fetchall()



    # STATISTICS


    cursor.execute(
        "SELECT COUNT(*) FROM bookings"
    )

    total = cursor.fetchone()[0]



    cursor.execute(
        """
        SELECT COUNT(*)

        FROM bookings

        WHERE status='Pending'

        """
    )

    pending = cursor.fetchone()[0]



    cursor.execute(
        """
        SELECT COUNT(*)

        FROM bookings

        WHERE status='Confirmed'

        """
    )

    confirmed = cursor.fetchone()[0]



    cursor.execute(
        """
        SELECT COUNT(*)

        FROM bookings

        WHERE status='Cancelled'

        """
    )

    cancelled = cursor.fetchone()[0]



    # GALLERY IMAGES

    cursor.execute(
        """
        SELECT *

        FROM gallery

        ORDER BY id DESC

        """
    )

    images = cursor.fetchall()



    # REVIEWS

    cursor.execute(
        """
        SELECT *

        FROM reviews

        ORDER BY id DESC

        """
    )

    reviews = cursor.fetchall()



    conn.close()



    return render_template(

        "admin.html",

        bookings=bookings,

        total=total,

        pending=pending,

        confirmed=confirmed,

        cancelled=cancelled,

        images=images,

        reviews=reviews,

        search=search

    )
# ==========================
# CONFIRM BOOKING
# ==========================

@app.route("/confirm/<int:id>")
def confirm(id):

    if not session.get("admin"):

        return redirect("/admin")



    conn = get_db()

    cursor = conn.cursor()



    cursor.execute(
        """
        UPDATE bookings

        SET status='Confirmed'

        WHERE id=?

        """,
        (id,)
    )



    conn.commit()

    conn.close()



    flash(
        "Booking confirmed successfully!",
        "success"
    )


    return redirect("/dashboard")




# ==========================
# CANCEL BOOKING
# ==========================

@app.route("/cancel/<int:id>")
def cancel(id):

    if not session.get("admin"):

        return redirect("/admin")



    conn = get_db()

    cursor = conn.cursor()



    cursor.execute(
        """
        UPDATE bookings

        SET status='Cancelled'

        WHERE id=?

        """,
        (id,)
    )



    conn.commit()

    conn.close()



    flash(
        "Booking cancelled!",
        "warning"
    )


    return redirect("/dashboard")




# ==========================
# DELETE BOOKING
# ==========================

@app.route("/delete_booking/<int:id>")
def delete_booking(id):

    if not session.get("admin"):

        return redirect("/admin")



    conn = get_db()

    cursor = conn.cursor()



    cursor.execute(
        """
        DELETE FROM bookings

        WHERE id=?

        """,
        (id,)
    )



    conn.commit()

    conn.close()



    flash(
        "Booking deleted!",
        "danger"
    )


    return redirect("/dashboard")




# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.pop(
        "admin",
        None
    )


    flash(
        "Logged out successfully!",
        "success"
    )


    return redirect("/admin")
# ==========================
# GALLERY PAGE
# ==========================

@app.route("/gallery")
def gallery():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT *

        FROM gallery

        ORDER BY id DESC

        """
    )


    images = cursor.fetchall()


    conn.close()



    return render_template(
        "gallery.html",
        images=images
    )




# ==========================
# UPLOAD IMAGE (ADMIN)
# ==========================

@app.route("/upload", methods=["POST"])
def upload():

    if not session.get("admin"):

        return redirect("/admin")



    if "image" not in request.files:

        flash(
            "No image selected",
            "danger"
        )

        return redirect("/dashboard")



    image = request.files["image"]



    if image.filename == "":

        flash(
            "No file selected",
            "danger"
        )

        return redirect("/dashboard")



    filename = secure_filename(
        image.filename
    )



    image.save(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )
    )



    conn = get_db()

    cursor = conn.cursor()



    cursor.execute(
        """
        INSERT INTO gallery(filename)

        VALUES(?)

        """,
        (filename,)
    )



    conn.commit()

    conn.close()



    flash(
        "Image uploaded successfully!",
        "success"
    )


    return redirect("/dashboard")




# ==========================
# DELETE IMAGE
# ==========================

@app.route("/delete_image/<int:id>")
def delete_image(id):

    if not session.get("admin"):

        return redirect("/admin")



    conn = get_db()

    cursor = conn.cursor()



    cursor.execute(
        """
        SELECT filename

        FROM gallery

        WHERE id=?

        """,
        (id,)
    )


    image = cursor.fetchone()



    if image:


        file_path = os.path.join(

            app.config["UPLOAD_FOLDER"],

            image["filename"]

        )


        if os.path.exists(file_path):

            os.remove(file_path)



        cursor.execute(
            """
            DELETE FROM gallery

            WHERE id=?

            """,
            (id,)
        )



        conn.commit()



    conn.close()



    flash(
        "Image deleted!",
        "danger"
    )


    return redirect("/dashboard")




# ==========================
# SERVE UPLOAD FILES
# ==========================

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(

        app.config["UPLOAD_FOLDER"],

        filename

    )
# ==========================
# EXPORT BOOKINGS TO CSV
# ==========================

@app.route("/export")
def export():

    if not session.get("admin"):

        return redirect("/admin")



    conn = get_db()

    cursor = conn.cursor()



    cursor.execute(
        """
        SELECT *

        FROM bookings

        ORDER BY id DESC

        """
    )


    bookings = cursor.fetchall()


    conn.close()




    class Echo:

        def write(self, value):

            return value




    def generate():

        writer = csv.writer(Echo())



        yield writer.writerow([

            "ID",

            "Name",

            "Email",

            "Phone",

            "Event",

            "Date",

            "Message",

            "Status"

        ])




        for booking in bookings:

            yield writer.writerow([

                booking["id"],

                booking["name"],

                booking["email"],

                booking["phone"],

                booking["event"],

                booking["date"],

                booking["message"],

                booking["status"]

            ])




    return Response(

        generate(),

        mimetype="text/csv",

        headers={

            "Content-Disposition":

            "attachment; filename=ondiri_bookings.csv"

        }

    )




# ==========================
# VIEW ALL REVIEWS
# ==========================

@app.route("/reviews")
def all_reviews():

    conn = get_db()

    cursor = conn.cursor()



    cursor.execute(

        """

        SELECT *

        FROM reviews

        ORDER BY id DESC

        """

    )


    reviews = cursor.fetchall()



    conn.close()



    return render_template(

        "reviews.html",

        reviews=reviews

    )




# ==========================
# ADD REVIEW PAGE
# ==========================

@app.route("/add_review", methods=["POST"])
def add_review():

    name = request.form.get("name")

    message = request.form.get("message")



    conn = get_db()

    cursor = conn.cursor()



    cursor.execute(

        """

        INSERT INTO reviews

        (name,message)

        VALUES(?,?)

        """,

        (

        name,

        message

        )

    )



    conn.commit()

    conn.close()



    flash(

        "Review added successfully!",

        "success"

    )


    return redirect("/reviews")
# ==========================
# CHANGE BOOKING STATUS
# ==========================

@app.route("/update_status/<int:id>/<status>")
def update_status(id, status):

    if not session.get("admin"):
        return redirect("/admin")

    allowed_status = [
        "Pending",
        "Confirmed",
        "Cancelled"
    ]

    if status not in allowed_status:
        flash("Invalid status", "danger")
        return redirect("/dashboard")

    conn = get_db()
    cursor = conn.cursor()

    # Get booking details before updating
    cursor.execute("""
        SELECT name, email, phone, event, date
        FROM bookings
        WHERE id=?
    """, (id,))

    booking = cursor.fetchone()

    if not booking:
        conn.close()
        flash("Booking not found.", "danger")
        return redirect("/dashboard")

    name = booking[0]
    email = booking[1]
    phone = booking[2]
    event = booking[3]
    date = booking[4]

    # Update booking status
    cursor.execute("""
        UPDATE bookings
        SET status=?
        WHERE id=?
    """, (status, id))

    conn.commit()
    conn.close()

    # Send email
    try:

        if status == "Confirmed":

            subject = "Booking Confirmed - Ondiri Gardens"

            body = f"""
Dear {name},

Congratulations!

Your booking has been CONFIRMED.

Booking Details
-------------------------
Name: {name}
Phone: {phone}
Event: {event}
Date: {date}

We look forward to welcoming you to Ondiri Gardens.

Thank you for choosing us.

Best Regards,
Ondiri Gardens Team
"""

        elif status == "Cancelled":

            subject = "Booking Cancelled - Ondiri Gardens"

            body = f"""
Dear {name},

We regret to inform you that your booking has been CANCELLED.

Booking Details
-------------------------
Name: {name}
Event: {event}
Date: {date}

If you have any questions, please contact us.

Best Regards,
Ondiri Gardens Team
"""

        else:

            subject = "Booking Status Updated - Ondiri Gardens"

            body = f"""
Dear {name},

Your booking status has been updated.

Current Status: {status}

Thank you for choosing Ondiri Gardens.
"""

        msg = Message(
            subject,
            sender=app.config["MAIL_USERNAME"],
            recipients=[email]
        )

        msg.body = body

        mail.send(msg)

    except Exception as e:
        print("Email Error:", e)

    flash(f"Booking marked as {status}", "success")

    return redirect("/dashboard")



# ==========================
# ADMIN DELETE REVIEW
# ==========================

@app.route("/delete_review/<int:id>")
def delete_review(id):

    if not session.get("admin"):

        return redirect("/admin")



    conn = get_db()

    cursor = conn.cursor()



    cursor.execute(

        """

        DELETE FROM reviews

        WHERE id=?

        """,

        (id,)

    )



    conn.commit()

    conn.close()



    flash(

        "Review deleted",

        "danger"

    )


    return redirect("/dashboard")





@app.errorhandler(500)
def server_error(error):

    return """

    <h2>Server Error</h2>

    <p>Please check app.py for mistakes.</p>

    """, 500
# ==========================
# HOME TEST ROUTE
# ==========================

@app.route("/test")
def test():

    return """

    <h2>Ondiri Gardens Website Running ✅</h2>

    <p>Flask server is working correctly.</p>

    <a href="/">Go Home</a>

    """



# ==========================
# RUN WEBSITE
# ==========================

if __name__ == "__main__":

    create_database()


    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )
  