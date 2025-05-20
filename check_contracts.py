from flask import Flask
from extensions import db
from models import Contract

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/household_help'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_contracts():
    with app.app_context():
        # Count total contracts
        contract_count = Contract.query.count()
        print(f"Total contracts: {contract_count}")
        
        # Show a few contracts with their new fields
        contracts = Contract.query.all()
        for contract in contracts[:5]:  # Show up to 5 contracts
            print(f"Contract ID: {contract.contract_id}")
            print(f"  Is Full Time: {contract.is_full_time}")
            print(f"  Working Hours: {contract.working_hours_from} - {contract.working_hours_to}")
            print(f"  Start Date: {contract.start_date}")
            print(f"  End Date: {contract.end_date}")
            print(f"  Monthly Salary: ₹{contract.monthly_salary}")
            print("-" * 40)

if __name__ == '__main__':
    check_contracts() 