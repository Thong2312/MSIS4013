from flask import Flask, render_template, request, redirect, url_for, flash
try:
    import pyodbc
except ImportError:
    import pypyodbc as pyodbc
from pypyodbc import IntegrityError

app = Flask(__name__)
app.secret_key = 'replace-with-your-secret-key'

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=DemoDB;"
    "Trusted_Connection=yes;"
)

def get_conn():
    return pyodbc.connect(CONN_STR)


@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_conn()
    cur = conn.cursor()

    if request.method == 'POST' and request.form.get('action') == 'add':
        name = request.form['name'].strip()
        salary = request.form['salary']
        if name and salary:
            cur.execute(
                "INSERT INTO employees (name, salary) VALUES (?, ?)",
                (name, float(salary))
            )
            conn.commit()
            flash(f"Đã thêm nhân viên {name}", "success")
        return redirect(url_for('index'))

    cur.execute("SELECT id, name, salary, dept_id FROM employees ORDER BY id")
    employees = cur.fetchall()
    cur.execute("SELECT dept_id, name FROM departments ORDER BY dept_id")
    depts = cur.fetchall()

    selected_id = request.args.get('emp_id')
    audits = []
    if selected_id:
        cur.execute("""
            SELECT audit_id, old_salary, new_salary, changed_at, change_desc
                FROM salary_audit
            WHERE emp_id = ?
            ORDER BY changed_at DESC
        """, (int(selected_id),))
        audits = cur.fetchall()

    conn.close()
    return render_template('index.html',
                           employees=employees,
                           depts=depts,
                           audits=audits,
                           selected_id=selected_id)


@app.route('/increase', methods=['POST'])
def increase():
    emp_id = int(request.form['emp_id'])
    amount = float(request.form['amount'])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "EXEC increase_salary @emp_id=?, @amount=?",
        (emp_id, amount)
    )
    conn.commit()
    conn.close()
    flash(f"Tăng lương nhân viên #{emp_id} thêm {amount:.2f}", "info")
    return redirect(url_for('index', emp_id=emp_id))


@app.route('/departments', methods=['GET', 'POST'])
def departments():
    conn = get_conn()
    cur = conn.cursor()
    if request.method == 'POST':
        name = request.form['dept_name'].strip()
        if name:
            cur.execute("EXEC add_department @name=?", (name,))
            conn.commit()
            flash(f"Đã thêm phòng ban {name}", "success")
        return redirect(url_for('departments'))

    cur.execute("SELECT dept_id, name FROM departments ORDER BY dept_id")
    depts = cur.fetchall()
    conn.close()
    return render_template('departments.html', depts=depts)


@app.route('/assign_dept', methods=['POST'])
def assign_dept():
    emp_id = int(request.form['emp_id'])
    dept_id = int(request.form['dept_id'])
    conn = get_conn()
    cur = conn.cursor()

    # Kiểm tra tồn tại department
    cur.execute("SELECT COUNT(*) FROM departments WHERE dept_id = ?", (dept_id,))
    exists = cur.fetchone()[0]
    if not exists:
        flash(f"Phòng ban #{dept_id} không tồn tại.", "danger")
    else:
        try:
            cur.execute(
                "EXEC assign_employee_dept @emp_id=?, @dept_id=?",
                (emp_id, dept_id)
            )
            conn.commit()
            flash(f"Đã gán nhân viên #{emp_id} vào phòng ban #{dept_id}", "success")
        except IntegrityError as e:
            flash(f"Lỗi khi gán phòng ban: {e}", "danger")

    conn.close()
    return redirect(url_for('index'))


@app.route('/edit/<int:emp_id>', methods=['GET', 'POST'])
def edit(emp_id):
    conn = get_conn()
    cur = conn.cursor()
    if request.method == 'POST':
        name = request.form['name'].strip()
        salary = float(request.form['salary'])
        cur.execute(
            "UPDATE employees SET name=?, salary=? WHERE id=?",
            (name, salary, emp_id)
        )
        conn.commit()
        conn.close()
        flash(f"Đã cập nhật nhân viên #{emp_id}", "warning")
        return redirect(url_for('index'))

    cur.execute("SELECT id, name, salary FROM employees WHERE id=?", (emp_id,))
    emp = cur.fetchone()
    conn.close()
    return render_template('edit.html', emp=emp)


@app.route('/delete/<int:emp_id>', methods=['POST'])
def delete(emp_id):
    conn = get_conn()
    cur  = conn.cursor()
    try:
        cur.execute("DELETE FROM salary_audit WHERE emp_id = ?", (emp_id,))
        cur.execute("DELETE FROM employees     WHERE id     = ?", (emp_id,))
        conn.commit()
        flash(f"Đã xoá nhân viên #{emp_id}", "danger")
    except Exception as e:
        conn.rollback()
        flash(f"Không thể xóa nhân viên #{emp_id}: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
