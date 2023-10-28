from flask import Flask, jsonify , request
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

class MenuItems(db.Model):
    __tablename__ = 'MenuItems'
    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(255))
    item_description = db.Column(db.String(400))
    item_price = db.Column(db.Float)
    item_picture_url = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('Categories.category_id'))

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

#Orders
@app.route('/menus', methods=['GET'])
def get_Menus():
    menus = MenuItems.query.all()
    return jsonify([{'item_id': item.item_id, 'item_name': item.item_name , 'item_price' : item.item_price} for item in menus])

@app.route('/pic_url', methods= ['GET'])
def get_Pic():
    pic_menu = MenuItems.query.all()
    return jsonify([{'item_picture_url' : pic.item_picture_url} for pic in pic_menu])

@app.route('/OrderDetail', methods= ['GET'])
def get_OrderDetail():
    detail = MenuItems.query.all()
    return jsonify([{'item_id': item.item_id, 'item_name': item.item_name , 'item_price' : item.item_price , 'item_description' : item.item_description , 'item_picture_url' : item.item_picture_url} for item in detail])

#oder-confirm
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


#status
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

#payment

# ------------------- ADMIN UI INTERFACE ----------------------

#admin Table 
@app.route('/table', methods=['GET'])
def get_tables():
    tables = Table.query.all()
    return jsonify([{ 'table_id': table.table_id, 'table_number': table.table_number } for table in tables])

@app.route('/table_status', methods= ['GET'])
def get_statustable():
    status_table = Table.query.all()
    return jsonify([{'table_id' : status.table_id,'status_table' : status.is_occupied.name} for status in status_table])

@app.route('/addtable', methods=['POST'])
def add_table():
    # รับข้อมูลจาก JSON ที่ส่งมา
    data = request.json

    # สร้าง Table ใหม่จากข้อมูลที่ได้
    new_table = Table(
        table_number=data['table_number'],
        is_occupied=TableStatusEnum['ว่าง'],
        qr_code=data.get('qr_code', '')  # ถ้าไม่มี qr_code ใน JSON จะใช้ค่าว่าง
    )

    # บันทึกลงฐานข้อมูล
    db.session.add(new_table)
    db.session.commit()

    # ส่งกลับ response แสดงว่าการทำงานสำเร็จ
    return jsonify({"message": "Table added successfully", "table_id": new_table.table_id}), 201

#admin Orders
@app.route('/showorder', methods=['GET'])
def get_orders():
    show = Orders.query.all()
    return jsonify([{'order_id' : user.order_id, 'table_id' : user.table_id , 'order_time' : user.order_time , 'status' : user.order_status.name }for user in show])

#Stock
@app.route('/addstock', methods=['POST'])
def post_AddStock(): #addstock button
    
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
    
    
    
# -------------- RUN ---------------
#(ห้ามแก้ไขบรรทัดนี้เด็ดขาด เนื่องจากเป็น syntax)
if __name__ == "__main__":
    app.run(debug=True)
