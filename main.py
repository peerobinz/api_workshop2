from flask import Flask, abort, jsonify, make_response, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import func
import enum

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://avnadmin:AVNS_zMGhESqA5uEbOxeWshl@mysql-peerobinz-peerobinz.aivencloud.com:13806/AppNotification'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()


class TableStatusEnum(enum.Enum):
    ว่าง = "ว่าง"
    ไม่ว่าง = "ไม่ว่าง"
    

class Table(db.Model):
    __tablename__ = 'Table'
    table_id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer)
    is_occupied = db.Column(db.Enum(TableStatusEnum))
    qr_code = db.Column(db.String(255))


class OrdersStatusEnum(enum.Enum):
    กําลังปรุง = "กําลังปรุง"
    เสิร์ฟแล้ว = "เสิร์ฟแล้ว"
    ยกเลิก = "ยกเลิก"


class Orders(db.Model):
    __tablename__ = 'Orders'
    order_id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('Table.table_id'))
    order_time = db.Column(db.DateTime)
    order_status = db.Column(db.Enum(OrdersStatusEnum))


class ItemsStatusEnum(enum.Enum):
    กําลังปรุง = "กําลังปรุง"
    เสิร์ฟแล้ว = "เสิร์ฟแล้ว"
    ยกเลิก = "ยกเลิก"


class OrderItems(db.Model):
    __tablename__ = 'OrderItems'
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.order_id'))
    menu_item_id = db.Column(db.Integer, db.ForeignKey('MenuItems.item_id'))
    quantity = db.Column(db.Integer)
    item_status = db.Column(db.Enum(ItemsStatusEnum))
    note_item = db.Column(db.String(100))


class EmployeeCalls(db.Model):
    __tablename__ = 'EmployeeCalls'
    call_id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('Table.table_id'))
    call_time = db.Column(db.DateTime)


class PaymentStatus(enum.Enum):
    ชำระเเล้ว = "ชำระเเล้ว"
    ยังไม่ชำระ = "ยังไม่ชำระ"


class Bills(db.Model):
    __tablename__ = 'Bills'
    bill_id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('Table.table_id'))
    total_amount = db.Column(db.Float)
    is_paid = db.Column(db.Enum(PaymentStatus))
    bill_time = db.Column(db.DateTime)

class Menu_Status(enum.Enum):
    มี = "มี"
    หมด = "หมด"


class MenuItems(db.Model):
    __tablename__ = 'MenuItems'
    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(255))
    item_description = db.Column(db.String(400))
    item_price = db.Column(db.Float)
    item_picture_url = db.Column(db.String(500))
    category_id = db.Column(
        db.Integer, db.ForeignKey('Categories.category_id'))
    menu_status = db.Column(db.Enum(Menu_Status))


class DashboardData(db.Model):
    __tablename__ = 'DashboardData'
    dashboard_id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('Table.table_id'))
    total_orders = db.Column(db.Integer)
    total_amount = db.Column(db.Float)
    call_employee_count = db.Column(db.Integer)
    last_order_time = db.Column(db.DateTime)


class Categories(db.Model):
    __tablename__ = 'Categories'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(255))
    category_description = db.Column(db.Text)

db.init_app(app)


# ------------------- USER UI INTERFACE ----------------------

# Orders
@app.route('/Orders/menus', methods=['GET'])
def get_Menus():
    menus = MenuItems.query.all()
    return jsonify([{'item_id': item.item_id, 'item_name': item.item_name, 'item_price': item.item_price , 'itam_picture':item.item_picture_url} for item in menus])

@app.route('/Orders/pic_url', methods=['GET'])
def get_Pic():
    pic_menu = MenuItems.query.all()
    return jsonify([pic.item_picture_url for pic in pic_menu])

#Orders_detail
@app.route('/OrderDetail/<int:item_id>', methods=['GET'])
def get_order_detail(item_id):
    menu_item = MenuItems.query.get(item_id)
    if not menu_item:
        return jsonify({'message': 'Menu item not found!'}), 404

    return jsonify({
        'item_id': menu_item.item_id,
        'item_name': menu_item.item_name,
        'item_description': menu_item.item_description,
        'item_price': menu_item.item_price,
        'item_picture_url': menu_item.item_picture_url,
        'category_id': menu_item.category_id
    })
@app.route('/order/<int:order_id>/add-items', methods=['POST'])
def add_items_to_order(order_id):
    # รับข้อมูลจาก JSON ที่ส่งมา
    data = request.json
    items = data.get('items')
    
    # ตรวจสอบว่ามีข้อมูล items หรือไม่
    if not items:
        abort(400, description="No items provided.")
    
    # สร้าง OrderItems ใหม่สำหรับแต่ละเมนูอาหารที่เลือก
    for item in items:
        new_order_item = OrderItems(
            order_id=order_id,
            menu_item_id=order_id,  # กำหนดให้ menu_item_id เท่ากับ order_item_id
            quantity=item.get('quantity', 1),  # ค่าเริ่มต้นคือ 1 หากไม่ระบุ
            item_status='กําลังปรุง',  # หรือสถานะเริ่มต้นอื่นๆ ตามที่คุณกำหนด
            note_item=item.get('note_item', '')  # หมายเหตุเพิ่มเติมหากมี
        )
        db.session.add(new_order_item)
    
    # บันทึกการเปลี่ยนแปลงลงฐานข้อมูล
    db.session.commit()

    return jsonify({"message": f"Items added to order {order_id} successfully."}), 201

# oder-confirm
@app.route('/place_order', methods=['POST'])  #need json request
def place_order():
    # รับข้อมูลจาก JSON ที่ส่งมา
    data = request.json
    
    # สร้าง Orders object ใหม่
    new_order = Orders(table_id=data['table_id'])
    db.session.add(new_order)
    
    # รับรายการ MenuItems ที่เลือกและสร้าง OrderItems สำหรับแต่ละรายการ
    for menu_item in data['selected_menu_items']:
        new_order_item = OrderItems(
            order_id=new_order.order_id,
            menu_item_id=menu_item['menu_item_id'],
            quantity=menu_item['quantity'],
            item_status=ItemsStatusEnum['กําลังปรุง']
        )
        db.session.add(new_order_item)
    
    # บันทึกทุกอย่างลงฐานข้อมูล
    db.session.commit()
    
    # ส่งกลับ response แสดงว่าการทำงานสำเร็จ
    return jsonify({"message": "Order placed successfully", "order_id": new_order.order_id}), 201

# status
@app.route('/status/orderstatus/<int:order_id>', methods=['GET'])
def get_order_status(order_id):
    # ดึงข้อมูล OrderItem ทั้งหมดภายใต้ order_id ที่ระบุ
    order_items = OrderItems.query.filter_by(order_id=order_id).all()

    # แปลงข้อมูลเป็นรูปแบบ JSON
    result = []
    for item in order_items:
        menu_item = MenuItems.query.get(item.menu_item_id)
        result.append({
            'order_id': item.order_id,
            'menu_item_name': menu_item.item_name,
            'item_status': item.item_status.name
        })

    # ส่งกลับข้อมูลในรูปแบบ JSON
    return jsonify(result)

# payment
@app.route('/payment/<int:order_id>', methods=['GET'])
def get_payment_details_by_order_id(order_id):
    # ค้นหา bill ตาม order_id ที่ระบุ
    bill = Bills.query.filter_by(table_id=order_id).first()

    # ตรวจสอบว่ามี bill นี้ในฐานข้อมูลหรือไม่
    if not bill:
        return jsonify({"error": "Bill not found for the given order_id!"}), 404

    # ค้นหา order items ตาม order_id
    order_items = OrderItems.query.filter_by(order_id=order_id).all()

    items = [{'item_name': item.menu_item.item_name, 'quantity': item.quantity, 'price': item.menu_item.item_price}
             for item in order_items]

    result = {
        'bill_id': bill.bill_id,
        'table_id': bill.table_id,
        'total_amount': bill.total_amount,
        'items': items
    }

    return jsonify(result)

# ------------------- ADMIN UI INTERFACE ----------------------

# admin Table
@app.route('/table', methods=['GET'])
def get_tables():
    tables = Table.query.all()
    return jsonify([{'table_id': table.table_id, 'table_number': table.table_number} for table in tables])

@app.route('/table/table_status', methods=['GET'])
def get_statustable():
    status_table = Table.query.all()
    return jsonify([{'table_id': status.table_id, 'status_table': status.is_occupied.name} for status in status_table])

@app.route('/table/addtable', methods=['POST'])
def post_add_table():
    # ค้นหา table_number ที่มากที่สุดในฐานข้อมูล
    max_table_number = db.session.query(db.func.max(Table.table_number)).scalar()
    if max_table_number is None:
        max_table_number = 0  # ถ้าไม่มีข้อมูล ให้เริ่มที่ 0

    # สร้าง Table ใหม่โดยกำหนด table_number ให้มากกว่าค่าที่มากที่สุดที่พบ
    new_table = Table(
        table_number=max_table_number + 1,
        is_occupied=TableStatusEnum['ว่าง'],
        qr_code=""  # ถ้าไม่ต้องการ qr_code สามารถตั้งค่าเป็นสตริงว่าง
    )

    # บันทึกลงฐานข้อมูล
    db.session.add(new_table)
    db.session.commit()

    # ส่งกลับ response แสดงว่าการทำงานสำเร็จ
    return jsonify({"message": "Table added successfully", "table_id": new_table.table_id}), 201

@app.route('/table/update_status_table/<int:table_id>', methods=['PUT'])
def update_table_status(table_id):
    # ค้นหาโต๊ะตาม id ที่ระบุ
    table = Table.query.get(table_id)
    
    # ตรวจสอบว่ามีโต๊ะนี้ในฐานข้อมูลหรือไม่
    if not table:
        return jsonify({"error": "Table not found!"}), 404

    # รับข้อมูลสถานะใหม่ที่ต้องการเปลี่ยน
    data = request.json
    new_status = data.get('is_occupied')
    
    # ตรวจสอบว่าสถานะที่ระบุมาถูกต้องหรือไม่
    if new_status not in TableStatusEnum._value2member_map_:
        return jsonify({"error": f"Invalid status! Possible values are: {', '.join(TableStatusEnum._value2member_map_.keys())}."}), 400

    # อัพเดตสถานะและบันทึกลงฐานข้อมูล
    table.is_occupied = TableStatusEnum(new_status)
    db.session.commit()

    return jsonify({"message": f"Status for table {table_id} updated successfully."}), 200

@app.route('/table/deletetable', methods=['DELETE'])
def delete_table_number():
    # ค้นหา table ที่มี table_number มากที่สุด
    table_to_delete = Table.query.order_by(Table.table_number.desc()).first()

    # ตรวจสอบว่ามี table นี้ในฐานข้อมูลหรือไม่
    if not table_to_delete:
        return jsonify({"error": "No tables found!"}), 404

    # ลบ table นี้
    db.session.delete(table_to_delete)
    db.session.commit()

    return jsonify({"message": f"Table with the highest table number {table_to_delete.table_number} has been deleted."}), 200


# admin Orders
@app.route('/adminorders/showorders/<int:table_id>', methods=['GET'])
def get_orders_by_table(table_id):
    orders = Orders.query.filter_by(table_id=table_id).all()
    if not orders:
        return jsonify({"message": "No orders found for this table"}), 404
    return jsonify([{
        'order_id': order.order_id,
        'table_id': order.table_id,
        'order_time': order.order_time,
        'status': order.order_status.name
    } for order in orders])

@app.route('/adminorders/showorder/<int:order_id>', methods=['GET'])
def get_order_by_id(order_id):
    order = Orders.query.get(order_id)
    if not order:
        return jsonify({"message": "Order not found"}), 404
    return jsonify({
        'order_id': order.order_id,
        'table_id': order.table_id,
        'order_time': order.order_time,
        'status': order.order_status.name
    })

@app.route('/adminorders/update_orderitem_status/<int:order_item_id>', methods=['PUT'])
def put_orderitem_status(order_item_id):
    data = request.json
    new_status = data.get('new_status')

    # หา order item จาก order_item_id
    order_item = OrderItems.query.get(order_item_id)
    if not order_item:
        return make_response(jsonify({"message": "Order item not found"}), 404)

    try:
        # ตั้งค่าสถานะใหม่
        order_item.item_status = ItemsStatusEnum[new_status]

        # บันทึกการเปลี่ยนแปลงลงในฐานข้อมูล
        db.session.commit()

        return jsonify({"message": "Order item status updated successfully"})
    except Exception as e:
        return make_response(jsonify({"message": str(e)}), 400)

# Admin Queue
@app.route('/adminqueue/show_orders_by_time', methods=['GET'])
def get_show_orders_by_time():
    # ดึงข้อมูลจากฐานข้อมูลโดยเรียงตาม order_time และทำการ join กับตาราง Table
    orders = db.session.query(Orders.order_id, Table.table_number, Orders.order_time)\
                       .join(Table, Table.table_id == Orders.table_id)\
                       .order_by(Orders.order_time.desc()).all()
    
    # แปลงข้อมูลในรูปแบบ JSON และส่งกลับ
    return jsonify([{'table_number': order.table_number, 'order_id': order.order_id} for order in orders])

@app.route('/adminqueue/OrderDetail_queue/<int:item_id>', methods=['GET'])
def get_order_detail_queue(item_id):
    menu_item = MenuItems.query.get(item_id)
    if not menu_item:
        return jsonify({'message': 'Menu item not found!'}), 404

    return jsonify({
        'item_id': menu_item.item_id,
        'item_name': menu_item.item_name,
        'item_description': menu_item.item_description,
        'item_price': menu_item.item_price,
        'item_picture_url': menu_item.item_picture_url,
        'category_id': menu_item.category_id
    })

@app.route('/adminqueue/show_calls_by_time', methods=['GET'])
def get_show_calls_by_time():
    # ดึงข้อมูลจากฐานข้อมูลโดยเรียงตาม call_time และทำการ join กับตาราง Table
    calls = db.session.query(EmployeeCalls.call_id, Table.table_number, EmployeeCalls.call_time)\
                      .join(Table, Table.table_id == EmployeeCalls.table_id)\
                      .order_by(EmployeeCalls.call_time.desc()).all()
    
    # แปลงข้อมูลในรูปแบบ JSON และส่งกลับ
    return jsonify([{'table_number': call.table_number, 'call_id': call.call_id} for call in calls])

@app.route('/adminqueue/bills_order', methods=['GET'])
def get_bills_by_time():
    bills = Bills.query.order_by(Bills.bill_time.desc()).all()
    return jsonify([{'bill_id': bill.bill_id, 'bill_time': bill.bill_time} for bill in bills])

# Admin Chef
@app.route('/adminchef/show_orders_by_time_to_chef', methods=['GET'])
def get_show_orders_by_time_to_chef():
    # ดึงข้อมูลจากฐานข้อมูลโดยเรียงตาม order_time และทำการ join กับตาราง Table
    orders = db.session.query(Orders.order_id, Table.table_number, Orders.order_time)\
                       .join(Table, Table.table_id == Orders.table_id)\
                       .order_by(Orders.order_time.desc()).all()
    
    # แปลงข้อมูลในรูปแบบ JSON และส่งกลับ
    return jsonify([{'table_number': order.table_number, 'order_id': order.order_id} for order in orders])

@app.route('/adminchef/orderitem_details/<int:order_id>', methods=['GET'])
def get_order_item_details(order_id):
    # ดึงข้อมูล OrderItems ตาม order_id ที่กำหนด
    order_items = OrderItems.query.filter_by(order_id=order_id).all()

    # ตรวจสอบว่ามีข้อมูลใน order_items หรือไม่
    if not order_items:
        return jsonify({'message': 'No items found for this order'}), 404

    # แปลงข้อมูลเป็นรูปแบบ JSON และส่งกลับ
    return jsonify([{
        'order_item_id': item.order_item_id,
        'menu_item_id': item.menu_item_id,
        'quantity': item.quantity,
        'item_status': item.item_status.name if item.item_status else None,  # แสดงสถานะของ item ถ้ามี
        'note_item': item.note_item
    } for item in order_items])

# Admin Checkbill
@app.route('/admincheckbill/billdetails/<int:bill_id>', methods=['GET'])
def get_bill_details(bill_id):
    bill = Bills.query.filter_by(bill_id=bill_id).first()
    
    if not bill:
        return jsonify({"error": "Bill not found"}), 404

    table = Table.query.filter_by(table_id=bill.table_id).first()

    return jsonify({
        'table_number': table.table_number,
        'bill_time': bill.bill_time,
        'order_id': bill.order_id,  # ต้องมั่นใจว่ามี field order_id ใน Bills
        'total_amount': bill.total_amount,
        'payment_status': bill.is_paid.name
    })

# Admin Stock
@app.route('/adminstock/orderitemStock', methods=['GET'])
def get_all_orderitem_Stock():
    # ดึงข้อมูลทั้งหมดจากตาราง MenuItems
    all_menu_items = MenuItems.query.all()

    # สร้าง response จากข้อมูลที่ได้
    menu_summary = [
        {
            'item_id': item.item_id,
            'item_name': item.item_name,
            'item_price': item.item_price,
            'menu_status': item.menu_status.name  # แสดงสถานะของเมนู
        }
        for item in all_menu_items
    ]

    return jsonify(menu_summary)


@app.route('/adminstock/menuitem/update_status/<int:menu_item_id>', methods=['PUT'])
def put_menuitem_status(menu_item_id):
    # ค้นหา menu item ตาม id ที่ระบุ
    menu_item = MenuItems.query.get(menu_item_id)
    
    # ตรวจสอบว่ามี menu item นี้ในฐานข้อมูลหรือไม่
    if not menu_item:
        return jsonify({"error": "Menu item not found!"}), 404

    # รับข้อมูลสถานะใหม่ที่ต้องการเปลี่ยน
    data = request.json
    new_status = data.get('menu_status')
    
    # ตรวจสอบว่าสถานะที่ระบุมาถูกต้องหรือไม่
    if new_status not in Menu_Status._value2member_map_:
        return jsonify({"error": f"Invalid status! Possible values are: {', '.join(Menu_Status._value2member_map_.keys())}."}), 400

    # อัพเดตสถานะและบันทึกลงฐานข้อมูล
    menu_item.menu_status = Menu_Status(new_status)
    db.session.commit()

    return jsonify({"message": f"Status for menu item {menu_item_id} updated successfully."}), 200

# Admin AddStock
@app.route('/adminstock/addstock', methods=['POST'])
def post_AddStock():  # addstock button

    data = request.json

    new_item = MenuItems(
        item_name=data['item_name'],
        item_description=data['item_description'],
        item_price=data['item_price'],
        item_picture_url=data['item_picture_url'],
        category_id=data['category_id']
    )

    # เพิ่มข้อมูลใหม่เข้าฐานข้อมูล
    db.session.add(new_item)
    db.session.commit()

# Admin DeleteStock
@app.route('/adminstock/deleteitem/<string:item_name>', methods=['DELETE'])
def delete_item_by_name(item_name):
    # ค้นหา MenuItem จาก item_name
    item = MenuItems.query.filter_by(item_name=item_name).first()

    if not item:
        return jsonify({"error": "Menu item not found"}), 404

    # ลบ item จาก database
    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Menu item deleted successfully"}), 200

# Admin EditStock
# 1. ฟังก์ชันแสดงรายละเอียดของอาหาร
@app.route('/adminstock/menu/<int:item_id>', methods=['GET'])
def get_menu_detail(item_id):
    menu_item = MenuItems.query.get(item_id)
    if not menu_item:
        return jsonify({'message': 'Menu item not found!'}), 404

    return jsonify({
        'item_id': menu_item.item_id,
        'item_name': menu_item.item_name,
        'item_description': menu_item.item_description,
        'item_price': menu_item.item_price,
        'item_picture_url': menu_item.item_picture_url,
        'category_id': menu_item.category_id
    })

# 2. ฟังก์ชันแก้ไขรายละเอียดของอาหาร
@app.route('/adminstock/editmenu/<int:item_id>', methods=['PUT'])
def put_menu_stock(item_id):
    menu_item = MenuItems.query.get(item_id)
    if not menu_item:
        return jsonify({'message': 'Menu item not found!'}), 404

    data = request.json
    menu_item.item_name = data.get('item_name', menu_item.item_name)
    menu_item.item_description = data.get(
        'item_description', menu_item.item_description)
    menu_item.item_price = data.get('item_price', menu_item.item_price)
    menu_item.item_picture_url = data.get(
        'item_picture_url', menu_item.item_picture_url)
    menu_item.category_id = data.get('category_id', menu_item.category_id)

    db.session.commit()
    return jsonify({'message': 'Menu item updated successfully!'})

# Admin Dashboard
@app.route('/admindashboard/orders_count', methods=['GET'])
def get_monthly_order_count():
    # รับเดือนและปีปัจจุบัน
    current_month = datetime.now().month
    current_year = datetime.now().year

    # คัดกรอง Orders ที่มีเดือนและปีเดียวกันกับปัจจุบัน
    monthly_orders = Orders.query.filter(
        db.extract('month', Orders.order_time) == current_month,
        db.extract('year', Orders.order_time) == current_year
    ).all()

    # ส่งกลับจำนวน orders ของเดือนนั้น
    return jsonify({"orders_count": len(monthly_orders)}), 200

@app.route('/admindashboard/today_sales', methods=['GET'])
def get_today_sales():
    # รับวันที่ปัจจุบัน
    today = date.today()

    # คัดกรอง Bills ที่มีวันเดียวกันกับวันปัจจุบัน
    today_bills = Bills.query.filter(
        db.func.date(Bills.bill_time) == today
    ).all()

    # คำนวณยอดขายรวม
    total_sales = sum(bill.total_amount for bill in today_bills)

    # ส่งกลับยอดขายรวมของวันนี้
    return jsonify({"today_sales": total_sales}), 200


@app.route('/admindashboard/top_orders', methods=['GET'])
def get_top_orders():
    # รับเดือนปัจจุบัน
    current_month = datetime.now().month

    # รวม OrderItems และจัดเรียงตาม menu_item_id โดยใช้ group_by
    top_orders = (
        db.session.query(OrderItems.menu_item_id, 
                         func.sum(OrderItems.quantity).label('total_ordered'),
                         MenuItems.item_name)
        .join(MenuItems, MenuItems.item_id == OrderItems.menu_item_id)
        .join(Orders, Orders.order_id == OrderItems.order_id)
        .filter(func.extract('month', Orders.order_time) == current_month)
        .group_by(OrderItems.menu_item_id, MenuItems.item_name)
        .order_by(func.sum(OrderItems.quantity).desc())
        .limit(3)
        .all()
    )

    # แปลงข้อมูลเป็น JSON และส่งกลับ
    return jsonify([{'menu_item_name': item.item_name, 'total_ordered': item.total_ordered} for item in top_orders]), 200


# -------------- RUN ---------------
# (ห้ามแก้ไขบรรทัดนี้เด็ดขาด เนื่องจากเป็น syntax)
if __name__ == "__main__":
    app.run(debug=True)
