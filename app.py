import os
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session
)

from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db_connection, init_db


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

# Password ko memory me hashed form me rakhenge
ADMIN_PASSWORD_HASH = (
    generate_password_hash(ADMIN_PASSWORD)
    if ADMIN_PASSWORD
    else None
)


# =========================================================
# DATABASE INIT
# =========================================================

init_db()


# =========================================================
# LOGIN REQUIRED DECORATOR
# =========================================================

def login_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if not session.get("logged_in"):

            # save_bill AJAX request hai
            if request.path == "/save_bill":

                return jsonify({
                    "success": False,
                    "message": "Session expired. Please login again."
                }), 401

            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # Already logged in
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

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

        # Environment variables check
        if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:

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

            return redirect(url_for("dashboard"))

        else:

            error = "Username ya Password galat hai."

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

    return redirect(url_for("login"))


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
        SELECT COALESCE(SUM(grand_total), 0) AS total
        FROM bills
    """).fetchone()["total"]

    total_customers = conn.execute("""
        SELECT COUNT(DISTINCT customer_mobile) AS total
        FROM bills
        WHERE customer_mobile IS NOT NULL
        AND customer_mobile != ''
    """).fetchone()["total"]

    total_due = conn.execute("""
        SELECT COALESCE(SUM(balance), 0) AS total
        FROM bills
    """).fetchone()["total"]

    conn.close()

    return render_template(
        "dashboard.html",
        total_bills=total_bills,
        total_sales=round(total_sales, 2),
        total_customers=total_customers,
        total_due=round(total_due, 2)
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
        next_number = last_bill["id"] + 1
    else:
        next_number = 1

    bill_no = f"SRK-{next_number:04d}"

    return render_template(
        "index.html",
        bill_no=bill_no
    )


# =========================================================
# SAVE BILL
# =========================================================

@app.route("/save_bill", methods=["POST"])
@login_required
def save_bill():

    conn = None

    try:

        data = request.get_json() or {}

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
            data.get("subtotal", 0) or 0
        )

        discount = float(
            data.get("discount", 0) or 0
        )

        gst = float(
            data.get("gst", 0) or 0
        )

        grand_total = float(
            data.get("grand_total", 0) or 0
        )

        payment_mode = data.get(
            "payment_mode",
            ""
        )

        amount_paid = float(
            data.get("amount_paid", 0) or 0
        )

        items = data.get(
            "items",
            []
        )

        # -------------------------
        # VALIDATION
        # -------------------------

        if not bill_no:

            return jsonify({
                "success": False,
                "message": "Bill Number required hai."
            })

        if not customer_name:

            return jsonify({
                "success": False,
                "message": "Customer Name required hai."
            })

        if amount_paid < 0:

            return jsonify({
                "success": False,
                "message": "Amount Paid invalid hai."
            })

        if amount_paid > grand_total:

            return jsonify({
                "success": False,
                "message":
                    "Amount Paid Grand Total se jyada nahi ho sakta."
            })

        balance = grand_total - amount_paid

        if balance < 0:
            balance = 0

        conn = get_db_connection()

        # -------------------------
        # DUPLICATE BILL CHECK
        # -------------------------

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

        # -------------------------
        # SAVE BILL
        # -------------------------

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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

        # -------------------------
        # SAVE ITEMS
        # -------------------------

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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bill_id,
                item_name,
                item.get("purity", ""),
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

        return jsonify({
            "success": True,
            "message":
                "Bill Saved Successfully!",
            "bill_id":
                bill_id
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
                "Bill save nahi hua: " + str(e)
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
# VIEW BILL
# =========================================================

@app.route("/bill/<int:bill_id>")
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

    conn.close()

    return render_template(
        "view_bill.html",
        bill=bill,
        items=items,
        payments=payments
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

@app.route("/customer/<mobile>")
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
            bill["grand_total"] or 0
        )
        for bill in customer_bills
    )

    total_paid = sum(
        float(
            bill["amount_paid"] or 0
        )
        for bill in customer_bills
    )

    total_balance = sum(
        float(
            bill["balance"] or 0
        )
        for bill in customer_bills
    )

    customer_name = (
        customer_bills[0]["customer_name"]
    )

    conn.close()

    return render_template(
        "customer_detail.html",
        customer_name=customer_name,
        mobile=mobile,
        bills=customer_bills,
        total_purchase=total_purchase,
        total_paid=total_paid,
        total_balance=total_balance
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

        payment_mode = request.form.get(
            "payment_mode",
            "Cash"
        )

        note = request.form.get(
            "note",
            ""
        ).strip()

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
            bill["balance"] or 0
        )

        current_paid = float(
            bill["amount_paid"] or 0
        )

        if current_balance <= 0:

            return redirect(
                url_for(
                    "customer_detail",
                    mobile=
                        bill["customer_mobile"]
                )
            )

        if amount > current_balance:

            return (
                "Payment Due Amount se jyada nahi ho sakta.",
                400
            )

        new_paid = (
            current_paid + amount
        )

        new_balance = (
            current_balance - amount
        )

        if new_balance < 0.01:
            new_balance = 0

        # -------------------------
        # UPDATE BILL
        # -------------------------

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

        # -------------------------
        # PAYMENT HISTORY
        # -------------------------

        conn.execute("""
            INSERT INTO payments (
                bill_id,
                customer_mobile,
                amount,
                payment_mode,
                note
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            bill_id,
            bill["customer_mobile"],
            amount,
            payment_mode,
            note
        ))

        conn.commit()

        mobile = (
            bill["customer_mobile"]
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