import os
import csv
import io

from functools import wraps
from urllib.parse import quote

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    Response,
    abort
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from itsdangerous import (
    URLSafeSerializer,
    BadSignature
)

from database import (
    get_db_connection,
    init_db
)


app = Flask(__name__)


# =========================================================
# SECURITY SETTINGS
# =========================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-before-production"
)

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

ADMIN_PASSWORD_HASH = (
    generate_password_hash(ADMIN_PASSWORD)
    if ADMIN_PASSWORD
    else None
)

bill_serializer = URLSafeSerializer(
    app.secret_key,
    salt="public-bill-link"
)


# =========================================================
# DATABASE INIT
# =========================================================

init_db()


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if not session.get("logged_in"):

            if request.path == "/save_bill":

                return jsonify({
                    "success": False,
                    "message": "Session expired. Please login again."
                }), 401

            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper


# =========================================================
# MOBILE NUMBER HELPER
# =========================================================

def clean_mobile_number(mobile):

    if not mobile:
        return ""

    digits = "".join(
        ch for ch in str(mobile)
        if ch.isdigit()
    )

    # 10 digit Indian number
    if len(digits) == 10:
        return "91" + digits

    # Already contains India code
    if (
        len(digits) == 12
        and digits.startswith("91")
    ):
        return digits

    return digits


# =========================================================
# BILL PENDING HELPER
# =========================================================

def get_bill_pending_details(
    conn,
    mobile,
    bill_id
):

    if not mobile:

        return {
            "previous_pending": 0.0,
            "current_due": 0.0,
            "total_pending": 0.0
        }

    previous_row = conn.execute("""
        SELECT
            COALESCE(
                SUM(balance),
                0
            ) AS total

        FROM bills

        WHERE customer_mobile = ?

        AND id < ?
    """, (
        mobile,
        bill_id
    )).fetchone()

    current_row = conn.execute("""
        SELECT balance

        FROM bills

        WHERE id = ?
    """, (
        bill_id,
    )).fetchone()

    previous_pending = float(
        previous_row["total"] or 0
    )

    current_due = (
        float(current_row["balance"] or 0)
        if current_row
        else 0
    )

    total_pending = (
        previous_pending
        + current_due
    )

    return {
        "previous_pending":
            round(previous_pending, 2),

        "current_due":
            round(current_due, 2),

        "total_pending":
            round(total_pending, 2)
    }


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if session.get("logged_in"):

        return redirect(
            url_for("dashboard")
        )

    error = None

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            not ADMIN_USERNAME
            or not ADMIN_PASSWORD_HASH
        ):

            error = (
                "Login credentials configure nahi hue hain. "
                "Render Environment Variables set kariye."
            )

        elif (
            username == ADMIN_USERNAME
            and check_password_hash(
                ADMIN_PASSWORD_HASH,
                password
            )
        ):

            session.clear()

            session["logged_in"] = True
            session["username"] = ADMIN_USERNAME

            return redirect(
                url_for("dashboard")
            )

        else:

            error = (
                "Username ya Password galat hai."
            )

    return render_template(
        "login.html",
        error=error
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
@login_required
def dashboard():

    conn = get_db_connection()

    total_bills = conn.execute("""
        SELECT COUNT(*) AS total
        FROM bills
    """).fetchone()["total"]

    total_sales = conn.execute("""
        SELECT
            COALESCE(
                SUM(grand_total),
                0
            ) AS total

        FROM bills
    """).fetchone()["total"]

    total_customers = conn.execute("""
        SELECT
            COUNT(
                DISTINCT customer_mobile
            ) AS total

        FROM bills

        WHERE customer_mobile IS NOT NULL

        AND customer_mobile != ''
    """).fetchone()["total"]

    total_due = conn.execute("""
        SELECT
            COALESCE(
                SUM(balance),
                0
            ) AS total

        FROM bills
    """).fetchone()["total"]

    conn.close()

    return render_template(
        "dashboard.html",

        total_bills=total_bills,

        total_sales=round(
            float(total_sales),
            2
        ),

        total_customers=total_customers,

        total_due=round(
            float(total_due),
            2
        )
    )


# =========================================================
# NEW BILL
# =========================================================

@app.route("/new-bill")
@login_required
def new_bill():

    conn = get_db_connection()

    last_bill = conn.execute("""
        SELECT id

        FROM bills

        ORDER BY id DESC

        LIMIT 1
    """).fetchone()

    conn.close()

    if last_bill:

        next_number = (
            last_bill["id"] + 1
        )

    else:

        next_number = 1

    bill_no = (
        f"SRK-{next_number:04d}"
    )

    return render_template(
        "index.html",
        bill_no=bill_no
    )


# =========================================================
# CUSTOMER PENDING API
# =========================================================

@app.route(
    "/customer-pending/<mobile>"
)
@login_required
def customer_pending(mobile):

    mobile = "".join(
        ch for ch in mobile
        if ch.isdigit()
    )

    conn = get_db_connection()

    row = conn.execute("""
        SELECT

            COALESCE(
                SUM(balance),
                0
            ) AS total_pending,

            COUNT(*) AS total_bills,

            MAX(customer_name) AS customer_name

        FROM bills

        WHERE customer_mobile = ?
    """, (
        mobile,
    )).fetchone()

    conn.close()

    return jsonify({

        "success": True,

        "mobile": mobile,

        "customer_name":
            row["customer_name"] or "",

        "previous_pending":
            round(
                float(
                    row["total_pending"]
                    or 0
                ),
                2
            ),

        "total_bills":
            int(
                row["total_bills"]
                or 0
            )
    })


# =========================================================
# SAVE BILL
# =========================================================

@app.route(
    "/save_bill",
    methods=["POST"]
)
@login_required
def save_bill():

    conn = None

    try:

        data = (
            request.get_json()
            or {}
        )

        bill_no = data.get(
            "bill_no",
            ""
        ).strip()

        customer_name = data.get(
            "customer_name",
            ""
        ).strip()

        customer_mobile = data.get(
            "customer_mobile",
            ""
        ).strip()

        subtotal = float(
            data.get(
                "subtotal",
                0
            ) or 0
        )

        discount = float(
            data.get(
                "discount",
                0
            ) or 0
        )

        gst = float(
            data.get(
                "gst",
                0
            ) or 0
        )

        grand_total = float(
            data.get(
                "grand_total",
                0
            ) or 0
        )

        payment_mode = data.get(
            "payment_mode",
            ""
        )

        amount_paid = float(
            data.get(
                "amount_paid",
                0
            ) or 0
        )

        items = data.get(
            "items",
            []
        )


        # ================= VALIDATION =================

        if not bill_no:

            return jsonify({
                "success": False,
                "message":
                    "Bill Number required hai."
            })

        if not customer_name:

            return jsonify({
                "success": False,
                "message":
                    "Customer Name required hai."
            })

        if amount_paid < 0:

            return jsonify({
                "success": False,
                "message":
                    "Amount Paid invalid hai."
            })

        if amount_paid > grand_total:

            return jsonify({
                "success": False,
                "message":
                    "Amount Paid Grand Total se jyada nahi ho sakta."
            })


        # ================= BALANCE =================

        balance = (
            grand_total
            - amount_paid
        )

        if balance < 0:
            balance = 0


        # ================= DATABASE =================

        conn = get_db_connection()

        existing_bill = conn.execute("""
            SELECT id

            FROM bills

            WHERE bill_no = ?
        """, (
            bill_no,
        )).fetchone()

        if existing_bill:

            return jsonify({
                "success": False,
                "message":
                    "Ye Bill Number pehle se use ho chuka hai."
            })


        # ================= INSERT BILL =================

        cursor = conn.execute("""
            INSERT INTO bills (

                bill_no,

                customer_name,

                customer_mobile,

                subtotal,

                discount,

                gst,

                grand_total,

                payment_mode,

                amount_paid,

                balance

            )

            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?
            )
        """, (

            bill_no,

            customer_name,

            customer_mobile,

            subtotal,

            discount,

            gst,

            grand_total,

            payment_mode,

            amount_paid,

            balance
        ))

        bill_id = cursor.lastrowid


        # ================= INSERT ITEMS =================

        for item in items:

            item_name = item.get(
                "item_name",
                ""
            ).strip()

            if not item_name:
                continue

            conn.execute("""
                INSERT INTO bill_items (

                    bill_id,

                    item_name,

                    purity,

                    gross_weight,

                    net_weight,

                    rate,

                    making,

                    amount

                )

                VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?
                )
            """, (

                bill_id,

                item_name,

                item.get(
                    "purity",
                    ""
                ),

                float(
                    item.get(
                        "gross_weight",
                        0
                    ) or 0
                ),

                float(
                    item.get(
                        "net_weight",
                        0
                    ) or 0
                ),

                float(
                    item.get(
                        "rate",
                        0
                    ) or 0
                ),

                float(
                    item.get(
                        "making",
                        0
                    ) or 0
                ),

                float(
                    item.get(
                        "amount",
                        0
                    ) or 0
                )
            ))

        conn.commit()


        # ================= PENDING =================

        pending_data = (
            get_bill_pending_details(
                conn,
                customer_mobile,
                bill_id
            )
        )


        return jsonify({

            "success": True,

            "message":
                "Bill Saved Successfully!",

            "bill_id":
                bill_id,

            "previous_pending":
                pending_data[
                    "previous_pending"
                ],

            "current_due":
                pending_data[
                    "current_due"
                ],

            "total_pending":
                pending_data[
                    "total_pending"
                ]
        })


    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "SAVE BILL ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                "Bill save nahi hua: "
                + str(e)

        }), 500


    finally:

        if conn:
            conn.close()


# =========================================================
# BILL HISTORY
# =========================================================

@app.route("/bills")
@login_required
def bills():

    conn = get_db_connection()

    all_bills = conn.execute("""
        SELECT *

        FROM bills

        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "bills.html",
        bills=all_bills
    )


# =========================================================
# EXPORT BILLS CSV
# =========================================================

@app.route("/export-bills")
@login_required
def export_bills():

    conn = get_db_connection()

    bills_data = conn.execute("""
        SELECT

            bill_no,

            customer_name,

            customer_mobile,

            subtotal,

            discount,

            gst,

            grand_total,

            payment_mode,

            amount_paid,

            balance,

            created_at

        FROM bills

        ORDER BY id DESC
    """).fetchall()

    conn.close()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([

        "Bill No",

        "Customer Name",

        "Mobile",

        "Subtotal",

        "Discount",

        "GST",

        "Grand Total",

        "Payment Mode",

        "Amount Paid",

        "Balance",

        "Date"
    ])

    for bill in bills_data:

        writer.writerow([

            bill["bill_no"],

            bill["customer_name"],

            bill["customer_mobile"],

            bill["subtotal"],

            bill["discount"],

            bill["gst"],

            bill["grand_total"],

            bill["payment_mode"],

            bill["amount_paid"],

            bill["balance"],

            bill["created_at"]
        ])

    csv_data = output.getvalue()

    output.close()

    return Response(

        csv_data,

        mimetype="text/csv",

        headers={
            "Content-Disposition":
                "attachment; filename=jewellery_bills_backup.csv"
        }
    )


# =========================================================
# VIEW BILL
# =========================================================

@app.route(
    "/bill/<int:bill_id>"
)
@login_required
def view_bill(bill_id):

    conn = get_db_connection()

    bill = conn.execute("""
        SELECT *

        FROM bills

        WHERE id = ?
    """, (
        bill_id,
    )).fetchone()


    if bill is None:

        conn.close()

        return (
            "Bill not found",
            404
        )


    items = conn.execute("""
        SELECT *

        FROM bill_items

        WHERE bill_id = ?
    """, (
        bill_id,
    )).fetchall()


    payments = conn.execute("""
        SELECT *

        FROM payments

        WHERE bill_id = ?

        ORDER BY id DESC
    """, (
        bill_id,
    )).fetchall()


    # =====================================================
    # PENDING DETAILS
    # =====================================================

    pending_data = (
        get_bill_pending_details(
            conn,
            bill["customer_mobile"],
            bill_id
        )
    )


    # =====================================================
    # SECURE PUBLIC BILL LINK
    # =====================================================

    token = bill_serializer.dumps({
        "bill_id": bill_id
    })

    public_bill_url = url_for(
        "public_bill",
        bill_id=bill_id,
        token=token,
        _external=True
    )


    # =====================================================
    # WHATSAPP
    # =====================================================

    whatsapp_number = (
        clean_mobile_number(
            bill["customer_mobile"]
        )
    )

    whatsapp_message = (

        "Shree Ram Kumar Jewellers\n\n"

        f"Bill No: {bill['bill_no']}\n"

        f"Customer: {bill['customer_name']}\n"

        f"Bill Amount: Rs.{float(bill['grand_total'] or 0):.2f}\n"

        f"Paid: Rs.{float(bill['amount_paid'] or 0):.2f}\n"

        f"Current Due: Rs.{float(bill['balance'] or 0):.2f}\n"

        f"Previous Pending: Rs.{pending_data['previous_pending']:.2f}\n"

        f"Total Pending: Rs.{pending_data['total_pending']:.2f}\n\n"

        f"View Bill:\n{public_bill_url}\n\n"

        "Thank you for shopping with us."
    )

    whatsapp_url = ""

    if whatsapp_number:

        whatsapp_url = (
            "https://wa.me/"
            + whatsapp_number
            + "?text="
            + quote(
                whatsapp_message
            )
        )


    # =====================================================
    # SMS
    # =====================================================

    sms_message = (

        "Shree Ram Kumar Jewellers\n"

        f"Bill No: {bill['bill_no']}\n"

        f"Customer: {bill['customer_name']}\n"

        f"Total: Rs.{float(bill['grand_total'] or 0):.2f}\n"

        f"Paid: Rs.{float(bill['amount_paid'] or 0):.2f}\n"

        f"Current Due: Rs.{float(bill['balance'] or 0):.2f}\n"

        f"Total Pending: Rs.{pending_data['total_pending']:.2f}\n"

        f"Bill: {public_bill_url}\n"

        "Thank you - Shree Ram Kumar Jewellers"
    )

    sms_url = ""

    if bill["customer_mobile"]:

        sms_number = "".join(
            ch
            for ch in str(
                bill["customer_mobile"]
            )
            if ch.isdigit()
        )

        if sms_number:

            sms_url = (
                "sms:"
                + sms_number
                + "?body="
                + quote(
                    sms_message
                )
            )


    conn.close()


    return render_template(

        "view_bill.html",

        bill=bill,

        items=items,

        payments=payments,

        previous_pending=
            pending_data[
                "previous_pending"
            ],

        current_due=
            pending_data[
                "current_due"
            ],

        total_pending=
            pending_data[
                "total_pending"
            ],

        public_bill_url=
            public_bill_url,

        whatsapp_url=
            whatsapp_url,

        sms_url=
            sms_url,

        public_view=False
    )


# =========================================================
# PUBLIC BILL
# Customer can open without login
# =========================================================

@app.route(
    "/public-bill/<int:bill_id>/<token>"
)
def public_bill(
    bill_id,
    token
):

    try:

        token_data = (
            bill_serializer.loads(
                token
            )
        )

    except BadSignature:

        abort(403)


    if (
        int(
            token_data.get(
                "bill_id",
                -1
            )
        )
        != bill_id
    ):

        abort(403)


    conn = get_db_connection()


    bill = conn.execute("""
        SELECT *

        FROM bills

        WHERE id = ?
    """, (
        bill_id,
    )).fetchone()


    if bill is None:

        conn.close()

        return (
            "Bill not found",
            404
        )


    items = conn.execute("""
        SELECT *

        FROM bill_items

        WHERE bill_id = ?
    """, (
        bill_id,
    )).fetchall()


    payments = conn.execute("""
        SELECT *

        FROM payments

        WHERE bill_id = ?

        ORDER BY id DESC
    """, (
        bill_id,
    )).fetchall()


    pending_data = (
        get_bill_pending_details(
            conn,
            bill["customer_mobile"],
            bill_id
        )
    )


    conn.close()


    return render_template(

        "view_bill.html",

        bill=bill,

        items=items,

        payments=payments,

        previous_pending=
            pending_data[
                "previous_pending"
            ],

        current_due=
            pending_data[
                "current_due"
            ],

        total_pending=
            pending_data[
                "total_pending"
            ],

        public_bill_url=
            request.url,

        whatsapp_url="",

        sms_url="",

        public_view=True
    )


# =========================================================
# DELETE BILL
# =========================================================

@app.route(
    "/delete_bill/<int:bill_id>",
    methods=["POST"]
)
@login_required
def delete_bill(bill_id):

    conn = get_db_connection()

    try:

        conn.execute("""
            DELETE FROM payments

            WHERE bill_id = ?
        """, (
            bill_id,
        ))

        conn.execute("""
            DELETE FROM bill_items

            WHERE bill_id = ?
        """, (
            bill_id,
        ))

        conn.execute("""
            DELETE FROM bills

            WHERE id = ?
        """, (
            bill_id,
        ))

        conn.commit()

    except Exception as e:

        conn.rollback()

        print(
            "DELETE ERROR:",
            e
        )

    finally:

        conn.close()

    return redirect(
        url_for("bills")
    )


# =========================================================
# CUSTOMER KHATA
# =========================================================

@app.route("/customers")
@login_required
def customers():

    conn = get_db_connection()

    customer_list = conn.execute("""
        SELECT

            customer_name,

            customer_mobile,

            COALESCE(
                SUM(grand_total),
                0
            ) AS total_purchase,

            COALESCE(
                SUM(amount_paid),
                0
            ) AS total_paid,

            COALESCE(
                SUM(balance),
                0
            ) AS total_balance

        FROM bills

        WHERE customer_mobile IS NOT NULL

        AND customer_mobile != ''

        GROUP BY

            customer_mobile,

            customer_name

        ORDER BY

            total_balance DESC

    """).fetchall()

    conn.close()

    return render_template(
        "customers.html",
        customers=customer_list
    )


# =========================================================
# CUSTOMER DETAIL
# =========================================================

@app.route(
    "/customer/<mobile>"
)
@login_required
def customer_detail(mobile):

    conn = get_db_connection()

    customer_bills = conn.execute("""
        SELECT *

        FROM bills

        WHERE customer_mobile = ?

        ORDER BY id DESC
    """, (
        mobile,
    )).fetchall()


    if not customer_bills:

        conn.close()

        return (
            "Customer not found",
            404
        )


    total_purchase = sum(

        float(
            bill["grand_total"]
            or 0
        )

        for bill
        in customer_bills
    )


    total_paid = sum(

        float(
            bill["amount_paid"]
            or 0
        )

        for bill
        in customer_bills
    )


    total_balance = sum(

        float(
            bill["balance"]
            or 0
        )

        for bill
        in customer_bills
    )


    customer_name = (
        customer_bills[0][
            "customer_name"
        ]
    )


    conn.close()


    return render_template(

        "customer_detail.html",

        customer_name=
            customer_name,

        mobile=
            mobile,

        bills=
            customer_bills,

        total_purchase=
            total_purchase,

        total_paid=
            total_paid,

        total_balance=
            total_balance
    )


# =========================================================
# RECEIVE PAYMENT
# =========================================================

@app.route(
    "/receive-payment/<int:bill_id>",
    methods=["POST"]
)
@login_required
def receive_payment(bill_id):

    conn = None

    try:

        amount = float(
            request.form.get(
                "amount",
                0
            ) or 0
        )

        payment_mode = (
            request.form.get(
                "payment_mode",
                "Cash"
            )
        )

        note = (
            request.form.get(
                "note",
                ""
            ).strip()
        )


        if amount <= 0:

            return (
                "Payment amount invalid hai.",
                400
            )


        conn = get_db_connection()


        bill = conn.execute("""
            SELECT *

            FROM bills

            WHERE id = ?
        """, (
            bill_id,
        )).fetchone()


        if bill is None:

            return (
                "Bill not found",
                404
            )


        current_balance = float(
            bill["balance"]
            or 0
        )

        current_paid = float(
            bill["amount_paid"]
            or 0
        )


        if current_balance <= 0:

            return redirect(
                url_for(
                    "customer_detail",
                    mobile=
                        bill[
                            "customer_mobile"
                        ]
                )
            )


        if amount > current_balance:

            return (
                "Payment Due Amount se jyada nahi ho sakta.",
                400
            )


        new_paid = (
            current_paid
            + amount
        )

        new_balance = (
            current_balance
            - amount
        )

        if new_balance < 0.01:

            new_balance = 0


        conn.execute("""
            UPDATE bills

            SET

                amount_paid = ?,

                balance = ?

            WHERE id = ?
        """, (
            new_paid,
            new_balance,
            bill_id
        ))


        conn.execute("""
            INSERT INTO payments (

                bill_id,

                customer_mobile,

                amount,

                payment_mode,

                note

            )

            VALUES (
                ?, ?, ?, ?, ?
            )
        """, (

            bill_id,

            bill["customer_mobile"],

            amount,

            payment_mode,

            note
        ))


        conn.commit()


        mobile = (
            bill[
                "customer_mobile"
            ]
        )


        return redirect(
            url_for(
                "customer_detail",
                mobile=mobile
            )
        )


    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "PAYMENT ERROR:",
            e
        )

        return (
            "Payment save nahi hua: "
            + str(e),
            500
        )


    finally:

        if conn:
            conn.close()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )