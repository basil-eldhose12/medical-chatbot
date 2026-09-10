from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from gemini_service import get_chatbot_response

import intent, response, data
from database import get_db_connection, init_db

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads/doctors')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize DB
init_db()

# --- Add payment_deadline column if missing ---
def migrate_payment_deadline():
    conn = get_db_connection()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(appointments)").fetchall()]
    if "payment_deadline" not in cols:
        conn.execute("ALTER TABLE appointments ADD COLUMN payment_deadline TEXT")
        conn.commit()
        print("[MIGRATION] Added payment_deadline column.")
    conn.close()

migrate_payment_deadline()

app = Flask(__name__)
app.secret_key = "medical_chatbot_secret_key"

# =========================
#  HOME & AUTHENTICATION
# =========================
@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/assistant")
def chat_ui():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user["password"], password):
            if user["status"] != "APPROVED":
                flash("Your account is pending admin approval.", "warning")
                return render_template("login.html")
            
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            
            if user["role"] == "ADMIN":
                return redirect(url_for("admin_dashboard"))
            elif user["role"] == "HOSPITAL":
                return redirect(url_for("hospital_dashboard"))
            else:
                return redirect(url_for("patient_dashboard"))
        
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/register/patient", methods=["GET", "POST"])
def register_patient():
    from datetime import date as date_cls
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        dob = request.form.get("dob", "").strip()
        
        if not username or not password or not email or not phone or not dob:
            flash("All fields are required.", "error")
            return render_template("register_patient.html", today_date=date_cls.today().isoformat())
            
        if dob > date_cls.today().isoformat():
            flash("Date of birth cannot be in the future.", "error")
            return render_template("register_patient.html", today_date=date_cls.today().isoformat())
            
        conn = get_db_connection()
        try:
            hashed_pw = generate_password_hash(password)
            conn.execute("INSERT INTO users (username, password, role, status, email, phone, dob) VALUES (?, ?, 'PATIENT', 'PENDING', ?, ?, ?)",
                         (username, hashed_pw, email, phone, dob))
            conn.commit()
            flash("Registration successful! Waiting for admin approval.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
        finally:
            conn.close()
            
    return render_template("register_patient.html", today_date=date_cls.today().isoformat())

@app.route("/register/hospital", methods=["GET", "POST"])
def register_hospital():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()
        
        if not username or not password or not email or not phone or not location:
            flash("All fields are required.", "error")
            return render_template("register_hospital.html")
            
        conn = get_db_connection()
        try:
            hashed_pw = generate_password_hash(password)
            conn.execute("INSERT INTO users (username, password, role, status, email, phone, location) VALUES (?, ?, 'HOSPITAL', 'PENDING', ?, ?, ?)",
                         (username, hashed_pw, email, phone, location))
            conn.commit()
            flash("Hospital registered! Waiting for admin approval.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
        finally:
            conn.close()
    return render_template("register_hospital.html")


# =========================
#  DASHBOARDS
# =========================
@app.route("/patient/dashboard")
def patient_dashboard():
    if session.get("role") != "PATIENT":
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    appts = conn.execute("""
        SELECT a.*, u.username as hospital_name, d.name as doctor_name
        FROM appointments a
        JOIN users u ON a.hospital_id = u.id
        LEFT JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id = ?
        ORDER BY a.date DESC, a.time DESC
    """, (session["user_id"],)).fetchall()
    conn.close()
    return render_template("patient_dashboard.html", username=session["username"], appointments=appts)

@app.route("/hospital/dashboard")
def hospital_dashboard():
    if session.get("role") != "HOSPITAL":
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    # Hospitals see all appointments for their hospital
    appts = conn.execute("""
        SELECT a.*, p.username as patient_name, p.email as patient_email, p.phone as patient_phone, p.dob as patient_dob, d.name as doctor_name
        FROM appointments a
        JOIN users p ON a.patient_id = p.id
        LEFT JOIN doctors d ON a.doctor_id = d.id
        WHERE a.hospital_id = ? AND a.status IN ('PENDING', 'PAYMENT_PENDING', 'CONFIRMED', 'COMPLETED', 'REJECTED')
        ORDER BY a.date DESC, a.time DESC
    """, (session["user_id"],)).fetchall()
    conn.close()
    return render_template("hospital_dashboard.html", username=session["username"], appointments=appts)


# =========================
#  ADMIN PANEL
# =========================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "ADMIN":
            flash("Admin access required.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    stats = {
        "patients": conn.execute("SELECT COUNT(*) FROM users WHERE role='PATIENT'").fetchone()[0],
        "hospitals": conn.execute("SELECT COUNT(*) FROM users WHERE role='HOSPITAL'").fetchone()[0],
        "pending_users": conn.execute("SELECT COUNT(*) FROM users WHERE status='PENDING'").fetchone()[0],
        "pending_appts": conn.execute("SELECT COUNT(*) FROM appointments WHERE status='PENDING'").fetchone()[0],
        "payments_collected": conn.execute("SELECT COUNT(*) FROM appointments WHERE payment_status='PAID'").fetchone()[0],
    }
    pending_users = conn.execute("SELECT * FROM users WHERE status='PENDING' ORDER BY id DESC").fetchall()
    pending_appts = conn.execute("""
        SELECT a.*, p.username as patient_name, p.email as patient_email, p.phone as patient_phone, p.dob as patient_dob, u.username as hospital_name, d.name as doctor_name
        FROM appointments a
        JOIN users p ON a.patient_id = p.id
        JOIN users u ON a.hospital_id = u.id
        LEFT JOIN doctors d ON a.doctor_id = d.id
        WHERE a.status IN ('PENDING', 'PAYMENT_PENDING')
        ORDER BY a.created_at DESC LIMIT 20
    """).fetchall()
    conn.close()
    return render_template("admin/dashboard.html", stats=stats, pending_users=pending_users, pending_appts=pending_appts)

@app.route("/admin/approve_user/<int:user_id>")
@admin_required
def approve_user(user_id):
    conn = get_db_connection()
    conn.execute("UPDATE users SET status = 'APPROVED' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User approved successfully.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reject_user/<int:user_id>")
@admin_required
def reject_user(user_id):
    conn = get_db_connection()
    conn.execute("UPDATE users SET status = 'REJECTED' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User rejected.", "info")
    return redirect(url_for("admin_dashboard"))

# Admin can BLOCK a user (set status=BLOCKED) via user management - no appointment approve/reject

@app.route("/admin/users")
@admin_required
def admin_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users WHERE role != 'ADMIN' ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin/manage_users.html", users_list=users)

@app.route("/admin/toggle_user/<int:user_id>")
@admin_required
def toggle_user_status(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT status FROM users WHERE id = ?", (user_id,)).fetchone()
    new_status = 'APPROVED' if user['status'] == 'BLOCKED' else 'BLOCKED'
    conn.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_users"))

@app.route("/admin/delete_user/<int:user_id>")
@admin_required
def delete_user(user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted.", "info")
    return redirect(url_for("admin_users"))

@app.route("/admin/appointments")
@admin_required
def admin_appointments():
    conn = get_db_connection()
    appts = conn.execute("""
        SELECT a.*, p.username as patient_name, u.username as hospital_name, d.name as doctor_name
        FROM appointments a
        JOIN users p ON a.patient_id = p.id
        JOIN users u ON a.hospital_id = u.id
        LEFT JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("admin/appointments.html", appointments=appts)

@app.route("/admin/feedback")
@admin_required
def admin_feedback_view():
    conn = get_db_connection()
    feedbacks = conn.execute("""
        SELECT f.*, 
               COALESCE(p.username, '[Deleted User]') as patient_name,
               u.username as hospital_name, 
               d.name as doctor_name
        FROM feedback f
        LEFT JOIN users p ON f.user_id = p.id
        LEFT JOIN appointments a ON f.appointment_id = a.id
        LEFT JOIN users u ON a.hospital_id = u.id
        LEFT JOIN doctors d ON a.doctor_id = d.id
        ORDER BY f.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("admin/feedback.html", feedback_list=feedbacks)


# =========================
#  HOSPITAL MODULE HELPERS
# =========================
@app.route("/update_appointment_status/<int:app_id>", methods=["POST"])
def update_appointment_status(app_id):
    if session.get("role") != "HOSPITAL":
        return jsonify({"success": False, "error": "Unauthorized"})
    
    new_status = request.form.get("status")
    conn = get_db_connection()
    
    # Fetch current appointment state first
    appt = conn.execute(
        "SELECT status, payment_status FROM appointments WHERE id = ? AND hospital_id = ?",
        (app_id, session["user_id"])
    ).fetchone()
    
    if not appt:
        conn.close()
        flash("Appointment not found.", "error")
        return redirect(url_for("hospital_dashboard"))
    
    current_status = appt["status"]
    
    # ── STATE MACHINE GUARDS ──────────────────────────────────────────
    # 1. REJECTED and COMPLETED are final — no changes allowed
    if current_status in ("REJECTED", "COMPLETED"):
        conn.close()
        flash(f"Cannot change a {current_status} appointment.", "warning")
        return redirect(url_for("hospital_dashboard"))
    
    # 2. CONFIRMED (patient already paid) cannot be rejected
    if current_status == "CONFIRMED" and new_status == "REJECTED":
        conn.close()
        flash("Cannot reject a CONFIRMED appointment — patient has already paid ₹200.", "error")
        return redirect(url_for("hospital_dashboard"))
    
    # 3. Mark COMPLETED only allowed from CONFIRMED state
    if new_status == "COMPLETED" and current_status != "CONFIRMED":
        conn.close()
        flash("Can only mark COMPLETED after patient has paid and appointment is CONFIRMED.", "warning")
        return redirect(url_for("hospital_dashboard"))
    # ─────────────────────────────────────────────────────────────────
    
    # When hospital approves → trigger payment requirement + set 5-min deadline
    if new_status == "APPROVED":
        new_status = "PAYMENT_PENDING"
        deadline = (datetime.now() + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE appointments SET status = ?, payment_deadline = ? WHERE id = ? AND hospital_id = ?",
            (new_status, deadline, app_id, session["user_id"])
        )
    elif new_status == "REJECTED":
        conn.execute("UPDATE appointments SET status = ?, payment_status = 'CANCELLED' WHERE id = ? AND hospital_id = ?",
                     (new_status, app_id, session["user_id"]))
    else:
        conn.execute("UPDATE appointments SET status = ? WHERE id = ? AND hospital_id = ?",
                     (new_status, app_id, session["user_id"]))
    conn.commit()
    conn.close()
    
    status_label = "Payment Pending (awaiting patient payment)" if new_status == "PAYMENT_PENDING" else new_status
    flash(f"Appointment updated: {status_label}.", "success")
    return redirect(url_for("hospital_dashboard"))

@app.route("/cancel_appointment_patient/<int:app_id>", methods=["POST"])
def cancel_appointment_patient(app_id):
    if session.get("role") != "PATIENT":
        return jsonify({"success": False, "error": "Unauthorized"})
        
    conn = get_db_connection()
    appt = conn.execute(
        "SELECT status FROM appointments WHERE id = ? AND patient_id = ?",
        (app_id, session["user_id"])
    ).fetchone()
    
    if not appt:
        conn.close()
        flash("Appointment not found or unauthorized.", "error")
        return redirect(url_for("patient_dashboard"))
        
    current_status = appt["status"]
    
    if current_status in ["PENDING", "PAYMENT_PENDING"]:
        conn.execute("UPDATE appointments SET status = 'CANCELLED', payment_status = 'CANCELLED' WHERE id = ?", (app_id,))
        conn.commit()
        flash("Appointment successfully cancelled.", "success")
    else:
        flash("Cannot cancel an appointment that is already confirmed or processed.", "warning")
        
    conn.close()
    return redirect(url_for("patient_dashboard"))

# =========================
#  FEEDBACK & LOGS
# =========================
@app.route("/feedback/<int:app_id>", methods=["GET", "POST"])
def submit_feedback(app_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        user_id = session["user_id"]
        
        conn = get_db_connection()
        try:
            local_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO feedback (user_id, appointment_id, rating, comment, created_at) VALUES (?, ?, ?, ?, ?)",
                         (user_id, app_id, rating, comment, local_ts))
            conn.commit()
            flash("Feedback submitted! Thank you.", "success")
        except Exception as e:
            flash("Already submitted feedback for this appointment.", "warning")
        finally:
            conn.close()
        return redirect(url_for("patient_dashboard"))
    
    return render_template("feedback.html", app_id=app_id)

@app.route("/submit-feedback", methods=["GET", "POST"])
def submit_general_feedback():
    if not session.get("user_id"):
        return redirect(url_for("login"))
        
    if request.method == "POST":
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        user_id = session["user_id"]
        
        print(f"[FEEDBACK DEBUG] User {user_id} submitting general feedback: {rating} stars, {comment}")
        conn = get_db_connection()
        try:
            local_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO feedback (user_id, rating, comment, created_at) VALUES (?, ?, ?, ?)",
                         (user_id, rating, comment, local_ts))
            conn.commit()
            print("[FEEDBACK DEBUG] Successfully saved to DB.")
            flash("Thank you for your feedback!", "success")
        except Exception as e:
            print(f"[FEEDBACK DEBUG] ERROR: {e}")
            flash("Error submitting feedback.", "error")
        finally:
            conn.close()
        
        target = "patient_dashboard" if session.get("role") == "PATIENT" else "hospital_dashboard"
        return redirect(url_for(target))
        
    return render_template("feedback.html", app_id=None)

@app.route("/patient/booking-log")
def booking_log():
    if session.get("role") != "PATIENT":
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM booking_logs WHERE patient_id = ? ORDER BY timestamp DESC", 
                        (session["user_id"],)).fetchall()
    conn.close()
    return render_template("booking_log.html", logs=logs)


# =========================
#  HOSPITAL LIST
# =========================
@app.route("/hospitals")
def list_hospitals():
    if session.get("role") != "PATIENT":
        flash("Please login to book appointments.", "info")
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    hospitals = conn.execute("SELECT id, username FROM users WHERE role = 'HOSPITAL' AND status = 'APPROVED'").fetchall()
    conn.close()
    from datetime import date
    return render_template("hospitals.html", hospitals=hospitals, today_date=date.today().isoformat())


# =========================
#  CHATS & ADMIN STUBS
# =========================
@app.route("/admin/cases")
@admin_required
def admin_cases():
    conn = get_db_connection()
    # Basic logic to show cases
    cases = conn.execute("SELECT * FROM cases").fetchall()
    conn.close()
    return render_template("admin/cases.html", cases=cases)

@app.route("/admin/normalization")
@admin_required
def admin_normalization():
    conn = get_db_connection()
    maps = conn.execute("SELECT * FROM normalization_map").fetchall()
    conn.close()
    return render_template("admin/normalization.html", normalization=maps)

@app.route("/admin/logs")
@admin_required
def admin_logs():
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 50").fetchall()
    conn.close()
    return render_template("admin/logs.html", logs=logs)


# =========================
# GEMINI CHAT ROUTE (REFINED BOOKING)
# =========================
@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        return redirect(url_for("chat_ui"))
    try:
        data_json = request.get_json()
        user_message = data_json.get("message", "").strip()
        print(f"User Request: {user_message}")

        if not user_message:
            return jsonify({"response": "Please type your symptoms."})

        # --- BASIC GREETING INTERCEPT ---
        greetings = ["hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon", "good evening"]
        normalized_msg = user_message.lower()
        if normalized_msg in greetings or normalized_msg.startswith(tuple(g + " " for g in greetings)):
            if not session.get("booking_step") and not session.get("awaiting_consent"):
                return jsonify({"response": "Hi there! 👋 I am HealthCare AI. How can I assist you with your health today? Please describe any symptoms you are experiencing so I can help."})

        # --- BOOKING FLOW STATE MACHINE ---
        booking_step = session.get("booking_step")
        
        # New State: If last response asked for consent and user said "yes"
        if intent.is_affirmative(user_message) and session.get("awaiting_consent"):
            session.pop("awaiting_consent", None)
            spec = session.get("last_specialist", "General Physician")
            doctors = get_doctors_by_specialist(spec)
            
            if doctors:
                session["doctor_options"] = doctors
                session["booking_step"] = "AWAITING_DOCTOR"
                
                formatted_list = "\n".join([f"{i+1}. Dr. {d['name']} - {d['hospital_name']}" for i, d in enumerate(doctors)])
                return jsonify({"response": f"Available {spec}s:\n\n{formatted_list}\n\n**Reply with the doctor number (e.g., 1) to continue.**"})
            return jsonify({"response": f"I couldn't find any {spec}s right now."})
            
        # Handle user declining the doctor suggestion
        elif intent.is_negative(user_message) and session.get("awaiting_consent"):
            session.pop("awaiting_consent", None)
            return jsonify({"response": "Alright! I won't book a doctor right now. If you need anything else, feel free to ask."})

        # Step 2: Handle Numbered Doctor Selection
        if booking_step == "AWAITING_DOCTOR":
            num = intent.get_number(user_message)
            options = session.get("doctor_options", [])
            if num and 1 <= num <= len(options):
                selected_doc = options[num-1]
                session["selected_doctor_id"] = selected_doc["id"]
                session["selected_doctor_name"] = selected_doc["name"]
                session["selected_hospital_id"] = selected_doc["hospital_id"]
                session["booking_step"] = "AWAITING_DATE"
                return jsonify({"response": f"Selected Dr. {selected_doc['name']}. Please enter the date (YYYY-MM-DD)."})
            return jsonify({"response": f"Please enter a number between 1 and {len(options)}."})

        # Step 3: Handle Date Selection
        if booking_step == "AWAITING_DATE":
            if intent.is_date(user_message):
                date_val = user_message.strip()
                session["selected_date"] = date_val
                doc_id = session.get("selected_doctor_id")
                
                # Fetch slots internally
                conn = get_db_connection()
                doc = conn.execute("SELECT shift_start, shift_end FROM doctors WHERE id = ?", (doc_id,)).fetchone()
                if not doc:
                    conn.close()
                    return jsonify({"response": "Error: Doctor not found."})
                
                booked = conn.execute("SELECT time FROM appointments WHERE doctor_id = ? AND date = ? AND status != 'REJECTED'", (doc_id, date_val)).fetchall()
                booked_times = [b["time"] for b in booked]
                
                start = datetime.strptime(doc["shift_start"], "%H:%M")
                end = datetime.strptime(doc["shift_end"], "%H:%M")
                
                slots = []
                current = start
                while current < end:
                    time_str = current.strftime("%H:%M")
                    if time_str not in booked_times:
                        slots.append(time_str)
                    current += timedelta(minutes=30)
                conn.close()
                
                if slots:
                    slot_list = ", ".join(slots)
                    session["booking_step"] = "AWAITING_SLOT"
                    return jsonify({"response": f"Available slots for {date_val}: {slot_list}. Reply with your preferred time."})
                return jsonify({"response": f"No available slots for {date_val}. Try another date."})
            return jsonify({"response": "Please use YYYY-MM-DD format."})

        # Step 4: Handle Slot Selection & Final Booking
        if booking_step == "AWAITING_SLOT":
            if intent.is_time(user_message):
                time_val = user_message.strip()
                doc_id = session.get("selected_doctor_id")
                date_val = session.get("selected_date")
                hosp_id = session.get("selected_hospital_id")
                
                if session.get("role") != "PATIENT":
                    return jsonify({"response": "Please log in as a patient to confirm."})
                
                res = book_appointment_api_internal({
                    "hospital_id": hosp_id,
                    "doctor_id": doc_id,
                    "date": date_val,
                    "time": time_val
                })
                
                if res["success"]:
                    session.pop("booking_step", None)
                    return jsonify({"response": f"✅ Appointment requested with Dr. {session.get('selected_doctor_name')} on {date_val} at {time_val}.\n\n⏳ **Awaiting hospital approval.** Once approved, you will see a **Pay ₹200** button on your dashboard to confirm your appointment."})
                return jsonify({"response": f"Error: {res['error']}"})

        # --- NORMAL CHAT & BOOKING INITIATION ---
        was_awaiting = session.pop("awaiting_consent", None)
        is_booking_intent = intent.detect_appointment_intent(user_message)
        
        if is_booking_intent or (was_awaiting and intent.is_affirmative(user_message)):
            spec = session.get("last_specialist", "General Physician")
            doctors = get_doctors_by_specialist(spec)
            
            if doctors:
                session["doctor_options"] = doctors
                session["booking_step"] = "AWAITING_DOCTOR"
                formatted_list = "\n".join([f"{i+1}. Dr. {d['name']} - {d['hospital_name']}" for i, d in enumerate(doctors)])
                return jsonify({"response": f"Available {spec}s:\n\n{formatted_list}\n\n**Reply with the doctor number.**"})
            return jsonify({"response": "No doctors found."})

        # --- CHATGPT / GEMINI ANALYSIS ---
        res = get_chatbot_response(user_message)
        
        if "condition" in res and "advice" in res:
            spec = res.get("specialist", "General Physician")
            session["last_specialist"] = spec
            session["awaiting_consent"] = True
            
            if "error" in res:
                formatted_response = (
                    f"System Notice: {res.get('advice')}\n\n"
                    f"Assessment: {res.get('condition')}\n"
                    f"Specialist: {spec}\n\n"
                    f"---\n⚠️ *{data.DISCLAIMER}*"
                )
            else:
                formatted_response = (
                    f"**Assessment**: {res.get('condition')}\n"
                    f"**Severity**: {res.get('severity')}\n"
                    f"**Specialist**: {spec}\n\n"
                    f"**Advice**: {res.get('advice')}\n\n"
                    f"---\n⚠️ *{data.DISCLAIMER}*"
                )
            
            # Save to logs table
            try:
                log_conn = get_db_connection()
                urgency = res.get('severity', 'LOW').upper()
                # Normalize: Gemini returns 'Normal'/'Serious'/'Emergency'
                # After .upper() these become 'NORMAL'/'SERIOUS'/'EMERGENCY'
                if urgency not in ('LOW', 'MEDIUM', 'HIGH', 'NORMAL', 'SERIOUS', 'EMERGENCY'):
                    urgency = 'LOW'
                # Use Python's local time (IST) instead of SQLite CURRENT_TIMESTAMP (UTC)
                local_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_conn.execute(
                    "INSERT INTO logs (timestamp, user_input, bot_response, urgency) VALUES (?, ?, ?, ?)",
                    (local_ts, user_message, formatted_response[:500], urgency)
                )
                log_conn.commit()
                log_conn.close()
            except Exception as log_err:
                print(f"[LOG WARNING] Could not write to logs: {log_err}")
                
            return jsonify({"response": f"{formatted_response}\n\n**Would you like me to suggests a doctor? (Reply Yes/No)**", "specialist": spec})

        # Absolute failsafe — also log the unidentified query
        try:
            log_conn = get_db_connection()
            local_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_conn.execute(
                "INSERT INTO logs (timestamp, user_input, bot_response, urgency) VALUES (?, ?, ?, ?)",
                (local_ts, user_message, "Could not identify condition. Referred to General Physician.", "LOW")
            )
            log_conn.commit()
            log_conn.close()
        except Exception as log_err:
            print(f"[LOG WARNING] Could not write to logs: {log_err}")
        return jsonify({"response": "I couldn't identify the condition. Consult a General Physician."})

    except Exception as e:
        print(f"Error in /chat: {e}")
        return jsonify({"response": "An internal error occurred."})


# =========================
#  DOCTOR FETCHING HELPERS
# =========================
def get_doctors_by_specialist(specialist, hospital_id=None):
    """Centralized function to fetch doctors with fuzzy matching on specialization."""
    print(f"[DEBUG] Fetching doctors for specialist: {specialist}")
    norm_spec = intent.normalize_specialization(specialist)
    
    conn = get_db_connection()
    query = """
        SELECT d.id, d.name, d.specialization, u.username as hospital_name, d.hospital_id, d.shift_start, d.shift_end, d.image_url
        FROM doctors d JOIN users u ON d.hospital_id = u.id
        WHERE u.status = 'APPROVED'
    """
    params = []
    if hospital_id:
        query += " AND d.hospital_id = ?"
        params.append(hospital_id)
    
    all_doctors = conn.execute(query, params).fetchall()
    conn.close()

    matches = []
    for doc in all_doctors:
        db_specs = doc["specialization"].lower().replace("/", " ").replace(",", " ").split()
        doc_norm_specs = [intent.normalize_specialization(s) for s in db_specs]
        if any(norm_spec in ds or ds in norm_spec for ds in doc_norm_specs) or norm_spec in doc["specialization"].lower():
            matches.append(dict(doc))

    if not matches and norm_spec != "general" and norm_spec != "general physician":
        return get_doctors_by_specialist("General Physician", hospital_id)

    return matches


# =========================
#  BOOKING APIs
# =========================
@app.route("/api/suggest_doctors")
def suggest_doctors():
    specialist = request.args.get("specialist", "General Physician")
    doctors = get_doctors_by_specialist(specialist)
    return jsonify({"specialist": specialist, "doctors": doctors})

@app.route("/api/specializations/<int:hospital_id>")
def get_specializations(hospital_id):
    conn = get_db_connection()
    specs = conn.execute("SELECT DISTINCT specialization FROM doctors WHERE hospital_id = ?", (hospital_id,)).fetchall()
    conn.close()
    return jsonify([row["specialization"] for row in specs])

@app.route("/api/doctors/<int:hospital_id>/<spec>")
def get_doctors_by_spec(hospital_id, spec):
    doctors = get_doctors_by_specialist(spec, hospital_id)
    return jsonify(doctors)

@app.route("/api/slots/<int:doctor_id>/<date>")
def get_available_slots(doctor_id, date):
    conn = get_db_connection()
    doc = conn.execute("SELECT shift_start, shift_end FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
    if not doc:
        conn.close()
        return jsonify([])

    from datetime import datetime, timedelta
    try:
        start_t = datetime.strptime(doc["shift_start"], "%H:%M")
        end_t = datetime.strptime(doc["shift_end"], "%H:%M")
    except:
        start_t = datetime.strptime("09:00", "%H:%M")
        end_t = datetime.strptime("17:00", "%H:%M")
    
    booked = conn.execute("SELECT time FROM appointments WHERE doctor_id = ? AND date = ? AND status != 'REJECTED'", (doctor_id, date)).fetchall()
    booked_times = [b["time"] for b in booked]
    
    slots = []
    current = start_t
    while current < end_t:
        time_str = current.strftime("%H:%M")
        if time_str not in booked_times:
            slots.append(time_str)
        current += timedelta(minutes=30)
    conn.close()
    return jsonify(slots)

@app.route("/api/book_appointment", methods=["POST"])
def book_appointment_api():
    if session.get("role") != "PATIENT":
        return jsonify({"success": False, "error": "Unauthorized."})
    return jsonify(book_appointment_api_internal(request.get_json()))

@app.route("/hospital/manage-staff", methods=["GET", "POST"])
def manage_staff():
    if session.get("role") != "HOSPITAL":
        return redirect(url_for("login"))
    
    hospital_id = session.get("user_id")
    conn = get_db_connection()
    
    if request.method == "POST":
        name = request.form.get("name")
        spec = request.form.get("specialization")
        start = request.form.get("shift_start")
        end = request.form.get("shift_end")
        image_url = request.form.get("image_url")
        
        # Handle File Upload
        file = request.files.get("doctor_image")
        if file and file.filename != '':
            filename = secure_filename(f"{name}_{file.filename}")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            image_url = f"/static/uploads/doctors/{filename}"
        
        if name and spec:
            try:
                conn.execute("INSERT INTO doctors (name, specialization, hospital_id, shift_start, shift_end, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                             (name, spec, hospital_id, start, end, image_url))
                conn.commit()
                flash("Doctor added successfully!", "success")
            except Exception as e:
                flash(f"Error adding doctor: {e}", "danger")
    
    doctors = conn.execute("SELECT * FROM doctors WHERE hospital_id = ?", (hospital_id,)).fetchall()
    conn.close()
    return render_template("hospital/manage_staff.html", doctors=doctors)

@app.route("/hospital/delete-doctor/<int:doc_id>", methods=["POST"])
def delete_doctor(doc_id):
    if session.get("role") != "HOSPITAL":
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    conn.execute("DELETE FROM doctors WHERE id = ? AND hospital_id = ?", (doc_id, session.get("user_id")))
    conn.commit()
    conn.close()
    flash("Doctor removed from staff.", "info")
    return redirect(url_for("manage_staff"))

@app.route("/book_appointment", methods=["POST"])
def book_appointment():
    if session.get("role") != "PATIENT":
        flash("Login required.", "error")
        return redirect(url_for("login"))
    
    res = book_appointment_api_internal(request.form)
    if res["success"]:
        flash("Appointment requested! Awaiting hospital approval.", "success")
    else:
        flash(f"Error: {res['error']}", "error")
    return redirect(url_for("patient_dashboard"))

def book_appointment_api_internal(data):
    from datetime import date as date_cls
    patient_id = session.get("user_id")
    doctor_id = data.get("doctor_id")
    hospital_id = data.get("hospital_id")
    date_val = data.get("date")
    time_val = data.get("time")
    
    if not all([doctor_id, date_val, time_val]):
        return {"success": False, "error": "Missing selection."}

    # Backend past-date validation
    if date_val < date_cls.today().isoformat():
        return {"success": False, "error": "Cannot book appointments for past dates."}
        
    from datetime import datetime
    if date_val == date_cls.today().isoformat():
        if time_val < datetime.now().strftime("%H:%M"):
            return {"success": False, "error": "Cannot book appointments for past times today."}
    
    try:
        conn = get_db_connection()
        if not hospital_id:
            doc = conn.execute("SELECT hospital_id FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
            hospital_id = doc["hospital_id"] if doc else None
            
        if not hospital_id:
            return {"success": False, "error": "Hospital not specified."}

        # Check if slot already taken
        exists = conn.execute("SELECT 1 FROM appointments WHERE doctor_id=? AND date=? AND time=? AND status NOT IN ('REJECTED','CANCELLED')",
                              (doctor_id, date_val, time_val)).fetchone()
        if exists:
            conn.close()
            return {"success": False, "error": "Slot already taken."}

        local_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO appointments (patient_id, hospital_id, doctor_id, date, time, status, amount, created_at) VALUES (?, ?, ?, ?, ?, 'PENDING', 200, ?)",
                     (patient_id, hospital_id, doctor_id, date_val, time_val, local_ts))
        app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        conn.execute("INSERT INTO booking_logs (patient_id, action, details) VALUES (?, ?, ?)",
                     (patient_id, "BOOKING_REQUEST", f"Booked Dr. ID {doctor_id} for {date_val} at {time_val}"))
        
        conn.commit()
        conn.close()
        return {"success": True, "app_id": app_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =========================
#  PAYMENT
# =========================
@app.route("/payment/<int:app_id>")
def payment_page(app_id):
    if session.get("role") != "PATIENT":
        return redirect(url_for("login"))
    conn = get_db_connection()
    appt = conn.execute("""
        SELECT a.*, d.name as doctor_name, u.username as hospital_name
        FROM appointments a
        LEFT JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON a.hospital_id = u.id
        WHERE a.id = ? AND a.patient_id = ?
    """, (app_id, session["user_id"])).fetchone()
    conn.close()
    if not appt:
        flash("Appointment not found.", "error")
        return redirect(url_for("patient_dashboard"))
    # Only allow payment when hospital has approved (PAYMENT_PENDING)
    if appt["status"] not in ("PAYMENT_PENDING",):
        if appt["status"] == "CONFIRMED":
            flash("Payment already completed.", "info")
        else:
            flash("Payment is only available after hospital approval.", "warning")
        return redirect(url_for("patient_dashboard"))
    return render_template("payment.html",
        app_id=app_id,
        doctor_name=appt["doctor_name"] or "Doctor",
        hospital_name=appt["hospital_name"],
        appt_date=appt["date"],
        appt_time=appt["time"]
    )

@app.route("/payment/mark/<int:app_id>", methods=["POST"])
def mark_payment(app_id):
    import uuid, datetime as dt
    if session.get("role") != "PATIENT":
        return jsonify({"success": False})
    conn = get_db_connection()
    appt = conn.execute("SELECT status FROM appointments WHERE id = ? AND patient_id = ?",
                        (app_id, session["user_id"])).fetchone()
    if not appt or appt["status"] != "PAYMENT_PENDING":
        conn.close()
        return jsonify({"success": False, "error": "Payment not allowed at this stage."})
    
    # Check no duplicate payment
    existing = conn.execute("SELECT 1 FROM payments WHERE appointment_id = ?", (app_id,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"success": False, "error": "Already paid."})
    
    txn_id = "TXN" + uuid.uuid4().hex[:10].upper()
    method = request.json.get("method", "CARD") if request.is_json else "CARD"
    paid_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn.execute(
        "UPDATE appointments SET payment_status='PAID', status='CONFIRMED', payment_id=? WHERE id=? AND patient_id=?",
        (txn_id, app_id, session["user_id"])
    )
    conn.execute(
        "INSERT INTO payments (appointment_id, user_id, amount, transaction_id, method, paid_at) VALUES (?,?,200,?,?,?)",
        (app_id, session["user_id"], txn_id, method, paid_at)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "transaction_id": txn_id, "paid_at": paid_at})

@app.route("/payment/receipt/<int:app_id>")
def payment_receipt(app_id):
    if session.get("role") != "PATIENT":
        return redirect(url_for("login"))
    conn = get_db_connection()
    appt = conn.execute("""
        SELECT a.*, d.name as doctor_name, u.username as hospital_name,
               p_user.username as patient_name,
               pay.transaction_id, pay.paid_at, pay.method, pay.amount as paid_amount
        FROM appointments a
        LEFT JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON a.hospital_id = u.id
        JOIN users p_user ON a.patient_id = p_user.id
        LEFT JOIN payments pay ON pay.appointment_id = a.id
        WHERE a.id = ? AND a.patient_id = ?
    """, (app_id, session["user_id"])).fetchone()
    conn.close()
    if not appt or appt["status"] != "CONFIRMED":
        flash("Receipt not available.", "warning")
        return redirect(url_for("patient_dashboard"))
    return render_template("payment_receipt.html", appt=appt)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()

    # =========================
    #  BACKGROUND SCHEDULER
    # =========================
    def expire_payment_deadlines():
        """Auto-cancels PAYMENT_PENDING appointments whose 5-min window has expired."""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = get_db_connection()
            result = conn.execute(
                """UPDATE appointments
                   SET status = 'REJECTED', payment_status = 'CANCELLED'
                   WHERE status = 'PAYMENT_PENDING'
                     AND payment_deadline IS NOT NULL
                     AND payment_deadline < ?""",
                (now,)
            )
            if result.rowcount > 0:
                print(f"[SCHEDULER] Auto-cancelled {result.rowcount} expired payment(s) at {now}")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SCHEDULER ERROR] {e}")

    scheduler = BackgroundScheduler()
    scheduler.add_job(expire_payment_deadlines, 'interval', minutes=1)
    scheduler.start()
    print("[SCHEDULER] Payment expiry job started (checks every 60s).")

    app.run(debug=True, use_reloader=False)