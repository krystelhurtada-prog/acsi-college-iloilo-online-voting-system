from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, client 
from dotenv import load_dotenv
import os


# =========================
# LOAD ENVIRONMENT
# =========================

load_dotenv

app = Flask(__name__)
app.secret_key = "acsi_voting_secret"

SUPABASE_URL = ("https://jawfrnmrrniruafdetft.supabase.co")
SUPABASE_KEY = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imphd2Zybm1ycm5pcnVhZmRldGZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA1OTcxMzMsImV4cCI6MjEwNjE3MzEzM30.mg-3FX3Q6tqUu-l93t3QTjYpano9OtaFRsgmX0EjdnE")
 
print("SUPABASE_URL:", SUPABASE_URL)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/")
def home():
    return render_template("index.html")



@app.route("/vlogin", methods=["GET", "POST"])
def vlogin():

    if request.method == "POST":

        student_id = request.form.get("student_id")
        password = request.form.get("password")

        if not student_id or not password:
            flash("Please enter student ID and password.", "error")
            return render_template("vlogin.html")

        result = supabase.table("voters") \
            .select("*") \
            .eq("student_id", student_id) \
            .execute()

        if not result.data:
            flash("Voter not found.", "error")
            return render_template("vlogin.html")

        voter = result.data[0]

        if voter.get("password") != password:
            flash("Incorrect password.", "error")
            return render_template("vlogin.html")

        # Check if already voted
        if str(voter.get("status")).strip().lower() == "true":
            flash("You have already voted. You cannot vote again.", "warning")
            return render_template("vlogin.html")

        session["student_id"] = voter["student_id"]
        session["student_name"] = voter["student_name"]
        session["course"] = voter.get("course")

        return render_template(
            "votingpage.html",
            student_id=voter["student_id"],
            student_name=voter["student_name"],
            course=voter.get("course")
        )

    return render_template("vlogin.html")


@app.route('/votingpage')
def votingpage():

    # Get logged-in student ID
    student_id = session.get('student_id')

    if not student_id:
        return redirect(url_for('vlogin'))

    # Get voter information from database
    voter_result = supabase.table('voters') \
        .select('*') \
        .eq('student_id', student_id) \
        .execute()

    if not voter_result.data:
        return "Voter not found."

    voter = voter_result.data[0]

    # Check if voter already voted
    if voter.get('status') == True:
        return redirect(url_for('confirmation'))

    # Get voter details
    student_name = voter.get('student_name')
    course = voter.get('course')

    # Get candidates
    candidate_result = supabase.table('candidates') \
        .select('*') \
        .execute()

    candidates = candidate_result.data

    # Open voting page
    return render_template(
        'votingpage.html',
        student_name=student_name,
        student_id=student_id,
        course=course,
        candidates=candidates
    )


@app.route("/submit_vote", methods=["POST"])
def submit_vote():

    # Get student ID
    student_id = request.form.get("student_id")

    if not student_id:
        return "Student ID is missing."

    # Get voter
    voter_result = supabase.table("voters") \
        .select("*") \
        .eq("student_id", student_id) \
        .execute()

    if not voter_result.data:
        return "Voter not found."

    voter = voter_result.data[0]

    # Get course
    course = str(voter.get("course", "")).upper().strip()

    # Check if voter already voted
    if str(voter.get("status")).lower() == "true":
        return """
        <div style="text-align:center; margin-top:100px; font-family:Arial;">
            <h1>You Have Already Voted</h1>
            <p>You cannot vote again.</p>
            <a href="/">Back to Home</a>
        </div>
        """

    # ==========================================
    # GET SELECTED CANDIDATES
    # ==========================================

    president = request.form.get("president")
    vice_president = request.form.get("vice_president")
    secretary = request.form.get("secretary")
    treasurer = request.form.get("treasurer")
    auditor = request.form.get("auditor")
    public_information_officer = request.form.get("public_information_officer")

    bscs_representative = request.form.get("bscs_representative")
    bsis_representative = request.form.get("bsis_representative")
    act_representative = request.form.get("act_representative")
    shs_representative = request.form.get("shs_representative")

    # ==========================================
    # CHECK COMMON POSITIONS
    # ==========================================

    if not president:
        return "Please select a candidate for President."

    if not vice_president:
        return "Please select a candidate for Vice President."

    if not secretary:
        return "Please select a candidate for Secretary."

    if not treasurer:
        return "Please select a candidate for Treasurer."

    if not auditor:
        return "Please select a candidate for Auditor."

    if not public_information_officer:
        return "Please select a candidate for Public Information Officer."

    # ==========================================
    # CHECK REPRESENTATIVE BASED ON COURSE
    # ==========================================

    if course == "BSCS":

        if not bscs_representative:
            return "Please select a candidate for BSCS Representative."

        # Do not save representatives from other courses
        bsis_representative = None
        act_representative = None
        shs_representative = None

    elif course == "BSIS":

        if not bsis_representative:
            return "Please select a candidate for BSIS Representative."

        bscs_representative = None
        act_representative = None
        shs_representative = None

    elif course == "ACT":

        if not act_representative:
            return "Please select a candidate for ACT Representative."

        bscs_representative = None
        bsis_representative = None
        shs_representative = None

    elif course == "SHS":

        if not shs_representative:
            return "Please select a candidate for SHS Representative."

        bscs_representative = None
        bsis_representative = None
        act_representative = None

    else:
        return "Invalid course."

    # ==========================================
    # PREPARE VOTE DATA
    # ==========================================

    vote_data = {
        "student_id": voter["student_id"],
        "student_name": voter["student_name"],
        "president": president,
        "vice_president": vice_president,
        "secretary": secretary,
        "treasurer": treasurer,
        "auditor": auditor,
        "public_information_officer": public_information_officer,
        "bscs_representative": bscs_representative,
        "bsis_representative": bsis_representative,
        "act_representative": act_representative,
        "shs_representative": shs_representative
    }

    # ==========================================
    # SAVE VOTE TO VOTES TABLE
    # ==========================================

    vote_result = supabase.table("votes") \
        .insert(vote_data) \
        .execute()

    # ==========================================
    # UPDATE VOTER STATUS TO TRUE
    # ==========================================

    supabase.table("voters") \
        .update({"status": "true"}) \
        .eq("student_id", student_id) \
        .execute()

    print("STATUS UPDATE RESULT:", vote_result.data)

    # Check actual status
    check_status = supabase.table("voters") \
        .select("student_id, status") \
        .eq("student_id", student_id) \
        .execute()

    print("STATUS AFTER VOTING:", check_status.data)

    # ==========================================
    # SHOW CONFIRMATION PAGE
    # ==========================================

    return render_template(
        "confirmationpage.html",
        student_name=voter["student_name"],
        student_id=voter["student_id"],
        course=course,
        president=president,
        vice_president=vice_president,
        secretary=secretary,
        treasurer=treasurer,
        auditor=auditor,
        public_information_officer=public_information_officer,
        bscs_representative=bscs_representative,
        bsis_representative=bsis_representative,
        act_representative=act_representative,
        shs_representative=shs_representative
    )













@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        # Check empty fields
        if not username or not password:
            return render_template(
                'adminlogin.html',
                error='Please enter username and password'
            )

        # Your admin account
        if username != 'admin':
            return render_template(
                'adminlogin.html',
                error='Incorrect username'
            )

        if password != 'admin123':
            return render_template(
                'adminlogin.html',
                error='Incorrect password'
            )

        # Correct login
        session['admin_logged_in'] = True

        return redirect(url_for('dashboard'))

    return render_template('adminlogin.html')

@app.route('/dashboard')
def dashboard():

    if not session.get('admin_logged_in'):
        return redirect(url_for('adminlogin'))

    return render_template('admindashboard.html')




@app.route("/admin_logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect(url_for("adminlogin"))




# =========================
# ADD VOTER
# =========================
@app.route('/addvoter', methods=['GET', 'POST'])
def addvoter():

    if not session.get('admin_logged_in'):
        return redirect(url_for('adminlogin'))

    if request.method == 'POST':

        student_id = request.form.get('student_id')
        student_name = request.form.get('student_name')
        password = request.form.get('password')
        course = request.form.get('course')

        # Check empty fields
        if not student_id or not student_name or not password or not course:
            return "Please complete all fields."

        # Check existing Student ID
        existing = supabase.table('voters') \
            .select('id') \
            .eq('student_id', student_id) \
            .execute()

        if existing.data:
            return "Student ID already exists."

        # Insert voter
        supabase.table('voters').insert({
            'student_id': student_id,
            'student_name': student_name,
            'password': password,
            'status': False,
            'course':course
        
        }).execute()

        # Back to dashboard
        return redirect(url_for('dashboard'))

    return render_template('addvoter.html')

    # =========================
# VIEW VOTERS
# =========================

# =========================
# VIEW VOTERS
# =========================
@app.route('/viewvoters')
def view_voters():

    if not session.get('admin_logged_in'):
        return redirect(url_for('adminlogin'))

    # Get all voters from Supabase
    result = supabase.table('voters') \
        .select('*') \
        .order('id') \
        .execute()

    voters = result.data

    return render_template('viewvoters.html', voters=voters)






@app.route('/candidates')
def manage_candidates():

    # Get candidates
    candidates_result = supabase.table('candidates').select('*').execute()
    candidates_data = candidates_result.data or []

    # Get positions
    positions_result = supabase.table('positions').select('*').execute()
    positions_data = positions_result.data or []

    # Match POSITION_ID with POSITION_NAME
    for candidate in candidates_data:
        candidate["position_name"] = "No Position"

        for position in positions_data:
            if candidate["position_id"] == position["id"]:
                candidate["position_name"] = position["position_name"]
                break

    return render_template(
        'candidates.html',
        candidates=candidates_data,
        positions=positions_data
    )
@app.route('/add_candidate', methods=['POST'])
def add_candidate():

    full_name = request.form.get('full_name')
    position_id = request.form.get('position_id')

    if not full_name or not position_id:
        return redirect(url_for('manage_candidates'))

    supabase.table('candidates').insert({
        'full_name': full_name,
        'position_id': int(position_id)
    }).execute()

    return redirect(url_for('manage_candidates'))





@app.route('/results')
def results():

    # GET ALL CANDIDATES
    candidates_result = supabase.table('candidates').select('*').execute()
    candidates = candidates_result.data or []

    # GET ALL VOTES
    votes_result = supabase.table('votes').select('*').execute()
    votes = votes_result.data or []

    # GET ALL POSITIONS
    positions_result = supabase.table('positions').select('*').execute()
    positions = positions_result.data or []

    # POSITION ORDER
    position_order = [
        "President",
        "Vice President",
        "Secretary",
        "Treasurer",
        "Auditor",
        "Public Information Officer",
        "BSCS Representative",
        "BSIS Representative",
        "ACT Representative",
        "SHS Representative"
    ]

    # SORT POSITIONS
    positions = sorted(
        positions,
        key=lambda x: (
            position_order.index(x["position_name"])
            if x["position_name"] in position_order
            else 999
        )
    )

    # VOTE COLUMN MAPPING
    vote_columns = {
        "President": "president",
        "Vice President": "vice_president",
        "Secretary": "secretary",
        "Treasurer": "treasurer",
        "Auditor": "auditor",
        "Public Information Officer": "public_information_officer",
        "BSCS Representative": "bscs_representative",
        "BSIS Representative": "bsis_representative",
        "ACT Representative": "act_representative",
        "SHS Representative": "shs_representative"
    }

    results_data = []

    # LOOP THROUGH POSITIONS
    for position in positions:

        position_id = position["id"]
        position_name = position["position_name"]

        vote_column = vote_columns.get(position_name)

        # GET CANDIDATES FOR THIS POSITION
        position_candidates = []

        for candidate in candidates:

            if candidate["position_id"] == position_id:
                position_candidates.append(candidate)

        # COUNT VOTES
        candidate_results = []

        for candidate in position_candidates:

            candidate_name = str(candidate["full_name"]).strip()

            vote_count = 0

            for vote in votes:

                selected_candidate = vote.get(vote_column)

                if selected_candidate is not None:

                    selected_candidate = str(
                        selected_candidate
                    ).strip()

                    if selected_candidate.lower() == candidate_name.lower():

                        vote_count += 1

            candidate_results.append({
                "name": candidate_name,
                "votes": vote_count
            })

        # ADD POSITION RESULTS
        results_data.append({
            "name": position_name,
            "candidates": candidate_results
        })

         # DISPLAY RESULTS
    return render_template(
        "results.html",
        results=results_data
    )


 
if __name__ == "__main__":
    app.run(debug=True)