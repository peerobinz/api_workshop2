from flask import Flask, jsonify, make_response, request
from flask_sqlalchemy import SQLAlchemy
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
    กำลังปรุง = "กำลังปรุง"
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
@app.route('/menus', methods=['GET'])
def get_Menus():
    menus = MenuItems.query.all()
    return jsonify([{'item_id': item.item_id, 'item_name': item.item_name, 'item_price': item.item_price} for item in menus])

@app.route('/pic_url', methods=['GET'])
def get_Pic():
    pic_menu = MenuItems.query.all()
    return jsonify([{'item_picture_url': pic.item_picture_url} for pic in pic_menu])

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

# oder-confirm
@app.route('/placeorder', methods=['POST'])
def place_order():
    # รับข้อมูลจาก JSON ที่ส่งมา
    data = request.json

    # สร้าง order ใหม่
    new_order = Orders(table_id=data['table_id'])
    db.session.add(new_order)
    db.session.commit()

    # สร้าง OrderItem จากข้อมูลที่ได้
    order_items = data['items']
    for item in order_items:
        new_orderitem = OrderItems(
            order_id=new_order.order_id,
            menu_item_id=item['menu_item_id'],
            quantity=item['quantity'],
            item_status=ItemsStatusEnum['กําลังปรุง'],
            note_item=item.get('note_item', '')
        )
        db.session.add(new_orderitem)

    db.session.commit()

    # ส่งกลับ response แสดงว่าการทำงานสำเร็จ
    return jsonify({"message": "Order placed successfully", "order_id": new_order.order_id}), 201

# status
@app.route('/orderstatus/<int:order_id>', methods=['GET'])
def get_order_status(order_id):
    # ดึงข้อมูล OrderItem ทั้งหมดภายใต้ order_id ที่ระบุ
    order_items = OrderItems.query.filter_by(order_id=order_id).all()

    # แปลงข้อมูลเป็นรูปแบบ JSON
    result = []
    for item in order_items:
        result.append({
            'order_item_id': item.order_item_id,
            'menu_item_id': item.menu_item_id,
            'quantity': item.quantity,
            'item_status': item.item_status.name,
            'note_item': item.note_item
        })

    # ส่งกลับข้อมูลในรูปแบบ JSON
    return jsonify(result)

# payment
@app.route('/payment', methods=['GET'])
def get_unpaid_orders():
    # ค้นหา bills ที่ยังไม่ได้ชำระเงิน
    unpaid_bills = Bills.query.filter_by(
        is_paid=PaymentStatus['ยังไม่ชำระ']).all()

    results = []

    for bill in unpaid_bills:
        # สามารถ join ตารางเพื่อรับข้อมูลเพิ่มเติมถ้าจำเป็น
        order_items = OrderItems.query.filter_by(order_id=bill.table_id).all()

        items = [{'item_name': item.menu_item.item_name, 'quantity': item.quantity, 'price': item.menu_item.item_price}
                 for item in order_items]

        results.append({
            'bill_id': bill.bill_id,
            'table_id': bill.table_id,
            'total_amount': bill.total_amount,
            'items': items
        })

    return jsonify(results)


# ------------------- ADMIN UI INTERFACE ----------------------

# admin Table
@app.route('/table', methods=['GET'])
def get_tables():
    tables = Table.query.all()
    return jsonify([{'table_id': table.table_id, 'table_number': table.table_number} for table in tables])

@app.route('/table_status', methods=['GET'])
def get_statustable():
    status_table = Table.query.all()
    return jsonify([{'table_id': status.table_id, 'status_table': status.is_occupied.name} for status in status_table])

@app.route('/addtable', methods=['POST'])
def add_table():
    # รับข้อมูลจาก JSON ที่ส่งมา
    data = request.json

    # สร้าง Table ใหม่จากข้อมูลที่ได้
    new_table = Table(
        table_number=data['table_number'],
        is_occupied=TableStatusEnum['ว่าง'],
        # ถ้าไม่มี qr_code ใน JSON จะใช้ค่าว่าง
        qr_code=data.get('qr_code', '')
    )

    # บันทึกลงฐานข้อมูล
    db.session.add(new_table)
    db.session.commit()

    # ส่งกลับ response แสดงว่าการทำงานสำเร็จ
    return jsonify({"message": "Table added successfully", "table_id": new_table.table_id}), 201

# admin Orders
@app.route('/showorders/table/<int:table_id>', methods=['GET'])
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

@app.route('/showorder/<int:order_id>', methods=['GET'])
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

@app.route('/update_orderitem_status/<int:order_item_id>', methods=['PUT'])
def update_orderitem_status(order_item_id):
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
@app.route('/show_orders_by_time', methods=['GET'])
def show_orders_by_time():
    # ดึงข้อมูลจากฐานข้อมูลโดยเรียงตาม order_time และทำการ join กับตาราง Table
    orders = db.session.query(Orders.order_id, Table.table_number, Orders.order_time)\
                       .join(Table, Table.table_id == Orders.table_id)\
                       .order_by(Orders.order_time.desc()).all()
    
    # แปลงข้อมูลในรูปแบบ JSON และส่งกลับ
    return jsonify([{'table_number': order.table_number, 'order_id': order.order_id} for order in orders])

@app.route('/show_calls_by_time', methods=['GET'])
def show_calls_by_time():
    # ดึงข้อมูลจากฐานข้อมูลโดยเรียงตาม call_time และทำการ join กับตาราง Table
    calls = db.session.query(EmployeeCalls.call_id, Table.table_number, EmployeeCalls.call_time)\
                      .join(Table, Table.table_id == EmployeeCalls.table_id)\
                      .order_by(EmployeeCalls.call_time.desc()).all()
    
    # แปลงข้อมูลในรูปแบบ JSON และส่งกลับ
    return jsonify([{'table_number': call.table_number, 'call_id': call.call_id} for call in calls])

# Admin Chef
@app.route('/show_orders_by_time_to_chef', methods=['GET'])
def show_orders_by_time_to_chef():
    # ดึงข้อมูลจากฐานข้อมูลโดยเรียงตาม order_time และทำการ join กับตาราง Table
    orders = db.session.query(Orders.order_id, Table.table_number, Orders.order_time)\
                       .join(Table, Table.table_id == Orders.table_id)\
                       .order_by(Orders.order_time.desc()).all()
    
    # แปลงข้อมูลในรูปแบบ JSON และส่งกลับ
    return jsonify([{'table_number': order.table_number, 'order_id': order.order_id} for order in orders])

@app.route('/orderitem_details/<int:order_id>', methods=['GET'])
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

# Admin Stock
@app.route('/orderitemStock/<int:menu_id>', methods=['GET'])
def get_orderitem_Stock_by_menu_id(menu_id):
    # ดึงข้อมูลจากฐานข้อมูลโดยการ join 2 ตารางและ filter ด้วย menu_id
    results = db.session.query(OrderItems, MenuItems).join(
        MenuItems, OrderItems.menu_item_id == MenuItems.item_id).filter(MenuItems.item_id == menu_id).all()

    # สร้าง response จากข้อมูลที่ได้
    orderitem_summary = [
        {
            'item_name': menu.item_name,
            'item_price': menu.item_price,
            'menu_status': menu.menu_status.value  # แสดงสถานะของเมนู
        }
        for menu in results
    ]

    return jsonify(orderitem_summary)


# Admin AddStock

@app.route('/addstock', methods=['POST'])
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

# Admin EditStock

# 1. ฟังก์ชันแสดงรายละเอียดของอาหาร
@app.route('/menu/<int:item_id>', methods=['GET'])
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
@app.route('/menu/<int:item_id>', methods=['PUT'])
def update_menu(item_id):
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


# -------------- RUN ---------------
# (ห้ามแก้ไขบรรทัดนี้เด็ดขาด เนื่องจากเป็น syntax)
if __name__ == "__main__":
    app.run(debug=True)
