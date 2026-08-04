
# app.py - Main Flask Application
app_code = '''import os
import json
from datetime import datetime, timedelta
from io import BytesIO, StringIO
import csv

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, Response
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import db, Item, CalculationHistory, CalibrationLog, ActivityLog

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_globals():
    return {
        'now': datetime.now(),
        'app_name': 'حاسبة وزن الحديد الذكية'
    }

# ==================== HOME & CALCULATOR ====================

@app.route('/')
def index():
    """Main calculator page"""
    # Get most used items for quick access
    popular_items = Item.query.order_by(Item.usage_count.desc()).limit(10).all()
    return render_template('index.html', popular_items=popular_items)

@app.route('/api/items/search')
def search_items():
    """AJAX search for items"""
    query = request.args.get('q', '').strip()
    
    if not query:
        items = Item.query.order_by(Item.usage_count.desc()).limit(20).all()
    else:
        # Smart search: search in name, color, thickness, length, item_number
        try:
            num_query = float(query)
            items = Item.query.filter(
                db.or_(
                    Item.name.contains(query),
                    Item.color.contains(query),
                    Item.item_number.contains(query),
                    Item.thickness == num_query,
                    Item.length == num_query,
                    Item.width == num_query
                )
            ).order_by(Item.usage_count.desc()).all()
        except ValueError:
            items = Item.query.filter(
                db.or_(
                    Item.name.contains(query),
                    Item.color.contains(query),
                    Item.item_number.contains(query)
                )
            ).order_by(Item.usage_count.desc()).all()
    
    return jsonify([item.to_dict() for item in items])

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Calculate expected weight and compare with actual"""
    data = request.get_json()
    
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 0))
    actual_weight = data.get('actual_weight')
    
    if not item_id or quantity <= 0:
        return jsonify({'error': 'بيانات غير صحيحة'}), 400
    
    item = Item.query.get_or_404(item_id)
    
    # Increment usage count
    item.usage_count += 1
    
    expected_weight = item.unit_weight * quantity
    
    result = {
        'item': item.to_dict(),
        'quantity': quantity,
        'expected_weight': round(expected_weight, 2),
        'actual_weight': None,
        'difference': None,
        'difference_percent': None,
        'status': 'pending',
        'status_text': '⏳ في انتظار الوزن الفعلي',
        'status_class': 'warning'
    }
    
    if actual_weight and float(actual_weight) > 0:
        actual = float(actual_weight)
        difference = actual - expected_weight
        difference_percent = (difference / expected_weight) * 100 if expected_weight > 0 else 0
        
        # Determine status
        abs_percent = abs(difference_percent)
        if abs_percent <= 2:
            status = 'matched'
            status_text = '🟢 مطابق'
            status_class = 'success'
        elif abs_percent <= 5:
            status = 'small_diff'
            status_text = '🟠 فرق بسيط'
            status_class = 'warning'
        else:
            status = 'large_diff'
            status_text = '🔴 تحذير: فرق كبير'
            status_class = 'danger'
        
        result.update({
            'actual_weight': round(actual, 2),
            'difference': round(difference, 2),
            'difference_percent': round(difference_percent, 2),
            'status': status,
            'status_text': status_text,
            'status_class': status_class
        })
        
        # Save to history
        history = CalculationHistory(
            item_id=item.id,
            item_name=item.name,
            item_color=item.color,
            quantity=quantity,
            expected_weight=expected_weight,
            actual_weight=actual,
            difference=difference,
            difference_percent=difference_percent,
            status=status
        )
        db.session.add(history)
        
        # Log activity
        activity = ActivityLog(
            action='حساب وزن حمولة',
            entity_type='calculation',
            entity_id=history.id,
            details=f'{item.name} - {quantity} حبة - متوقع: {expected_weight:.1f} - فعلي: {actual:.1f}'
        )
        db.session.add(activity)
    
    db.session.commit()
    return jsonify(result)

@app.route('/api/calibrate', methods=['POST'])
def calibrate():
    """Update item weight based on actual measurement"""
    data = request.get_json()
    
    item_id = data.get('item_id')
    new_weight = float(data.get('new_weight', 0))
    reason = data.get('reason', '')
    
    if not item_id or new_weight <= 0:
        return jsonify({'error': 'بيانات غير صحيحة'}), 400
    
    item = Item.query.get_or_404(item_id)
    old_weight = item.unit_weight
    
    # Save calibration log
    calibration = CalibrationLog(
        item_id=item.id,
        old_weight=old_weight,
        new_weight=new_weight,
        reason=reason
    )
    db.session.add(calibration)
    
    # Update item
    item.unit_weight = new_weight
    item.updated_at = datetime.now()
    
    # Log activity
    activity = ActivityLog(
        action='معايرة وزن صنف',
        entity_type='item',
        entity_id=item.id,
        details=f'{item.name}: {old_weight} → {new_weight} كجم'
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'تم تحديث وزن {item.name} من {old_weight} إلى {new_weight} كجم',
        'item': item.to_dict()
    })

# ==================== ENGINEERING CALCULATOR ====================

@app.route('/engineering')
def engineering():
    """Engineering weight calculator"""
    return render_template('engineering.html')

@app.route('/api/engineering-calculate', methods=['POST'])
def engineering_calculate():
    """Calculate weight from dimensions"""
    data = request.get_json()
    
    length = float(data.get('length', 0))  # meters
    width = float(data.get('width', 0))    # meters
    thickness = float(data.get('thickness', 0))  # mm
    density = float(data.get('density', 7.14))   # g/cm3
    quantity = int(data.get('quantity', 1))
    
    if length <= 0 or width <= 0 or thickness <= 0:
        return jsonify({'error': 'الأبعاد يجب أن تكون أكبر من صفر'}), 400
    
    # Convert to cm for calculation
    length_cm = length * 100
    width_cm = width * 100
    thickness_cm = thickness / 10  # mm to cm
    
    # Volume in cm3
    volume = length_cm * width_cm * thickness_cm
    
    # Weight in kg
    unit_weight = (volume * density) / 1000
    total_weight = unit_weight * quantity
    
    return jsonify({
        'volume': round(volume, 2),
        'unit_weight': round(unit_weight, 3),
        'quantity': quantity,
        'total_weight': round(total_weight, 2)
    })

# ==================== ITEMS DATABASE ====================

@app.route('/items')
def items_list():
    """Items database page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'name')
    
    query = Item.query
    
    if search:
        try:
            num_search = float(search)
            query = query.filter(
                db.or_(
                    Item.name.contains(search),
                    Item.color.contains(search),
                    Item.item_number.contains(search),
                    Item.thickness == num_search,
                    Item.length == num_search
                )
            )
        except ValueError:
            query = query.filter(
                db.or_(
                    Item.name.contains(search),
                    Item.color.contains(search),
                    Item.item_number.contains(search)
                )
            )
    
    # Sorting
    if sort_by == 'name':
        query = query.order_by(Item.name)
    elif sort_by == 'usage':
        query = query.order_by(Item.usage_count.desc())
    elif sort_by == 'newest':
        query = query.order_by(Item.created_at.desc())
    elif sort_by == 'weight':
        query = query.order_by(Item.unit_weight)
    else:
        query = query.order_by(Item.name)
    
    pagination = query.paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
    
    return render_template('items.html', 
                         items=pagination.items, 
                         pagination=pagination,
                         search=search,
                         sort_by=sort_by)

@app.route('/items/add', methods=['GET', 'POST'])
def add_item():
    """Add new item"""
    if request.method == 'POST':
        item = Item(
            item_number=request.form.get('item_number', '').strip(),
            name=request.form.get('name', '').strip(),
            color=request.form.get('color', '').strip(),
            length=float(request.form.get('length', 0)),
            width=float(request.form.get('width', 0)),
            thickness=float(request.form.get('thickness', 0)),
            unit_weight=float(request.form.get('unit_weight', 0)),
            notes=request.form.get('notes', '').strip()
        )
        db.session.add(item)
        
        activity = ActivityLog(
            action='إضافة صنف جديد',
            entity_type='item',
            entity_id=item.id,
            details=f'{item.name} - {item.color}'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('تم إضافة الصنف بنجاح!', 'success')
        return redirect(url_for('items_list'))
    
    return render_template('item_form.html', item=None)

@app.route('/items/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    """Edit existing item"""
    item = Item.query.get_or_404(id)
    
    if request.method == 'POST':
        item.item_number = request.form.get('item_number', '').strip()
        item.name = request.form.get('name', '').strip()
        item.color = request.form.get('color', '').strip()
        item.length = float(request.form.get('length', 0))
        item.width = float(request.form.get('width', 0))
        item.thickness = float(request.form.get('thickness', 0))
        item.unit_weight = float(request.form.get('unit_weight', 0))
        item.notes = request.form.get('notes', '').strip()
        item.updated_at = datetime.now()
        
        activity = ActivityLog(
            action='تعديل صنف',
            entity_type='item',
            entity_id=item.id,
            details=f'{item.name}'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('تم تحديث الصنف بنجاح!', 'success')
        return redirect(url_for('items_list'))
    
    return render_template('item_form.html', item=item)

@app.route('/items/delete/<int:id>', methods=['POST'])
def delete_item(id):
    """Delete item"""
    item = Item.query.get_or_404(id)
    
    activity = ActivityLog(
        action='حذف صنف',
        entity_type='item',
        entity_id=item.id,
        details=f'{item.name}'
    )
    db.session.add(activity)
    
    db.session.delete(item)
    db.session.commit()
    
    flash('تم حذف الصنف بنجاح!', 'success')
    return redirect(url_for('items_list'))

@app.route('/api/items/<int:id>')
def get_item(id):
    """Get single item as JSON"""
    item = Item.query.get_or_404(id)
    return jsonify(item.to_dict())

# ==================== HISTORY ====================

@app.route('/history')
def history():
    """Calculation history page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = CalculationHistory.query
    
    if search:
        query = query.filter(
            db.or_(
                CalculationHistory.item_name.contains(search),
                CalculationHistory.item_color.contains(search)
            )
        )
    
    if status_filter:
        query = query.filter(CalculationHistory.status == status_filter)
    
    query = query.order_by(CalculationHistory.created_at.desc())
    pagination = query.paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
    
    return render_template('history.html',
                         history=pagination.items,
                         pagination=pagination,
                         search=search,
                         status_filter=status_filter)

@app.route('/history/delete/<int:id>', methods=['POST'])
def delete_history(id):
    """Delete history entry"""
    entry = CalculationHistory.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('تم حذف السجل بنجاح!', 'success')
    return redirect(url_for('history'))

# ==================== ADMIN ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session.permanent = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('كلمة المرور غير صحيحة!', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('تم تسجيل الخروج بنجاح!', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    stats = {
        'total_items': Item.query.count(),
        'total_calculations': CalculationHistory.query.count(),
        'total_calibrations': CalibrationLog.query.count(),
        'matched_count': CalculationHistory.query.filter_by(status='matched').count(),
        'warning_count': CalculationHistory.query.filter_by(status='small_diff').count(),
        'danger_count': CalculationHistory.query.filter_by(status='large_diff').count(),
    }
    
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(20).all()
    
    return render_template('admin.html', stats=stats, activities=recent_activities)

# ==================== BACKUP & RESTORE ====================

@app.route('/admin/backup')
def backup():
    """Backup page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    return render_template('backup.html')

@app.route('/api/backup/export')
def export_backup():
    """Export all data as JSON"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = {
        'export_date': datetime.now().isoformat(),
        'items': [item.to_dict() for item in Item.query.all()],
        'history': [h.to_dict() for h in CalculationHistory.query.all()],
        'calibrations': [c.to_dict() for c in CalibrationLog.query.all()],
        'activities': [a.to_dict() for a in ActivityLog.query.all()]
    }
    
    response = Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json'
    )
    response.headers['Content-Disposition'] = f'attachment; filename=backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

@app.route('/api/backup/export-csv')
def export_csv():
    """Export items as CSV"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['رقم الصنف', 'الاسم', 'اللون', 'الطول', 'العرض', 'السماكة', 'وزن الحبة', 'ملاحظات'])
    
    for item in Item.query.all():
        writer.writerow([
            item.item_number, item.name, item.color,
            item.length, item.width, item.thickness,
            item.unit_weight, item.notes
        ])
    
    response = Response(output.getvalue(), mimetype='text/csv; charset=utf-8-sig')
    response.headers['Content-Disposition'] = f'attachment; filename=items_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return response

@app.route('/api/backup/import', methods=['POST'])
def import_backup():
    """Import data from JSON backup"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'لم يتم اختيار ملف'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'لم يتم اختيار ملف'}), 400
    
    try:
        data = json.load(file)
        
        # Import items
        if 'items' in data:
            for item_data in data['items']:
                existing = Item.query.filter_by(item_number=item_data.get('item_number')).first()
                if not existing:
                    item = Item(
                        item_number=item_data.get('item_number', ''),
                        name=item_data.get('name', ''),
                        color=item_data.get('color', ''),
                        length=item_data.get('length', 0),
                        width=item_data.get('width', 0),
                        thickness=item_data.get('thickness', 0),
                        unit_weight=item_data.get('unit_weight', 0),
                        notes=item_data.get('notes', '')
                    )
                    db.session.add(item)
        
        db.session.commit()
        
        activity = ActivityLog(
            action='استيراد نسخة احتياطية',
            entity_type='backup',
            details=f'تم استيراد {len(data.get("items", []))} صنف'
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم استيراد البيانات بنجاح!'})
    
    except Exception as e:
        return jsonify({'error': f'خطأ في الاستيراد: {str(e)}'}), 400

@app.route('/api/backup/import-csv', methods=['POST'])
def import_csv():
    """Import items from CSV"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'لم يتم اختيار ملف'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'لم يتم اختيار ملف'}), 400
    
    try:
        stream = StringIO(file.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)
        count = 0
        
        for row in reader:
            item_number = row.get('رقم الصنف', row.get('item_number', ''))
            if not Item.query.filter_by(item_number=item_number).first():
                item = Item(
                    item_number=item_number,
                    name=row.get('الاسم', row.get('name', '')),
                    color=row.get('اللون', row.get('color', '')),
                    length=float(row.get('الطول', row.get('length', 0))),
                    width=float(row.get('العرض', row.get('width', 0))),
                    thickness=float(row.get('السماكة', row.get('thickness', 0))),
                    unit_weight=float(row.get('وزن الحبة', row.get('unit_weight', 0))),
                    notes=row.get('ملاحظات', row.get('notes', ''))
                )
                db.session.add(item)
                count += 1
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'تم استيراد {count} صنف بنجاح!'})
    
    except Exception as e:
        return jsonify({'error': f'خطأ في الاستيراد: {str(e)}'}), 400

# ==================== CALIBRATION LOGS ====================

@app.route('/calibrations')
def calibrations():
    """Calibration logs page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    page = request.args.get('page', 1, type=int)
    query = CalibrationLog.query.order_by(CalibrationLog.created_at.desc())
    pagination = query.paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
    
    return render_template('calibrations.html', calibrations=pagination.items, pagination=pagination)

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message='الصفحة غير موجودة'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', code=500, message='خطأ في الخادم'), 500

# ==================== INIT DATABASE ====================

@app.cli.command('init-db')
def init_db():
    """Initialize database with sample data"""
    db.create_all()
    
    # Add sample items if empty
    if Item.query.count() == 0:
        sample_items = [
            Item(item_number='ZN-001', name='زنك', color='أبيض', length=6.0, width=1.05, thickness=0.35, unit_weight=8.5, notes='زنك عادي'),
            Item(item_number='ZN-002', name='زنك', color='أزرق', length=6.0, width=1.05, thickness=0.40, unit_weight=9.2, notes='زنك ملون'),
            Item(item_number='ZN-003', name='زنك', color='أحمر', length=6.0, width=1.05, thickness=0.45, unit_weight=10.1, notes='زنك سميك'),
            Item(item_number='ZN-004', name='زنك', color='أخضر', length=6.0, width=1.05, thickness=0.50, unit_weight=11.3, notes='زنك سميك جداً'),
            Item(item_number='ST-001', name='حديد تسليح', color='أسود', length=12.0, width=0.012, thickness=12.0, unit_weight=10.66, notes='قطر 12 مم'),
            Item(item_number='ST-002', name='حديد تسليح', color='أسود', length=12.0, width=0.014, thickness=14.0, unit_weight=14.52, notes='قطر 14 مم'),
            Item(item_number='ST-003', name='حديد تسليح', color='أسود', length=12.0, width=0.016, thickness=16.0, unit_weight=18.96, notes='قطر 16 مم'),
            Item(item_number='ST-004', name='حديد تسليح', color='أسود', length=12.0, width=0.020, thickness=20.0, unit_weight=29.60, notes='قطر 20 مم'),
            Item(item_number='PL-001', name='صاج مجلفن', color='فضي', length=2.0, width=1.0, thickness=0.50, unit_weight=7.85, notes='صاج عادي'),
            Item(item_number='PL-002', name='صاج مجلفن', color='فضي', length=2.5, width=1.25, thickness=0.75, unit_weight=18.4, notes='صاج سميك'),
        ]
        
        for item in sample_items:
            db.session.add(item)
        
        db.session.commit()
        print('Database initialized with sample data!')
    else:
        print('Database already has data.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
