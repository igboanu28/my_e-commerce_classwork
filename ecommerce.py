from app import app,db
from app.models import User, Products, CustomerOrder

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Products': Products, 'CustomerOrder':CustomerOrder}

port_number = 8000

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=port_number)