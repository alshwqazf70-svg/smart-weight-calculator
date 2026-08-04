// static/js/main.js

// ---------- شاشة الحساب ----------
let currentItem = null;
let currentCheckId = null;

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('item_search');
    const resultsDiv = document.getElementById('search_results');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(async function(e) {
            const q = e.target.value.trim();
            if (q.length === 0) {
                resultsDiv.style.display = 'none';
                return;
            }
            const res = await fetch(`/api/items/search?q=${encodeURIComponent(q)}`);
            const items = await res.json();
            resultsDiv.innerHTML = '';
            if (items.length === 0) {
                resultsDiv.innerHTML = '<div>لا توجد نتائج</div>';
            } else {
                items.forEach(item => {
                    const div = document.createElement('div');
                    div.textContent = `${item.name} - ${item.color} - سماكة ${item.thickness} ملم - ${item.unit_weight} كجم`;
                    div.addEventListener('click', function() {
                        selectItem(item);
                        resultsDiv.style.display = 'none';
                        searchInput.value = `${item.name} ${item.color} ${item.thickness}ملم`;
                    });
                    resultsDiv.appendChild(div);
                });
            }
            resultsDiv.style.display = 'block';
        }, 300));

        // إخفاء القائمة عند النقر خارجها
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !resultsDiv.contains(e.target)) {
                resultsDiv.style.display = 'none';
            }
        });
    }

    // تحديث الوزن المتوقع عند تغيير الكمية
    const qtyInput = document.getElementById('quantity');
    if (qtyInput) {
        qtyInput.addEventListener('input', updateExpectedWeight);
    }
});

function selectItem(item) {
    currentItem = item;
    document.getElementById('selected_item_id').value = item.id;
    document.getElementById('d_name').textContent = item.name;
    document.getElementById('d_color').textContent = item.color;
    document.getElementById('d_length').textContent = item.length;
    document.getElementById('d_width').textContent = item.width;
    document.getElementById('d_thickness').textContent = item.thickness;
    document.getElementById('d_unit_weight').textContent = item.unit_weight;
    document.getElementById('item_details').style.display = 'block';
    updateExpectedWeight();
}

function updateExpectedWeight() {
    if (!currentItem) return;
    const qty = parseInt(document.getElementById('quantity').value) || 0;
    const expected = currentItem.unit_weight * qty;
    document.getElementById('expected_weight_display').textContent = expected.toFixed(2);
}

async function calculate() {
    const quantity = document.getElementById('quantity').value;
    const actualWeight = document.getElementById('actual_weight').value;
    const itemId = document.getElementById('selected_item_id').value;
    const unitWeight = currentItem ? currentItem.unit_weight : null;

    if (!itemId && !unitWeight) {
        alert('الرجاء اختيار صنف أو استخدام الحاسبة الهندسية أولاً');
        return;
    }
    const payload = {
        item_id: itemId || null,
        quantity: quantity,
        actual_weight: actualWeight || null,
        unit_weight: unitWeight
    };
    const res = await fetch('/api/calculate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.error) {
        alert(data.error);
        return;
    }
    // عرض النتيجة
    document.getElementById('expected_weight_display').textContent = data.expected_weight.toFixed(2);
    const compDiv = document.getElementById('comparison_result');
    compDiv.style.display = 'block';
    document.getElementById('status_text').textContent = 'الحالة: ' + data.status;
    document.getElementById('diff_val').textContent = data.difference !== null ? data.difference.toFixed(2) : '--';
    document.getElementById('diff_percent').textContent = data.difference_percent !== null ? data.difference_percent.toFixed(2) : '--';
    
    const alertMsg = document.getElementById('alert_msg');
    if (data.alert_message) {
        alertMsg.textContent = data.alert_message;
        alertMsg.style.display = 'block';
    } else {
        alertMsg.style.display = 'none';
    }
    
    const statusCard = document.getElementById('status_card');
    statusCard.className = 'card status-card ' + (data.status_class || '');
    
    // إظهار زر المعايرة إذا كان هناك فرق كبير و item_id موجود
    const calibrateBtn = document.getElementById('calibrate_btn');
    if (data.item_id && data.difference_percent && Math.abs(data.difference_percent) > 2 && currentItem) {
        calibrateBtn.style.display = 'inline-block';
        currentCheckId = data.check_id;
    } else {
        calibrateBtn.style.display = 'none';
    }
}

async function calibrateWeight() {
    if (!currentCheckId || !currentItem) return;
    const newWeight = prompt('أدخل الوزن الصحيح للحبة (كجم) من الميزان:', currentItem.unit_weight);
    if (!newWeight) return;
    const res = await fetch('/api/calibrate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            check_id: currentCheckId,
            new_unit_weight: parseFloat(newWeight),
            reason: 'تصحيح بناءً على قياس فعلي'
        })
    });
    const data = await res.json();
    if (data.success) {
        alert(data.message);
        // تحديث وزن الحبة المعروض
        currentItem.unit_weight = parseFloat(newWeight);
        document.getElementById('d_unit_weight').textContent = newWeight;
        updateExpectedWeight();
        document.getElementById('calibrate_btn').style.display = 'none';
    }
}

// ---------- الحاسبة الهندسية ----------
function calculateEngineering() {
    const length = parseFloat(document.getElementById('eng_length').value);
    const width = parseFloat(document.getElementById('eng_width').value);
    const thickness = parseFloat(document.getElementById('eng_thickness').value);
    const density = parseFloat(document.getElementById('density').value);
    
    // الحجم = الطول * العرض * السماكة (تحويل السماكة من مم إلى متر)
    const thicknessM = thickness / 1000;
    const volume = length * width * thicknessM; // متر مكعب
    const densityKgM3 = density * 1000; // كثافة جم/سم³ إلى كجم/م³
    const unitWeight = volume * densityKgM3; // كجم
    document.getElementById('eng_unit_weight').textContent = unitWeight.toFixed(2);
    document.getElementById('eng_result').style.display = 'block';
}

function calculateEngLoad() {
    const unitWeight = parseFloat(document.getElementById('eng_unit_weight').textContent);
    const qty = parseInt(document.getElementById('eng_quantity').value) || 0;
    const loadWeight = unitWeight * qty;
    document.getElementById('eng_load_weight').textContent = loadWeight.toFixed(2);
    document.getElementById('eng_load_result').style.display = 'block';
}

// ---------- السجل ----------
async function loadHistory() {
    const q = document.getElementById('history_search')?.value || '';
    const res = await fetch(`/api/history?q=${encodeURIComponent(q)}`);
    const checks = await res.json();
    const container = document.getElementById('history_list');
    if (!container) return;
    if (checks.length === 0) {
        container.innerHTML = '<p>لا توجد عمليات سابقة.</p>';
        return;
    }
    let html = '<div class="table-responsive"><table><thead><tr><th>التاريخ</th><th>الصنف</th><th>اللون</th><th>الكمية</th><th>المتوقع</th><th>الفعلي</th><th>الفرق</th><th>الحالة</th></tr></thead><tbody>';
    checks.forEach(c => {
        html += `<tr>
            <td>${c.created_at}</td>
            <td>${c.item_name}</td>
            <td>${c.item_color}</td>
            <td>${c.quantity}</td>
            <td>${c.expected_weight} كجم</td>
            <td>${c.actual_weight} كجم</td>
            <td>${c.difference} كجم (${c.difference_percent}%)</td>
            <td>${c.status}</td>
        </tr>`;
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

// ---------- دوال الإدارة ----------
async function loadItems() {
    const res = await fetch('/api/admin/items');
    const items = await res.json();
    const container = document.getElementById('items_list');
    let html = '<div class="table-responsive"><table><thead><tr><th>رقم الصنف</th><th>الاسم</th><th>اللون</th><th>الطول</th><th>العرض</th><th>السماكة</th><th>وزن الحبة</th><th>الاستخدام</th><th>إجراءات</th></tr></thead><tbody>';
    items.forEach(i => {
        html += `<tr>
            <td>${i.item_number}</td>
            <td>${i.name}</td>
            <td>${i.color}</td>
            <td>${i.length}</td>
            <td>${i.width}</td>
            <td>${i.thickness}</td>
            <td>${i.unit_weight}</td>
            <td>${i.usage_count}</td>
            <td>
                <button class="btn btn-outline" onclick="editItem(${i.id})">تعديل</button>
                <button class="btn btn-danger" onclick="deleteItem(${i.id})">حذف</button>
            </td>
        </tr>`;
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function showAddItemForm() {
    document.getElementById('item_form').style.display = 'block';
    document.getElementById('edit_item_id').value = '';
    clearItemForm();
}

function editItem(id) {
    fetch('/api/admin/items').then(r => r.json()).then(items => {
        const item = items.find(i => i.id == id);
        if (!item) return;
        document.getElementById('edit_item_id').value = item.id;
        document.getElementById('item_number').value = item.item_number;
        document.getElementById('item_name').value = item.name;
        document.getElementById('item_color').value = item.color;
        document.getElementById('item_length').value = item.length;
        document.getElementById('item_width').value = item.width;
        document.getElementById('item_thickness').value = item.thickness;
        document.getElementById('item_unit_weight').value = item.unit_weight;
        document.getElementById('item_notes').value = item.notes || '';
        document.getElementById('item_form').style.display = 'block';
    });
}

function cancelItemForm() {
    document.getElementById('item_form').style.display = 'none';
}

async function saveItem() {
    const id = document.getElementById('edit_item_id').value;
    const data = {
        id: id || null,
        item_number: document.getElementById('item_number').value,
        name: document.getElementById('item_name').value,
        color: document.getElementById('item_color').value,
        length: document.getElementById('item_length').value,
        width: document.getElementById('item_width').value,
        thickness: document.getElementById('item_thickness').value,
        unit_weight: document.getElementById('item_unit_weight').value,
        notes: document.getElementById('item_notes').value
    };
    const res = await fetch('/api/admin/items', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    const result = await res.json();
    if (result.success) {
        alert('تم الحفظ بنجاح');
        cancelItemForm();
        loadItems();
    } else {
        alert('خطأ: ' + result.error);
    }
}

async function deleteItem(id) {
    if (!confirm('هل أنت متأكد من حذف هذا الصنف؟')) return;
    await fetch(`/api/admin/items/${id}`, { method: 'DELETE' });
    loadItems();
}

function exportBackup() {
    window.location.href = '/api/admin/export';
}

async function importBackup() {
    const fileInput = document.getElementById('backup_file');
    const file = fileInput.files[0];
    if (!file) {
        alert('الرجاء اختيار ملف');
        return;
    }
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/admin/import', { method: 'POST', body: formData });
    const result = await res.json();
    if (result.success) {
        alert(`تم استيراد ${result.count} صنف بنجاح`);
        loadItems();
    } else {
        alert('خطأ: ' + result.error);
    }
}

async function loadCalibrationLogs() {
    const res = await fetch('/api/admin/calibration_logs');
    const logs = await res.json();
    const container = document.getElementById('calibration_logs');
    if (logs.length === 0) {
        container.innerHTML = '<p>لا توجد تعديلات.</p>';
        return;
    }
    let html = '<ul>';
    logs.forEach(log => {
        html += `<li>${log.created_at} - ${log.item_name}: ${log.old_weight} ➔ ${log.new_weight} (${log.reason})</li>`;
    });
    html += '</ul>';
    container.innerHTML = html;
}

async function changePassword() {
    const newPass = document.getElementById('new_password').value;
    if (!newPass) return;
    const res = await fetch('/api/admin/change_password', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ password: newPass })
    });
    const data = await res.json();
    if (data.success) {
        alert('تم تغيير كلمة المرور بنجاح');
    } else {
        alert('خطأ');
    }
}

// دالة منع تكرار الطلبات
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}