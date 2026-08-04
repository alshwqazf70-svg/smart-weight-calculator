import os
import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Item, LoadCheck, CalibrationLog

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///steel_calc.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# كلمة مرور الإدارة الافتراضية (تُضبط من متغير البيئة ADMIN_PASSWORD)
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))

# -------------------- تهيئة قاعدة البيانات --------------------
with app.app_context():
    db.create_all()
    # إضافة أصناف افتراضية إذا كانت قاعدة البيانات فارغة
    if Item.query.count() == 0:
        sample_items = [
            {'item_number': '001', 'name': 'زنك', 'color': 'أبيض', 'length': 6.0, 'width': 1.05, 'thickness': 0.35, 'unit_weight': 8.5, 'notes': ''},
            {'item_number': '002', 'name': 'زنك', 'color': 'أبيض', 'length': 6.0, 'width': 1.05, 'thickness': 0.40, 'unit_weight': 9.7, 'notes': ''},
            {'item_number': '003', 'name': 'حديد', 'color': 'أسود', 'length': 6.0, 'width': 1.20, 'thickness': 0.50, 'unit_weight': 12.3, 'notes': ''},
            {'item_number': '004', 'name': 'زنك', 'color': 'أحمر', 'length': 4.5, 'width': 0.90, 'thickness': 0.30, 'unit_weight': 5.8, 'notes': ''},
        ]
        for item in sample_items:
            db.session.add(Item(**item))
        db.session.commit()

# -------------------- دوال مساعدة --------------------
def require_admin():
    return session.get('admin_logged_in', False)

# -------------------- الصفحات الرئيسية --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        return render_template('login.html', error='كلمة المرور غير صحيحة')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not require_admin():
        return redirect(url_for('login'))
    return render_template('admin.html')

# -------------------- واجهات API --------------------
@app.route('/api/items/search')
def api_search_items():
    q = request.args.get('q', '').strip()
    if not q:
        # الأكثر استخدامًا
        items = Item.query.order_by(Item.usage_count.desc()).limit(20).all()
    else:
        search = f"%{q}%"
        try:
            thickness_val = float(q)
        except:
            thickness_val = None

        query = Item.query.filter(
            (Item.name.contains(q)) |
            (Item.color.contains(q)) |
            (Item.item_number.contains(q)) |
            (Item.thickness == thickness_val if thickness_val is not None else False)
        )
        items = query.order_by(Item.usage_count.desc()).all()

    return jsonify([{
        'id': item.id,
        'item_number': item.item_number,
        'name': item.name,
        'color': item.color,
        'length': item.length,
        'width': item.width,
        'thickness': item.thickness,
        'unit_weight': item.unit_weight,
        'notes': item.notes,
        'usage_count': item.usage_count
    } for item in items])

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    data = request.json
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 0))
    actual_weight = data.get('actual_weight')

    if item_id:
        item = Item.query.get(item_id)
        if not item:
            return jsonify({'error': 'الصنف غير موجود'}), 404
        unit_weight = item.unit_weight
        item_name = item.name
        item_color = item.color
        item.usage_count = (item.usage_count or 0) + 1
        db.session.commit()
    else:
        # حساب هندسي بدون صنف
        unit_weight = float(data.get('unit_weight', 0))
        item_name = data.get('name', 'حساب هندسي')
        item_color = data.get('color', '-')
        item_id = None

    expected_weight = round(unit_weight * quantity, 2)

    difference = None
    difference_percent = None
    status = None
    alert_message = None
    status_class = ''

    if actual_weight is not None and actual_weight != '':
        actual_weight = float(actual_weight)
        difference = round(actual_weight - expected_weight, 2)
        difference_percent = round((difference / expected_weight) * 100, 2) if expected_weight != 0 else 0

        abs_diff_percent = abs(difference_percent)
        if abs_diff_percent <= 0.5:
            status = 'مطابق'
            status_class = 'green'
        elif abs_diff_percent <= 2:
            status = 'فرق بسيط'
            status_class = 'orange'
        else:
            status = 'تحذير: فرق كبير'
            status_class = 'red'

        if difference > 0 and abs_diff_percent > 2:
            extra_pieces = round(difference / unit_weight) if unit_weight > 0 else 0
            alert_message = f'⚠️ الوزن الفعلي أكبر من المتوقع بمقدار {difference} كجم. قد يكون هناك {extra_pieces} حبة/حبات زيادة.'
        elif difference < 0 and abs_diff_percent > 2:
            missing_pieces = round(abs(difference) / unit_weight) if unit_weight > 0 else 0
            alert_message = f'⚠️ الوزن الفعلي أقل من المتوقع بمقدار {abs(difference)} كجم. قد يكون هناك {missing_pieces} حبة/حبات ناقصة.'

    # حفظ العملية في السجل
    check = LoadCheck(
        item_id=item_id,
        item_name=item_name,
        item_color=item_color,
        quantity=quantity,
        expected_weight=expected_weight,
        actual_weight=actual_weight if actual_weight is not None else 0,
        difference=difference if difference is not None else 0,
        difference_percent=difference_percent if difference_percent is not None else 0,
        status=status or 'غير محدد'
    )
    db.session.add(check)
    db.session.commit()

    return jsonify({
        'item_name': item_name,
        'item_color': item_color,
        'unit_weight': unit_weight,
        'quantity': quantity,
        'expected_weight': expected_weight,
        'actual_weight': actual_weight,
        'difference': difference,
        'difference_percent': difference_percent,
        'status': status,
        'status_class': status_class,
        'alert_message': alert_message,
        'check_id': check.id,
        'item_id': item_id  # مهم لزر المعايرة
    })

@app.route('/api/history')
def api_history():
    q = request.args.get('q', '').strip()
    query = LoadCheck.query.order_by(LoadCheck.created_at.desc())
    if q:
        search = f"%{q}%"
        query = query.filter(
            (LoadCheck.item_name.contains(q)) |
            (LoadCheck.item_color.contains(q)) |
            (LoadCheck.status.contains(q))
        )
    checks = query.limit(100).all()
    return jsonify([{
        'id': c.id,
        'item_name': c.item_name,
        'item_color': c.item_color,
        'quantity': c.quantity,
        'expected_weight': c.expected_weight,
        'actual_weight': c.actual_weight,
        'difference': c.difference,
        'difference_percent': c.difference_percent,
        'status': c.status,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M')
    } for c in checks])

@app.route('/api/calibrate', methods=['POST'])
def api_calibrate():
    data = request.json
    check_id = data.get('check_id')
    new_unit_weight = float(data.get('new_unit_weight'))
    reason = data.get('reason', '')

    check = LoadCheck.query.get(check_id)
    if not check or not check.item_id:
        return jsonify({'error': 'لا يمكن معايرة هذا الصنف'}), 400

    item = Item.query.get(check.item_id)
    if not item:
        return jsonify({'error': 'الصنف غير موجود'}), 404

    old_weight = item.unit_weight
    log = CalibrationLog(
        item_id=item.id,
        old_weight=old_weight,
        new_weight=new_unit_weight,
        reason=f'تحديث من عملية فحص # {check_id}. {reason}'
    )
    item.unit_weight = new_unit_weight
    db.session.add(log)
    db.session.commit()

    return jsonify({'success': True, 'message': f'تم تحديث وزن الحبة من {old_weight} إلى {new_unit_weight}'})

# -------------------- واجهات الإدارة (API) --------------------
@app.route('/api/admin/items', methods=['GET', 'POST'])
def api_admin_items():
    if not require_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    if request.method == 'POST':
        data = request.json
        item_id = data.get('id')
        if item_id:
            item = Item.query.get(item_id)
            if not item:
                return jsonify({'error': 'الصنف غير موجود'}), 404
            item.item_number = data['item_number']
            item.name = data['name']
            item.color = data['color']
            item.length = float(data['length'])
            item.width = float(data['width'])
            item.thickness = float(data['thickness'])
            item.unit_weight = float(data['unit_weight'])
            item.notes = data.get('notes', '')
        else:
            new_item = Item(
                item_number=data['item_number'],
                name=data['name'],
                color=data['color'],
                length=float(data['length']),
                width=float(data['width']),
                thickness=float(data['thickness']),
                unit_weight=float(data['unit_weight']),
                notes=data.get('notes', '')
            )
            db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True})
    else:
        items = Item.query.order_by(Item.name, Item.thickness).all()
        return jsonify([{
            'id': i.id,
            'item_number': i.item_number,
            'name': i.name,
            'color': i.color,
            'length': i.length,
            'width': i.width,
            'thickness': i.thickness,
            'unit_weight': i.unit_weight,
            'notes': i.notes,
            'usage_count': i.usage_count
        } for i in items])

@app.route('/api/admin/items/<int:item_id>', methods=['DELETE'])
def api_admin_delete_item(item_id):
    if not require_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    item = Item.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'غير موجود'}), 404

@app.route('/api/admin/export')
def api_admin_export():
    if not require_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['رقم الصنف', 'اسم الصنف', 'اللون', 'الطول', 'العرض', 'السماكة', 'وزن الحبة', 'ملاحظة'])
    for item in Item.query.all():
        cw.writerow([item.item_number, item.name, item.color, item.length, item.width, item.thickness, item.unit_weight, item.notes])

    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8-sig'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f'items_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

@app.route('/api/admin/import', methods=['POST'])
def api_admin_import():
    if not require_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'لم يتم اختيار ملف'}), 400
    stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
    reader = csv.reader(stream)
    next(reader, None)
    count = 0
    for row in reader:
        if len(row) < 7:
            continue
        item = Item(
            item_number=row[0],
            name=row[1],
            color=row[2],
            length=float(row[3]),
            width=float(row[4]),
            thickness=float(row[5]),
            unit_weight=float(row[6]),
            notes=row[7] if len(row) > 7 else ''
        )
        db.session.add(item)
        count += 1
    db.session.commit()
    return jsonify({'success': True, 'count': count})

@app.route('/api/admin/calibration_logs')
def api_calibration_logs():
    if not require_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    logs = CalibrationLog.query.order_by(CalibrationLog.created_at.desc()).limit(100).all()
    return jsonify([{
        'id': log.id,
        'item_name': log.item.name if log.item else 'صنف محذوف',
        'old_weight': log.old_weight,
        'new_weight': log.new_weight,
        'reason': log.reason,
        'created_at': log.created_at.strftime('%Y-%m-%d %H:%M')
    } for log in logs])

@app.route('/api/admin/change_password', methods=['POST'])
def api_change_password():
    if not require_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    new_password = request.json.get('password')
    if not new_password:
        return jsonify({'error': 'كلمة المرور فارغة'}), 400
    global ADMIN_PASSWORD_HASH
    ADMIN_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify({'success': True})
